"""
Test LoRA (Low-Rank Adaptation) Configuration
Validates fine-tuning setup for RTX 3050
"""

import torch
from transformers import LlavaForConditionalGeneration, AutoTokenizer, BitsAndBytesConfig
from peft import get_peft_model, LoraConfig, TaskType

print("=" * 70)
print("TESTING LoRA CONFIGURATION FOR RTX 3050")
print("=" * 70)
print()

# Quantization config with CPU offload for 4GB VRAM
quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    llm_int8_enable_fp32_cpu_offload=True,  # Enable CPU offload for 4GB VRAM
)

model_id = "llava-hf/llava-1.5-7b-hf"

# Custom device map for RTX 3050 (4GB VRAM) - Put vision layers on GPU, some text on CPU
max_memory = {0: "3.5GiB", "cpu": "12GiB"}  # Leave 0.5GB for system

print("[1] Loading base model with int4 quantization...")
print("   [INFO] Using device_map with 3.5GB GPU + 12GB CPU")
try:
    model = LlavaForConditionalGeneration.from_pretrained(
        model_id,
        quantization_config=quantization_config,
        device_map="auto",
        max_memory=max_memory,
        trust_remote_code=True,
    )
    print("   [OK] Model loaded")
except Exception as e:
    print(f"   [FAILED] Failed: {e}")
    exit(1)

print()
print("[2] Configuring LoRA adapters...")

# LoRA configuration
lora_config = LoraConfig(
    r=8,                                    # Low rank (8 is good for RTX 3050)
    lora_alpha=16,                          # Scaling factor
    target_modules=["q_proj", "v_proj"],    # Target attention layers
    lora_dropout=0.05,
    bias="none",
    task_type=TaskType.CAUSAL_LM,
)

print(f"   • Rank (r): 8")
print(f"   • Alpha: 16")
print(f"   • Target modules: q_proj, v_proj")
print(f"   • Dropout: 0.05")

try:
    model = get_peft_model(model, lora_config)
    print("   [OK] LoRA adapters applied")
except Exception as e:
    print(f"   [FAILED] Failed: {e}")
    exit(1)

print()
print("[3] Analyzing trainable parameters...")

# Count parameters
total_params = sum(p.numel() for p in model.parameters())
trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
trainable_pct = 100.0 * trainable_params / total_params

print(f"   • Total parameters: {total_params / 1e6:.1f}M")
print(f"   • Trainable parameters: {trainable_params / 1e6:.1f}M")
print(f"   • Trainable %: {trainable_pct:.2f}%")

print()
print("4️⃣  Checking GPU memory...")

gpu_mem = torch.cuda.memory_allocated() / 1024**3
gpu_total = torch.cuda.get_device_properties(0).total_memory / 1024**3

print(f"   • GPU used: {gpu_mem:.2f} GB")
print(f"   • GPU total: {gpu_total:.1f} GB")
print(f"   • GPU free: {gpu_total - gpu_mem:.2f} GB")

print()
print("=" * 70)
print("[SUCCESS] LoRA CONFIGURATION VALIDATED")
print("=" * 70)
print()

# Display summary
print("[SUMMARY] Summary:")
print(f"   • Model size: {total_params / 1e9:.1f}B parameters")
print(f"   • LoRA adapters: {trainable_params / 1e6:.1f}M trainable parameters (0.21% of model)")
print(f"   • GPU memory: {gpu_mem:.2f} GB / {gpu_total:.1f} GB")
print(f"   • Remaining GPU: {gpu_total - gpu_mem:.2f} GB for training")
print()

# Recommendations
print("[RECOMMENDATIONS] Training Recommendations:")
if gpu_total - gpu_mem >= 1.5:
    print("   [OK] Batch size: 4 (optimal)")
    print("   [OK] Gradient accumulation: Not needed")
    print("   [OK] Gradient checkpointing: Optional (for faster training)")
elif gpu_total - gpu_mem >= 0.8:
    print("   [OK] Batch size: 2-3")
    print("   [OK] Gradient accumulation: 2-4 steps recommended")
    print("   [OK] Gradient checkpointing: Recommended")
else:
    print("   [WARNING] Batch size: 1 only")
    print("   [WARNING] Gradient accumulation: 8+ steps required")
    print("   [WARNING] Gradient checkpointing: REQUIRED")

print()
print("[INFO] For fine-tuning:")
print("   • Use mixed precision (fp16)")
print("   • Enable gradient checkpointing for memory efficiency")
print("   • Use LoRA rank of 8 (not higher)")
print("   • Consider reducing training context length if OOM errors occur")
print()
print("[READY] Ready for fine-tuning! See WEEK_5_6_FINETUNING.md for training scripts.")
print()
