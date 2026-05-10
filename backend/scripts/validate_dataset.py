"""
Validate Dataset Script
Validates all images and labels are properly formatted for training
"""

import os
import json
from pathlib import Path
from typing import List, Dict


def validate_dataset() -> bool:
    """
    Validate dataset integrity:
    - All images have corresponding labels
    - All labels have required fields
    - Check file format
    """
    
    print("=" * 70)
    print("VALIDATING DATASET")
    print("=" * 70)
    print()
    
    required_fields = ["brand", "size", "color", "material", "category"]
    errors = []
    stats = {}
    
    # Check each split
    for split in ["train", "val", "test"]:
        split_dir = Path(f"data/{split}")
        
        if not split_dir.exists():
            continue
        
        images = list(split_dir.glob("*.jpg"))
        labels = list(split_dir.glob("*.json"))
        
        print(f"[{split}]:")
        print(f"   Images: {len(images)}")
        print(f"   Labels: {len(labels)}")
        
        stats[split] = {
            "images": len(images),
            "labels": len(labels),
            "errors": []
        }
        
        # Check image/label match
        for img_file in images:
            label_file = img_file.with_suffix(".json")
            
            if not label_file.exists():
                error = f"Missing label for {img_file.name}"
                errors.append(error)
                stats[split]["errors"].append(error)
        
        # Check label format
        for label_file in labels:
            try:
                with open(label_file, "r") as f:
                    label = json.load(f)
                
                # Check required fields
                for field in required_fields:
                    if field not in label:
                        error = f"Missing '{field}' in {label_file.name}"
                        errors.append(error)
                        stats[split]["errors"].append(error)
                
                # Validate field types
                if not isinstance(label.get("brand"), str):
                    error = f"Invalid brand type in {label_file.name}"
                    errors.append(error)
                    stats[split]["errors"].append(error)
                
            except json.JSONDecodeError:
                error = f"Invalid JSON in {label_file.name}"
                errors.append(error)
                stats[split]["errors"].append(error)
            except Exception as e:
                error = f"Error reading {label_file.name}: {e}"
                errors.append(error)
                stats[split]["errors"].append(error)
        
        print()
    
    # Summary
    print("=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    
    total_images = sum(s.get("images", 0) for s in stats.values())
    total_labels = sum(s.get("labels", 0) for s in stats.values())
    
    print(f"Total images: {total_images}")
    print(f"Total labels: {total_labels}")
    print()
    
    # Check for mismatches
    if total_images != total_labels:
        print(f"[WARNING] Image/label mismatch: {total_images} images, {total_labels} labels")
        errors.append(f"Image/label mismatch")
    
    # Print errors
    if errors:
        print(f"\n[ERROR] {len(errors)} errors found:")
        for error in errors[:10]:  # Show first 10
            print(f"   - {error}")
        if len(errors) > 10:
            print(f"   ... and {len(errors) - 10} more")
        
        print("\n" + "=" * 70)
        print("[FAILED] VALIDATION FAILED")
        print("=" * 70)
        return False
    else:
        print("[OK] All images have valid labels")
        print("[OK] All labels have required fields")
        print("[OK] No format errors detected")
        
        print("\n" + "=" * 70)
        print("[SUCCESS] VALIDATION SUCCESSFUL")
        print("=" * 70)
        print()
        print("FINAL STATISTICS:")
        for split, data in stats.items():
            print(f"   {split:5s}: {data['images']:3d} images, {data['labels']:3d} labels")
        print()
        print("Dataset ready for training!")
        return True


if __name__ == "__main__":
    success = validate_dataset()
    exit(0 if success else 1)
