#!/usr/bin/env python3
import sys
sys.stdout.reconfigure(encoding='utf-8')
import torch

print("[TEST] Testing Qwen2-VL 2B on RTX 3050...")

# Test 1: Check GPU
print(f"\n[1] GPU: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"    {torch.cuda.get_device_name(0)}")
    print(f"    Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

# Test 2: Load model (minimal)
print("\n[2] Loading model...")
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from PIL import Image
from pathlib import Path

model_id = "Qwen/Qwen2-VL-2B-Instruct"
print(f"    Model: {model_id}")

try:
    # Load model
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        model_id,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True
    )
    print("    [OK] Model loaded!")

    # Check memory
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated() / 1e9
        print(f"    VRAM used: {allocated:.2f} GB")

    # Test processor
    print("\n[3] Loading processor...")
    processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
    print("    [OK] Processor loaded!")

    # Test with sample image
    print("\n[4] Testing with sample image...")
    images = list(Path("data/train").glob("*.jpg"))[:1]
    if images:
        image = Image.open(images[0]).convert("RGB")
        print(f"    Image: {images[0].name}")

        # Qwen2-VL uses special chat template
        # Create conversation properly
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image"},
                    {"type": "text", "text": "Extract product attributes: brand, size, color, material, category. Answer in JSON format."}
                ]
            }
        ]

        # Apply chat template
        text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        print(f"    Prompt: {text[:100]}...")

        # Process inputs
        inputs = processor(text=text, images=image, return_tensors="pt")
        inputs = {k: v.to(model.device) if isinstance(v, torch.Tensor) else v for k, v in inputs.items()}

        print(f"    input_ids shape: {inputs['input_ids'].shape}")
        print(f"    pixel_values shape: {inputs['pixel_values'].shape}")
        print("    [OK] Inputs prepared!")

        # Generate
        with torch.no_grad():
            output = model.generate(**inputs, max_new_tokens=100, do_sample=False)
        result = processor.decode(output[0], skip_special_tokens=True)
        print(f"\n    Output: {result}")
        print("\n[SUCCESS] Qwen2-VL is working!")
    else:
        print("    [SKIP] No images found")

except Exception as e:
    print(f"    [ERROR] {e}")
    import traceback
    traceback.print_exc()