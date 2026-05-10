"""
Auto-Labeling Script
Uses MockExtractor to automatically label all images in data/train/
"""

import os
import json
import asyncio
from pathlib import Path
from typing import Dict
import sys

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.extraction.vlm import MockExtractor


async def auto_label_images():
    """Auto-label all images in data/train/ that don't have labels yet"""
    
    print("=" * 70)
    print("🏷️  AUTO-LABELING IMAGES")
    print("=" * 70)
    print("Using MockExtractor to generate realistic labels\n")
    
    extractor = MockExtractor()
    train_dir = Path("data/train")
    
    if not train_dir.exists():
        print(f"❌ Error: {train_dir} not found")
        return 0
    
    # Get all images without labels
    image_files = list(train_dir.glob("*.jpg"))
    print(f"📊 Found {len(image_files)} images\n")
    
    labeled_count = 0
    skipped_count = 0
    
    for idx, img_file in enumerate(image_files, 1):
        label_file = img_file.with_suffix(".json")
        
        # Skip if already labeled
        if label_file.exists():
            skipped_count += 1
            continue
        
        try:
            # Extract using MockExtractor
            title = img_file.stem.replace("_", " ")
            attrs = await extractor.extract(
                image_url=str(img_file),
                description="",
                title=title
            )
            
            # Remove confidence (not needed in label)
            attrs.pop("confidence", None)
            
            # Save label
            with open(label_file, "w") as f:
                json.dump(attrs, f, indent=2)
            
            labeled_count += 1
            
            if idx % 50 == 0:
                print(f"  Progress: {idx}/{len(image_files)} images labeled")
            
        except Exception as e:
            print(f"  ⚠️  Error labeling {img_file.name}: {e}")
    
    print("\n" + "=" * 70)
    print("✅ AUTO-LABELING COMPLETE")
    print("=" * 70)
    print(f"Newly labeled: {labeled_count}")
    print(f"Already labeled: {skipped_count}")
    print(f"Total labeled: {labeled_count + skipped_count}")
    print("=" * 70)
    
    return labeled_count + skipped_count


if __name__ == "__main__":
    total = asyncio.run(auto_label_images())
    print(f"\n✨ {total} images ready for training")
