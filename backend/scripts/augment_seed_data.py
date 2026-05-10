"""
Synthetic Data Augmentation Script
Creates 400+ augmented images from 8 seed products for VLM fine-tuning
"""

import os
import json
import requests
from PIL import Image, ImageEnhance
from io import BytesIO
from pathlib import Path
from typing import List, Dict
import time

# ============================
# SEED PRODUCT DATA
# ============================

SEED_PRODUCTS = [
    {
        "id": "seed_001",
        "title": "Classic Blue Cotton T-Shirt",
        "brand": "Nike",
        "size": "M",
        "color": "Blue",
        "material": "Cotton",
        "category": "T-Shirt",
        "url": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=60"
    },
    {
        "id": "seed_002",
        "title": "Women's Red Kurta",
        "brand": "FabIndia",
        "size": "L",
        "color": "Red",
        "material": "Cotton",
        "category": "Kurta",
        "url": "https://images.unsplash.com/photo-1595777707802-b2d1ef58165f?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=60"
    },
    {
        "id": "seed_003",
        "title": "Men's Denim Jeans",
        "brand": "Levi's",
        "size": "32",
        "color": "Black",
        "material": "Denim",
        "category": "Jeans",
        "url": "https://images.unsplash.com/photo-1542272604-787c3835535d?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=60"
    },
    {
        "id": "seed_004",
        "title": "Leather Crossbody Bag",
        "brand": "Local",
        "size": "M",
        "color": "Brown",
        "material": "Leather",
        "category": "Bag",
        "url": "https://images.unsplash.com/photo-1548036328-c9fa89d128fa?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=60"
    },
    {
        "id": "seed_005",
        "title": "Running Shoes",
        "brand": "Adidas",
        "size": "9",
        "color": "Black",
        "material": "Mesh",
        "category": "Shoes",
        "url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=60"
    },
    {
        "id": "seed_006",
        "title": "Silver Pendant Necklace",
        "brand": "Local",
        "size": "Free",
        "color": "Silver",
        "material": "Sterling Silver",
        "category": "Jewelry",
        "url": "https://images.unsplash.com/photo-1515562141207-6811bcb33eaf?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=60"
    },
    {
        "id": "seed_007",
        "title": "Cotton Saree",
        "brand": "Local",
        "size": "Free",
        "color": "Green",
        "material": "Cotton",
        "category": "Saree",
        "url": "https://images.unsplash.com/photo-1608232243692-f6741f8a8f11?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=60"
    },
    {
        "id": "seed_008",
        "title": "Formal White Shirt",
        "brand": "Allen Solly",
        "size": "L",
        "color": "White",
        "material": "Cotton",
        "category": "Shirt",
        "url": "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=60"
    },
]

# ============================
# AUGMENTATION FUNCTIONS
# ============================

def rotate_image(image: Image.Image, degrees: int) -> Image.Image:
    """Rotate image by specified degrees"""
    return image.rotate(degrees, expand=False, fillcolor=(255, 255, 255))

def adjust_brightness(image: Image.Image, factor: float) -> Image.Image:
    """Adjust image brightness"""
    enhancer = ImageEnhance.Brightness(image)
    return enhancer.enhance(factor)

def adjust_contrast(image: Image.Image, factor: float) -> Image.Image:
    """Adjust image contrast"""
    enhancer = ImageEnhance.Contrast(image)
    return enhancer.enhance(factor)

def adjust_color(image: Image.Image, factor: float) -> Image.Image:
    """Adjust image color saturation"""
    enhancer = ImageEnhance.Color(image)
    return enhancer.enhance(factor)

def flip_image(image: Image.Image) -> Image.Image:
    """Flip image horizontally"""
    return image.transpose(Image.FLIP_LEFT_RIGHT)

def crop_and_resize(image: Image.Image) -> Image.Image:
    """Crop center and resize"""
    w, h = image.size
    crop_size = min(w, h)
    left = (w - crop_size) // 2
    top = (h - crop_size) // 2
    right = left + crop_size
    bottom = top + crop_size
    cropped = image.crop((left, top, right, bottom))
    return cropped.resize((400, 400))

# ============================
# MAIN EXECUTION
# ============================

