#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test collate function with real data"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import torch
import json
from pathlib import Path
from PIL import Image
from transformers import AutoProcessor

# Setup
MODEL_ID = "llava-hf/llava-1.5-7b-hf"
processor = AutoProcessor.from_pretrained(MODEL_ID)
train_dir = Path("data/train")

# Batch collate function (same as training script)
def collate_fn(batch):
    """Custom collate function for LLaVA batches with variable sequence lengths"""
    pixel_values = torch.stack([item["pixel_values"] for item in batch])
    
    # Pad sequences to same length in batch
    max_seq_len = max(seq["input_ids"].shape[0] for seq in batch)
    input_ids = batch[0]["input_ids"].new_zeros(len(batch), max_seq_len)
    attention_masks = batch[0]["attention_mask"].new_zeros(len(batch), max_seq_len)
    labels = batch[0]["labels"].new_full((len(batch), max_seq_len), -100)
    
    for i, item in enumerate(batch):
        seq_len = item["input_ids"].shape[0]
        input_ids[i, :seq_len] = item["input_ids"]
        attention_masks[i, :seq_len] = item["attention_mask"]
        labels[i, :seq_len] = item["labels"]
    
    return {
        "pixel_values": pixel_values,
        "input_ids": input_ids,
        "attention_mask": attention_masks,
        "labels": labels
    }

# Load 2 images
images = sorted(list(train_dir.glob("*.jpg")))[:2]
print(f"Found {len(images)} images")

batch = []
for img_path in images:
    label_path = img_path.with_suffix(".json")
    
    image = Image.open(img_path).convert("RGB")
    with open(label_path) as f:
        labels = json.load(f)
    
    # Create text with <image> token
    text = f"""<image>
Extract: Brand: {labels.get('brand', 'unknown')}
Size: {labels.get('size', 'unknown')}"""
    
    inputs = processor(text=text, images=image, return_tensors="pt", padding=True)
    
    batch.append({
        "pixel_values": inputs["pixel_values"][0],
        "input_ids": inputs["input_ids"][0],
        "attention_mask": inputs["attention_mask"][0],
        "labels": inputs["input_ids"][0].clone()
    })
    
    print(f"  Image {len(batch)}: input_ids shape {batch[-1]['input_ids'].shape}")

print(f"\nBatch size: {len(batch)}")

try:
    print("\nApplying collate function...")
    collated = collate_fn(batch)
    
    print(f"✅ Collate successful!")
    print(f"  Pixel values: {collated['pixel_values'].shape}")
    print(f"  Input IDs: {collated['input_ids'].shape}")
    print(f"  Attention mask: {collated['attention_mask'].shape}")
    print(f"  Labels: {collated['labels'].shape}")
    
    # Check for image tokens (ID 32000)
    img_token_count = (collated['input_ids'] == 32000).sum().item()
    print(f"  Image tokens in batch: {img_token_count}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
