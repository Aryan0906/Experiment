#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Debug script to check LLaVA processor output"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from transformers import AutoProcessor
from PIL import Image
import json
from pathlib import Path

# Initialize processor
MODEL_ID = "llava-hf/llava-1.5-7b-hf"
processor = AutoProcessor.from_pretrained(MODEL_ID)

# Load a sample image and label
train_dir = Path("data/train")
image_files = sorted(list(train_dir.glob("*.jpg")))

if image_files:
    image_path = image_files[0]
    label_path = image_path.with_suffix(".json")
    
    print(f"Testing with image: {image_path.name}")
    
    image = Image.open(image_path).convert("RGB")
    
    # Load label
    if label_path.exists():
        with open(label_path) as f:
            labels = json.load(f)
    else:
        labels = {"brand": "test", "size": "test", "color": "test", "material": "test", "category": "test"}
    
    print(f"Label: {labels}")
    print()
    
    # Test 1: Basic text only
    print("=" * 80)
    print("Test 1: Text only (no image)")
    print("=" * 80)
    text_only = processor(text="Extract attributes: Brand: test")
    print(f"Input IDs shape: {text_only['input_ids'].shape}")
    print(f"Input IDs: {text_only['input_ids']}")
    print(f"Has attention_mask: {'attention_mask' in text_only}")
    print()
    
    # Test 2: Image only
    print("=" * 80)
    print("Test 2: Image only (no text)")
    print("=" * 80)
    img_only = processor(images=image)
    print(f"Pixel values shape: {img_only['pixel_values'].shape if 'pixel_values' in img_only else 'N/A'}")
    print(f"Has input_ids: {'input_ids' in img_only}")
    print()
    
    # Test 3: Image + text (images parameter)
    print("=" * 80)
    print("Test 3: Image + text using 'images' parameter")
    print("=" * 80)
    text = "Extract attributes: Brand: test"
    try:
        output = processor(images=image, text=text, return_tensors="pt")
        print(f"✓ Success!")
        print(f"  Pixel values shape: {output['pixel_values'].shape}")
        print(f"  Input IDs shape: {output['input_ids'].shape}")
        print(f"  Input IDs (first 20 tokens): {output['input_ids'][0, :20].tolist()}")
        print(f"  Attention mask shape: {output['attention_mask'].shape}")
        
        # Check for image tokens (usually high IDs)
        input_ids_list = output['input_ids'][0].tolist()
        print(f"  Total tokens: {len(input_ids_list)}")
        print(f"  Token range: {min(input_ids_list)} to {max(input_ids_list)}")
        print()
    except Exception as e:
        print(f"✗ Error: {e}")
        print()
    
    # Test 4: Image + text with chat template
    print("=" * 80)
    print("Test 4: Image + text with chat template")
    print("=" * 80)
    try:
        # Try to use apply_chat_template if available
        if hasattr(processor, 'apply_chat_template'):
            message = [
                {"role": "user", "content": [
                    {"type": "image"},
                    {"type": "text", "text": "Extract attributes: Brand: test"}
                ]}
            ]
            output = processor(message, images=image, return_tensors="pt")
            print(f"✓ Success with chat template!")
            print(f"  Input IDs shape: {output['input_ids'].shape}")
        else:
            print("✗ apply_chat_template not available")
    except Exception as e:
        print(f"✗ Error: {e}")
        print()
    
    # Test 5: Check processor config
    print("=" * 80)
    print("Test 5: Processor Configuration")
    print("=" * 80)
    if hasattr(processor, 'image_processor'):
        print(f"Image processor: {type(processor.image_processor)}")
    if hasattr(processor, 'tokenizer'):
        print(f"Tokenizer vocab size: {processor.tokenizer.vocab_size}")
        print(f"Tokenizer model max length: {processor.tokenizer.model_max_length}")
    print()
    
else:
    print("No images found in data/train")
