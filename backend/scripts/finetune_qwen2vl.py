#!/usr/bin/env python3
# Qwen2-VL Fine-tuning - Runs in background
import sys
sys.stdout.reconfigure(encoding='utf-8')
import json
import torch
from pathlib import Path
from datetime import datetime
from PIL import Image
from tqdm import tqdm

from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from peft import LoraConfig, get_peft_model
from torch.utils.data import Dataset, DataLoader
from torch.optim import AdamW

print(f"[START] Qwen2-VL Fine-tuning - {datetime.now()}")

# Config
MODEL_ID = "Qwen/Qwen2-VL-2B-Instruct"
DATA_DIR = Path("data")
TRAIN_DIR = DATA_DIR / "train"
VAL_DIR = DATA_DIR / "val"
BATCH_SIZE = 1
GRADIENT_ACCUM = 4
NUM_EPOCHS = 3  # Reduced for faster completion
LR = 2e-4
LORA_R = 16

print(f"[CONFIG] Epochs: {NUM_EPOCHS}, Batch: {BATCH_SIZE}, LR: {LR}")

# Dataset
class ProductDataset(Dataset):
    def __init__(self, image_dir, processor):
        self.images = sorted(list(image_dir.glob("*.jpg")) + list(image_dir.glob("*.png")))
        self.processor = processor
        print(f"[DATA] Loaded {len(self.images)} images from {image_dir}")

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        img_path = self.images[idx]
        label_path = img_path.with_suffix(".json")
        
        image = Image.open(img_path).convert("RGB")
        
        if label_path.exists():
            with open(label_path) as f:
                labels = json.load(f)
        else:
            labels = {"brand": "unknown", "size": "unknown", "color": "unknown", "material": "unknown", "category": "unknown"}

        prompt = f"""Extract product attributes from this image.
Brand: {labels.get('brand', 'unknown')}
Size: {labels.get('size', 'unknown')}
Color: {labels.get('color', 'unknown')}
Material: {labels.get('material', 'unknown')}
Category: {labels.get('category', 'unknown')}"""

        messages = [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": prompt}]}]
        text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        
        inputs = self.processor(text=text, images=image, return_tensors="pt", padding=True)
        
        return {
            "pixel_values": inputs["pixel_values"][0],
            "input_ids": inputs["input_ids"][0],
            "attention_mask": inputs["attention_mask"][0],
            "labels": inputs["input_ids"][0].clone()
        }

def collate(batch):
    pixel_values = torch.stack([b["pixel_values"] for b in batch])
    max_len = max(b["input_ids"].shape[0] for b in batch)
    bs = len(batch)
    
    input_ids = torch.zeros(bs, max_len, dtype=torch.long)
    attention_mask = torch.zeros(bs, max_len, dtype=torch.long)
    labels = torch.full((bs, max_len), -100, dtype=torch.long)
    
    for i, b in enumerate(batch):
        l = b["input_ids"].shape[0]
        input_ids[i, :l] = b["input_ids"]
        attention_mask[i, :l] = b["attention_mask"]
        labels[i, :l] = b["labels"]
    
    return {"pixel_values": pixel_values, "input_ids": input_ids, "attention_mask": attention_mask, "labels": labels}

# Load model
print(f"[LOAD] Loading {MODEL_ID}...")
model = Qwen2VLForConditionalGeneration.from_pretrained(MODEL_ID, torch_dtype=torch.float16, device_map="auto", trust_remote_code=True)
processor = AutoProcessor.from_pretrained(MODEL_ID, trust_remote_code=True)

# LoRA
lora_config = LoraConfig(r=LORA_R, lora_alpha=32, target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"], lora_dropout=0.05, bias="none", task_type="CAUSAL_LM")
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

# Data
train_ds = ProductDataset(TRAIN_DIR, processor)
val_ds = ProductDataset(VAL_DIR, processor)
train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True, collate_fn=collate)
val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE, collate_fn=collate)

# Optimizer
optimizer = AdamW(model.parameters(), lr=LR)

# Training
print(f"\n[TRAIN] Starting...")
for epoch in range(NUM_EPOCHS):
    model.train()
    epoch_loss = 0
    pbar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{NUM_EPOCHS}")
    
    for batch_idx, batch in enumerate(pbar):
        batch = {k: v.to(model.device) for k, v in batch.items()}
        
        outputs = model(**batch)
        loss = outputs.loss / GRADIENT_ACCUM
        loss.backward()
        
        epoch_loss += loss.item()
        
        if (batch_idx + 1) % GRADIENT_ACCUM == 0:
            optimizer.step()
            optimizer.zero_grad()
            pbar.set_postfix({"loss": epoch_loss / (batch_idx + 1)})
    
    # Save checkpoint
    ckpt_path = Path("checkpoints/qwen2vl_finetuned") / f"epoch_{epoch+1}"
    ckpt_path.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(ckpt_path)
    print(f"[SAVE] Epoch {epoch+1} checkpoint: {ckpt_path}")

print(f"\n[DONE] Fine-tuning complete at {datetime.now()}")
print(f"[MODEL] Saved to checkpoints/qwen2vl_finetuned/")