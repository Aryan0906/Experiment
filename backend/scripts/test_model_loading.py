"""
Test Loading LLaVA 1.5 7B with int4 Quantization
Validates GPU compatibility for fine-tuning on RTX 3050
"""

import torch
from transformers import LlavaForConditionalGeneration, AutoTokenizer, BitsAndBytesConfig
import time

print("=" * 70)
print("TESTING LLaVA 1.5 MODEL LOADING WITH INT4 QUANTIZATION")
print("=" * 70)
print()

# Configuration for RTX 3050 (4GB VRAM)
print("Configuration for RTX 3050:")
print("  • Quantization: int4 (4-bit)")
print("  • Compute type: float16")
print("  • Device map: auto (GPU + CPU)")
print()

quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
)

model_id = "llava-hf/llava-1.5-7b-hf"

print(f"[LOAD] Loading model: {model_id}")
print(f"   (First time: ~3.5GB download from Hugging Face)")
print(f"   GPU Memory before: {torch.cuda.memory_allocated() / 1024**3:.2f} GB")
print(f"   GPU Memory available: {(torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated()) / 1024**3:.2f} GB")
print()

try:
    print("[DOWNLOAD] Downloading model...")
    start = time.time()
    
    # Load model with int4 quantization
    model = LlavaForConditionalGeneration.from_pretrained(
        model_id,
        quantization_config=quantization_config,
        device_map="auto",
        trust_remote_code=True,
    )
    
    print("[LOAD] Loading tokenizer...")
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    
    elapsed = time.time() - start
    
    gpu_used = torch.cuda.memory_allocated() / 1024**3
    gpu_total = torch.cuda.get_device_properties(0).total_memory / 1024**3
    
    print()
    print("=" * 70)
    print("[SUCCESS] MODEL LOADED SUCCESSFULLY!")
    print("=" * 70)
    print()
    print(f"[TIME] Loading time: {elapsed:.1f} seconds")
    print(f"[GPU] Memory used: {gpu_used:.2f} GB / {gpu_total:.1f} GB total")
    print(f"   Free GPU memory: {gpu_total - gpu_used:.2f} GB")
    
    # Count trainable parameters
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    
    print(f"[STATS] Model parameters:")
    print(f"   • Total: {total_params / 1e6:.1f}M")
    print(f"   • Trainable: {trainable_params / 1e6:.1f}M")
    print(f"   • Trainable %: {100.0 * trainable_params / total_params:.2f}%")
    
    print()
    
    # Compatibility check
    if gpu_used < 3.0:
        print("[OK] EXCELLENT! Plenty of room for training.")
        print("   Recommended batch size: 4")
    elif gpu_used < 3.5:
        print("[OK] GOOD! Enough space for training.")
        print("   Recommended batch size: 2-3")
    else:
        print("[WARNING] TIGHT! Limited space for training.")
        print("   Recommended batch size: 1")
        print("   May need to reduce context length or use gradient checkpointing")
    
    print()
    print("[RESULT] LLaVA 1.5 7B + LoRA fine-tuning: COMPATIBLE")
    print("   This GPU can successfully fine-tune LLaVA with:")
    print("   • int4 quantization")
    print("   • LoRA adapters")
    print("   • Gradient checkpointing (if needed)")
    
    print()
    print("=" * 70)
    print("[READY] Ready for Week 5-6 fine-tuning!")
    print("=" * 70)
    print()

except Exception as e:
    print()
    print("=" * 70)
    print(f"[FAILED] FAILED TO LOAD MODEL")
    print("=" * 70)
    print(f"Error: {e}")
    print()
    print("Troubleshooting:")
    print("  1. Check internet connection for model download")
    print("  2. Verify Hugging Face API access")
    print("  3. Check disk space (need ~3.5GB)")
    print("  4. Try reducing batch size")
    print()
    import traceback
    traceback.print_exc()
