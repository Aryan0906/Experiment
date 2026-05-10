"""Test processor loading"""
from transformers import AutoProcessor, LlavaProcessor

print("Testing AutoProcessor...")
try:
    processor = AutoProcessor.from_pretrained("llava-hf/llava-1.5-7b-hf", trust_remote_code=True)
    print("AutoProcessor loaded!")
except Exception as e:
    print(f"AutoProcessor failed: {e}")

print("\nTesting LlavaProcessor...")
try:
    processor = LlavaProcessor.from_pretrained("llava-hf/llava-1.5-7b-hf", trust_remote_code=True)
    print("LlavaProcessor loaded!")
except Exception as e:
    print(f"LlavaProcessor failed: {e}")
