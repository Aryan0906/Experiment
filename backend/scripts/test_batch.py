import sys, asyncio
sys.path.insert(0, 'c:/D_Drive_Archive/Experiment_local/backend')
from app.extraction.vlm import Qwen2VLExtractor
from pathlib import Path

async def test_batch():
    e = Qwen2VLExtractor()
    data_dir = Path("c:/D_Drive_Archive/Experiment_local/data/train")
    images = list(data_dir.glob("*.jpg"))[:3]
    
    print(f"[TEST] Batch extraction on {len(images)} images")
    for img in images:
        result = await e.extract(str(img))
        print(f"  - {img.name}: category={result.get('category')}, color={result.get('color')}")
    
    print("[SUCCESS] Batch test complete")

asyncio.run(test_batch())