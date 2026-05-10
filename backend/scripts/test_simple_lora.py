"""
Simplified LoRA Test without 4-bit quantization
Tests basic model loading and LoRA configuration
"""

import torch
from transformers import LlavaForConditionalGeneration, AutoTokenizer
from peft import get_peft_model, LoraConfig, TaskType

print("=" * 70)
print("SIMPLIFIED LoRA TEST (FP16 - No 4-bit Quantization)")
print("=" * 70)
print()

model_id = "llava-hf/llava-1.5-7b-hf"

# Check GPU memory
gpu_total = torch.cuda.get_device_properties(0).total_memory / 1024**3
print(f"[INFO] GPU Total Memory: {gpu_total:.2f} GB")
print(f"[INFO] This test loads model in FP16 (needs ~7GB, may use CPU)")
print()

# Try loading in FP16 with device_map auto
print("[1] Loading model in FP16 with device_map='auto'...")
try:
    model = LlavaForConditionalGeneration.from_pretrained(
        model_id,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True,
    )
    print("   [OK] Model loaded")
    
    # Show memory usage
    gpu_used = torch.cuda.memory_allocated() / 1024**3
    print(f"   [INFO] GPU used: {gpu_used:.2f} GB")
    
except Exception as e:
    print(f"   [FAILED] {e}")
    exit(1)

# LoRA config
print()
print("[2] Applying LoRA adapters...")
lora_config = LoraConfig(
    r=8,
    lora_alpha=16,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type=TaskType.CAUSAL_LM,
)

try:
    model = get_peft_model(model, lora_config)
    print("   [OK] LoRA applied")
    
    # Count parameters
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"   [INFO] Total: {total/1e9:.1f}B params")
    print(f"   [INFO] Trainable: {trainable/1e6:.1f}M params ({100*trainable/total:.2f}%)")
    
except Exception as e:
    print(f"   [FAILED] {e}")
    exit(1)

print()
print("=" * 70)
print("[SUCCESS] LoRA configuration working!")
print("=" * 70)
print()
print("Next steps:")
print("  1. For 4-bit quantization: Resolve bitsandbytes Windows compatibility")
print("  2. For training: Use this config with train_lora_finetuning.py")
print("  3. Alternative: Use RunPod/Vast.ai for cloud GPU training")
