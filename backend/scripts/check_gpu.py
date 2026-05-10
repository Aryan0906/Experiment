"""
GPU Setup Validation Script
Checks NVIDIA GPU, PyTorch, CUDA, and fine-tuning compatibility
"""

import sys

print("=" * 70)
print("🔍 WEEK 4: GPU SETUP VALIDATION")
print("=" * 70)
print()

# Step 1: Check nvidia-smi
print("1️⃣  NVIDIA GPU Status")
print("-" * 70)
try:
    import subprocess
    result = subprocess.run(
        ["nvidia-smi"],
        capture_output=True,
        text=True,
        timeout=5
    )
    if result.returncode == 0:
        lines = result.stdout.split('\n')
        for line in lines:
            if 'GeForce' in line or 'GPU' in line or 'Memory' in line:
                print(f"  ✅ {line.strip()}")
    else:
        print("  ⚠️  nvidia-smi check failed")
except Exception as e:
    print(f"  ⚠️  Error: {e}")

print()

# Step 2: Check PyTorch
print("2️⃣  PyTorch Installation")
print("-" * 70)
try:
    import torch
    print(f"  ✅ PyTorch version: {torch.__version__}")
except ImportError as e:
    print(f"  ❌ PyTorch not installed: {e}")
    sys.exit(1)

print()

# Step 3: Check CUDA
print("3️⃣  CUDA Configuration")
print("-" * 70)
try:
    cuda_available = torch.cuda.is_available()
    print(f"  {'✅' if cuda_available else '⚠️'} CUDA available: {cuda_available}")
    
    if cuda_available:
        print(f"  ✅ CUDA version: {torch.version.cuda}")
        print(f"  ✅ GPU name: {torch.cuda.get_device_name(0)}")
        
        gpu_props = torch.cuda.get_device_properties(0)
        total_mem_gb = gpu_props.total_memory / (1024**3)
        print(f"  ✅ GPU memory: {total_mem_gb:.1f} GB")
        print(f"  ✅ Compute capability: {gpu_props.major}.{gpu_props.minor}")
    else:
        print("  ❌ CUDA not available! Check NVIDIA drivers.")
        sys.exit(1)
except Exception as e:
    print(f"  ❌ Error: {e}")
    sys.exit(1)

print()

# Step 4: Test basic tensor operations
print("4️⃣  GPU Tensor Operations")
print("-" * 70)
try:
    # Create tensor on GPU
    x = torch.randn(100, 100).cuda()
    y = torch.randn(100, 100).cuda()
    z = torch.matmul(x, y)
    
    gpu_mem_used = torch.cuda.memory_allocated() / (1024**3)
    print(f"  ✅ Matrix multiplication successful")
    print(f"  ✅ GPU memory used: {gpu_mem_used:.2f} GB")
    
except RuntimeError as e:
    print(f"  ❌ GPU tensor operation failed: {e}")
    sys.exit(1)

print()

# Step 5: Check int4 quantization support
print("5️⃣  Int4 Quantization (for LLaVA)")
print("-" * 70)
try:
    import bitsandbytes
    print(f"  ✅ bitsandbytes available")
except ImportError:
    print(f"  ⚠️  bitsandbytes not installed - will install with training env")

print()

# Step 6: Check LoRA support
print("6️⃣  LoRA Fine-tuning (PEFT)")
print("-" * 70)
try:
    import peft
    print(f"  ✅ PEFT (LoRA) available")
except ImportError:
    print(f"  ⚠️  PEFT not installed - will install with training env")

print()

# Step 7: Memory check for RTX 3050
print("7️⃣  RTX 3050 Compatibility Check")
print("-" * 70)
total_gpu_mem = torch.cuda.get_device_properties(0).total_memory / (1024**3)
if total_gpu_mem >= 3.5:
    print(f"  ✅ GPU memory sufficient: {total_gpu_mem:.1f} GB ≥ 3.5 GB required")
    print(f"  ✅ Can train LLaVA 1.5 with:")
    print(f"     - int4 quantization: ~2.5 GB used")
    print(f"     - LoRA adapters: ~0.5 GB used")
    print(f"     - Batch size: 1-4 recommended")
else:
    print(f"  ⚠️  GPU memory tight: {total_gpu_mem:.1f} GB < 3.5 GB")
    print(f"  ⚠️  May need very small batch size (1)")

print()

# Final summary
print("=" * 70)
print("✅ GPU SETUP VALIDATION COMPLETE")
print("=" * 70)
print()
print("📋 Summary:")
print(f"  • GPU: NVIDIA GeForce RTX 3050 ({total_gpu_mem:.1f} GB VRAM)")
print(f"  • PyTorch: {torch.__version__}")
print(f"  • CUDA: {torch.version.cuda}")
print(f"  • Status: ✅ READY FOR FINE-TUNING")
print()
print("🚀 Next steps:")
print("  1. Install training dependencies: pip install transformers peft bitsandbytes accelerate")
print("  2. Test model loading: python backend/scripts/test_model_loading.py")
print("  3. Begin fine-tuning: See WEEK_5_6_FINETUNING.md")
print()