def create_augmentations():
    """Create augmented dataset"""
    
    # Ensure data directory exists
    os.makedirs("data/train", exist_ok=True)
    
    print("=" * 70)
    print("SYNTHETIC DATA AUGMENTATION")
    print("=" * 70)
    print(f"Creating training data from 8 seed products")
    print(f"[INFO] Saved to: data/train/")
    print(f"[INFO] Ready for LLaVA fine-tuning!\n")
    
    total_created = 0
    start_time = time.time()
    
    for product_idx, product in enumerate(SEED_PRODUCTS, 1):
        product_id = product["id"]
        print(f"[{product_idx}/8] Processing {product_id}...")
        
        try:
            # Download original image
            print(f"  [DOWNLOAD] Downloading image...", end=" ")
            response = requests.get(product["url"], timeout=10)
            response.raise_for_status()
            
            original_image = Image.open(BytesIO(response.content)).convert("RGB")
            print("[OK]")
            
            # Save original
            original_filename = f"data/train/{product_id}_000.jpg"
            original_image.save(original_filename, quality=95)
            
            # Save original label
            label = {
                "brand": product["brand"],
                "size": product["size"],
                "color": product["color"],
                "material": product["material"],
                "category": product["category"]
            }
            
            with open(f"data/train/{product_id}_000.json", "w") as f:
                json.dump(label, f)
            
            total_created += 1
            
            # Create augmentations
            augmentation_count = 0
            
            # Augmentation 1: Rotations (10 versions)
            for i in range(10):
                try:
                    degrees = -20 + (i * 4)  # -20 to +16 degrees
                    aug_image = rotate_image(original_image, degrees)
                    aug_filename = f"data/train/{product_id}_01{i:02d}.jpg"
                    aug_image.save(aug_filename, quality=95)
                    
                    with open(aug_filename.replace(".jpg", ".json"), "w") as f:
                        json.dump(label, f)
                    
                    augmentation_count += 1
                except Exception as e:
                    print(f"    [WARNING] Rotation {i} failed: {e}")
            
            # Augmentation 2: Brightness (10 versions)
            for i in range(10):
                try:
                    factor = 0.6 + (i * 0.08)  # 0.6 to 1.32
                    aug_image = adjust_brightness(original_image, factor)
                    aug_filename = f"data/train/{product_id}_02{i:02d}.jpg"
                    aug_image.save(aug_filename, quality=95)
                    
                    with open(aug_filename.replace(".jpg", ".json"), "w") as f:
                        json.dump(label, f)
                    
                    augmentation_count += 1
                except Exception as e:
                    print(f"    [WARNING] Brightness {i} failed: {e}")
            
            # Augmentation 3: Contrast (10 versions)
            for i in range(10):
                try:
                    factor = 0.7 + (i * 0.07)  # 0.7 to 1.33
                    aug_image = adjust_contrast(original_image, factor)
                    aug_filename = f"data/train/{product_id}_03{i:02d}.jpg"
                    aug_image.save(aug_filename, quality=95)
                    
                    with open(aug_filename.replace(".jpg", ".json"), "w") as f:
                        json.dump(label, f)
                    
                    augmentation_count += 1
                except Exception as e:
                    print(f"    [WARNING] Contrast {i} failed: {e}")
            
            # Augmentation 4: Color/Saturation (10 versions)
            for i in range(10):
                try:
                    factor = 0.8 + (i * 0.08)  # 0.8 to 1.52
                    aug_image = adjust_color(original_image, factor)
                    aug_filename = f"data/train/{product_id}_04{i:02d}.jpg"
                    aug_image.save(aug_filename, quality=95)
                    
                    with open(aug_filename.replace(".jpg", ".json"), "w") as f:
                        json.dump(label, f)
                    
                    augmentation_count += 1
                except Exception as e:
                    print(f"    [WARNING] Color {i} failed: {e}")
            
            # Augmentation 5: Combined (10 versions)
            for i in range(10):
                try:
                    # Combine multiple augmentations
                    aug_image = original_image.copy()
                    
                    # Rotate
                    degrees = -15 + (i * 3)
                    aug_image = rotate_image(aug_image, degrees)
                    
                    # Adjust brightness
                    factor = 0.8 + (i * 0.04)
                    aug_image = adjust_brightness(aug_image, factor)
                    
                    # Flip every other
                    if i % 2 == 0:
                        aug_image = flip_image(aug_image)
                    
                    aug_filename = f"data/train/{product_id}_05{i:02d}.jpg"
                    aug_image.save(aug_filename, quality=95)
                    
                    with open(aug_filename.replace(".jpg", ".json"), "w") as f:
                        json.dump(label, f)
                    
                    augmentation_count += 1
                except Exception as e:
                    print(f"    [WARNING] Combined aug {i} failed: {e}")
            
            total_created += augmentation_count
            print(f"  [OK] Created: 1 original + {augmentation_count} augmentations = {augmentation_count + 1} images")
            
        except requests.exceptions.RequestException as e:
            print(f"  [ERROR] Failed to download: {e}")
        except Exception as e:
            print(f"  [ERROR] Error processing {product_id}: {e}")
    
    elapsed = time.time() - start_time
    
    print("\n" + "=" * 70)
    print("[SUCCESS] AUGMENTATION COMPLETE")
    print("=" * 70)
    print(f"Total images created: {total_created}")
    print(f"Time taken: {elapsed:.1f} seconds")
    print(f"Average: {elapsed/len(SEED_PRODUCTS):.1f} seconds per product")
    print(f"\n[INFO] Location: data/train/")
    print(f"[INFO] Structure:")
    print(f"   - {total_created} images (.jpg files)")
    print(f"   - {total_created} labels (.json files)")
    print(f"\nNext steps:")
    print(f"   1. Verify: python backend/scripts/validate_dataset.py")
    print(f"   2. Collect more images if needed (target: 500-1000)")
    print(f"   3. Organize into train/val/test split (70%/15%/15%)")
    print("=" * 70)

if __name__ == "__main__":
    create_augmentations()
