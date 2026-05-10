#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Quick processor test"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from transformers import AutoProcessor
from PIL import Image
import torch
from pathlib import Path

MODEL_ID = "llava-hf/llava-1.5-7b-hf"
processor = AutoProcessor.from_pretrained(MODEL_ID)

# Find an image
train_dir = Path("data/train")
images = sorted(list(train_dir.glob("*.jpg")))

if images:
    img_path = images[0]
    image = Image.open(img_path).convert("RGB")
    
    print(f"Image: {img_path.name}")
    print()
    
    # Check if <image> is special token
    print("Tokenizer info:")
    print(f"  Vocab size: {processor.tokenizer.vocab_size}")
    
    # Try to see image token
    try:
        if hasattr(processor.tokenizer, 'image_token_id'):
            print(f"  Image token ID: {processor.tokenizer.image_token_id}")
    except:
        pass
    
    # Test prompt with image token
    text_with_image = "<image>\nWhat is this?"
    print(f"\nPrompt: {repr(text_with_image)}")
    
    # Process
    print("\nProcessing...")
    inputs = processor(text=text_with_image, images=image, return_tensors="pt", padding=True)
    
    print(f"Keys: {inputs.keys()}")
    print(f"Pixel values shape: {inputs['pixel_values'].shape}")
    print(f"Input IDs shape: {inputs['input_ids'].shape}")
    print(f"Attention mask shape: {inputs['attention_mask'].shape}")
    
    print(f"\nInput IDs (full): {inputs['input_ids']}")
    print(f"\nFirst 20 tokens: {inputs['input_ids'][0, :20].tolist()}")
    
    # Decode to see what tokens are
    decoded = processor.tokenizer.decode(inputs['input_ids'][0])
    print(f"\nDecoded text:\n{decoded[:200]}")
    
else:
    print("No images found")
