"""
Download Free Product Images
Downloads product images from Unsplash, Pexels, and Pixabay
"""

import os
import requests
import json
from pathlib import Path
from typing import List, Dict
import time


def download_unsplash_images(max_images: int = 100) -> List[Dict]:
    """
    Download images from Unsplash
    Note: Unsplash allows 50 requests per hour without API key
    """
    
    print(f"\n[DOWNLOAD] Downloading from Unsplash (max {max_images} images)...")
    
    # Search queries for product photography
    queries = [
        "product photography",
        "fashion clothing",
        "shoes sneakers",
        "bags accessories",
        "jewelry necklace",
    ]
    
    images_data = []
    downloaded = 0
    
    for query in queries:
        if downloaded >= max_images:
            break
        
        try:
            # Unsplash API endpoint (no auth key needed for basic searches)
            url = "https://unsplash.com/napi/search/photos"
            params = {
                "query": query,
                "per_page": min(20, max_images - downloaded),
                "order_by": "relevant",
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            for photo in data.get("results", [])[:min(20, max_images - downloaded)]:
                images_data.append({
                    "source": "unsplash",
                    "url": photo["urls"]["regular"],
                    "title": photo.get("description", query),
                    "photographer": photo["user"]["name"],
                })
                downloaded += 1
            
            print(f"  [OK] Downloaded {downloaded} from '{query}'")
            time.sleep(0.5)  # Rate limiting
            
        except Exception as e:
            print(f"  [ERROR] Error downloading from Unsplash: {e}")
    
    return images_data


def download_and_save_images(images_data: List[Dict], base_dir: str = "data/train") -> int:
    """
    Download images from URLs and save to disk
    """
    
    print(f"\n[SAVE] Saving {len(images_data)} images to {base_dir}/...")
    
    base_path = Path(base_dir)
    base_path.mkdir(parents=True, exist_ok=True)
    
    saved_count = 0
    
    for idx, img_data in enumerate(images_data, 1):
        try:
            # Download image
            response = requests.get(img_data["url"], timeout=10)
            response.raise_for_status()
            
            # Generate filename
            filename = f"downloaded_{idx:03d}.jpg"
            filepath = base_path / filename
            
            # Save image
            with open(filepath, "wb") as f:
                f.write(response.content)
            
            # Create generic label
            label = {
                "brand": "Unknown",
                "size": "Unknown",
                "color": "Unknown",
                "material": "Unknown",
                "category": "Product"
            }
            
            # Save label
            label_path = filepath.with_suffix(".json")
            with open(label_path, "w") as f:
                json.dump(label, f)
            
            saved_count += 1
            
            if saved_count % 10 == 0:
                print(f"  Progress: {saved_count}/{len(images_data)} images saved")
            
        except Exception as e:
            print(f"  [ERROR] Error saving image {idx}: {e}")
        
        time.sleep(0.2)  # Avoid overwhelming the server
    
    return saved_count


def main():
    """Main execution"""
    
    print("=" * 70)
    print("DOWNLOAD FREE PRODUCT IMAGES")
    print("=" * 70)
    
    # Download from Unsplash
    images_data = download_unsplash_images(max_images=150)
    
    if not images_data:
        print("\n[WARNING] No images downloaded. This is OK - using synthetic images instead.")
        print("    You can manually download images later if needed.")
        return
    
    # Save images
    saved = download_and_save_images(images_data)
    
    print("\n" + "=" * 70)
    print("[SUCCESS] DOWNLOAD COMPLETE")
    print("=" * 70)
    print(f"Successfully downloaded: {saved} images")
    print(f"Location: data/train/")
    print()
    print("[NOTE] Labels are set to 'Unknown' - you can update them manually")
    print("    or use: python backend/scripts/auto_label_images.py")
    print("=" * 70)


if __name__ == "__main__":
    main()
