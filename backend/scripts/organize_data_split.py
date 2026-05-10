"""
Organize Data Split Script
Organizes labeled images into train/val/test split (70%/15%/15%)
"""

import os
import json
import shutil
import random
from pathlib import Path
from typing import List, Tuple


def organize_data_split(train_pct: float = 0.70, val_pct: float = 0.15):
    """
    Organize images into train/val/test split
    
    Args:
        train_pct: Percentage for training (default 70%)
        val_pct: Percentage for validation (default 15%)
        test_pct: Percentage for testing (rest, default 15%)
    """
    
    print("=" * 70)
    print("📁 ORGANIZING DATA SPLIT")
    print("=" * 70)
    print(f"Target split: {train_pct*100:.0f}% train, {val_pct*100:.0f}% val, {(1-train_pct-val_pct)*100:.0f}% test\n")
    
    train_dir = Path("data/train")
    val_dir = Path("data/val")
    test_dir = Path("data/test")
    
    # Create directories if they don't exist
    val_dir.mkdir(parents=True, exist_ok=True)
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # Get all images with labels
    image_files = []
    for img_file in sorted(train_dir.glob("*.jpg")):
        label_file = img_file.with_suffix(".json")
        if label_file.exists():
            image_files.append(img_file)
    
    print(f"📊 Found {len(image_files)} labeled images in data/train/\n")
    
    if len(image_files) == 0:
        print("❌ No labeled images found!")
        return
    
    # Shuffle images
    random.seed(42)
    random.shuffle(image_files)
    
    # Calculate split points
    train_size = int(len(image_files) * train_pct)
    val_size = int(len(image_files) * val_pct)
    
    train_images = image_files[:train_size]
    val_images = image_files[train_size:train_size + val_size]
    test_images = image_files[train_size + val_size:]
    
    print(f"📊 Split calculated:")
    print(f"   Train: {len(train_images)} images ({len(train_images)/len(image_files)*100:.1f}%)")
    print(f"   Val:   {len(val_images)} images ({len(val_images)/len(image_files)*100:.1f}%)")
    print(f"   Test:  {len(test_images)} images ({len(test_images)/len(image_files)*100:.1f}%)")
    print()
    
    # Move validation images
    print(f"Moving {len(val_images)} images to data/val/...")
    for img_file in val_images:
        label_file = img_file.with_suffix(".json")
        
        # Move image
        shutil.move(str(img_file), str(val_dir / img_file.name))
        
        # Move label
        shutil.move(str(label_file), str(val_dir / label_file.name))
    
    print(f"✅ Moved to data/val/")
    
    # Move test images
    print(f"Moving {len(test_images)} images to data/test/...")
    for img_file in test_images:
        label_file = img_file.with_suffix(".json")
        
        # Move image
        shutil.move(str(img_file), str(test_dir / img_file.name))
        
        # Move label
        shutil.move(str(label_file), str(test_dir / label_file.name))
    
    print(f"✅ Moved to data/test/")
    
    # Remaining stay in train_dir
    print(f"✅ {len(train_images)} images remain in data/train/")
    
    print("\n" + "=" * 70)
    print("✅ DATA SPLIT COMPLETE")
    print("=" * 70)
    print(f"data/train: {len(list(Path('data/train').glob('*.jpg')))} images")
    print(f"data/val:   {len(list(Path('data/val').glob('*.jpg')))} images")
    print(f"data/test:  {len(list(Path('data/test').glob('*.jpg')))} images")
    print("=" * 70)


if __name__ == "__main__":
    organize_data_split()
