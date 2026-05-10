"""Minimal test for LLaVA loading"""
import torch
from transformers import LlavaForConditionalGeneration

print("Loading model...")
model = LlavaForConditionalGeneration.from_pretrained(
    "llava-hf/llava-1.5-7b-hf",
    torch_dtype=torch.float16,
    device_map="auto",
    trust_remote_code=True
)
print("Model loaded successfully!")
print(f"GPU memory: {torch.cuda.memory_allocated() / 1024**3:.2f} GB")
