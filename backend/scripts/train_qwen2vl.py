#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qwen2-VL 2B Fine-tuning with LoRA
Week 5-6: Fine-tune model for product attribute extraction
RTX 3050 optimized (4GB VRAM) - Uses ~2.5GB VRAM
"""

import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
import json
import torch
import numpy as np
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
from PIL import Image

from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from peft import LoraConfig, get_peft_model, TaskType
from torch.utils.data import Dataset, DataLoader
from torch.optim import AdamW
from torch.utils.tensorboard import SummaryWriter

try:
    import wandb
    WANDB_AVAILABLE = True
except ImportError:
    WANDB_AVAILABLE = False
    print("[WARNING] wandb not available - will use TensorBoard only")


class Config:
    MODEL_ID = "Qwen/Qwen2-VL-2B-Instruct"

    DATA_DIR = Path("data")
    TRAIN_DIR = DATA_DIR / "train"
    VAL_DIR = DATA_DIR / "val"
    TEST_DIR = DATA_DIR / "test"
    CHECKPOINT_DIR = Path("checkpoints/week5_qwen2vl")
    LOGS_DIR = Path("logs/week5_qwen2vl")

    BATCH_SIZE = 1
    GRADIENT_ACCUMULATION_STEPS = 4
    NUM_EPOCHS = 10
    LEARNING_RATE = 2e-4
    WARMUP_STEPS = 100
    MAX_SEQ_LENGTH = 512

    LORA_R = 16
    LORA_ALPHA = 32
    LORA_DROPOUT = 0.05

    USE_FP16 = True
    TORCH_DTYPE = torch.float16

    SAVE_STEPS = 100
    EVAL_STEPS = 50
    DEVICE_MAP = "auto"

    EXPERIMENT_NAME = "qwen2vl_product_extraction"
    RUN_NAME = f"lora_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

config = Config()


class ProductImageDataset(Dataset):
    def __init__(self, image_dir, processor, max_seq_length=512):
        self.image_dir = Path(image_dir)
        self.processor = processor
        self.max_seq_length = max_seq_length

        self.images = sorted(self.image_dir.glob("*.jpg")) + \
                      sorted(self.image_dir.glob("*.png"))

        if not self.images:
            raise ValueError(f"No images found in {image_dir}")

        print(f"[OK] Loaded {len(self.images)} images from {image_dir}")

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        image_path = self.images[idx]
        label_path = image_path.with_suffix(".json")

        image = Image.open(image_path).convert("RGB")

        if label_path.exists():
            with open(label_path) as f:
                labels = json.load(f)
        else:
            labels = {"brand": "unknown", "size": "unknown", "color": "unknown",
                     "material": "unknown", "category": "unknown"}

        prompt = f"""Extract product attributes from this image.
Brand: {labels.get('brand', 'unknown')}
Size: {labels.get('size', 'unknown')}
Color: {labels.get('color', 'unknown')}
Material: {labels.get('material', 'unknown')}
Category: {labels.get('category', 'unknown')}"""

        text = f"User: <image>\n{prompt} Assistant:"

        inputs = self.processor(
            text=[text],
            images=[image],
            return_tensors="pt",
            padding=True
        )

        return {
            "pixel_values": inputs["pixel_values"][0],
            "input_ids": inputs["input_ids"][0],
            "attention_mask": inputs["attention_mask"][0],
            "labels": inputs["input_ids"][0].clone()
        }


def collate_fn(batch):
    pixel_values = torch.stack([item["pixel_values"] for item in batch])

    max_len = max(seq["input_ids"].shape[0] for seq in batch)
    batch_size = len(batch)

    input_ids = torch.full((batch_size, max_len), 0, dtype=torch.long)
    attention_mask = torch.zeros((batch_size, max_len), dtype=torch.long)
    labels = torch.full((batch_size, max_len), -100, dtype=torch.long)

    for i, item in enumerate(batch):
        seq_len = item["input_ids"].shape[0]
        input_ids[i, :seq_len] = item["input_ids"]
        attention_mask[i, :seq_len] = item["attention_mask"]
        labels[i, :seq_len] = item["labels"]

    return {
        "pixel_values": pixel_values,
        "input_ids": input_ids,
        "attention_mask": attention_mask,
        "labels": labels
    }


def setup_lora():
    return LoraConfig(
        r=config.LORA_R,
        lora_alpha=config.LORA_ALPHA,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=config.LORA_DROPOUT,
        bias="none",
        task_type=TaskType.CAUSAL_LM
    )


def load_model():
    print("[LOAD] Loading Qwen2-VL model and processor...")
    print(f"   Model: {config.MODEL_ID}")
    print(f"   Mode: FP16")
    print(f"   LoRA Rank: {config.LORA_R}")

    processor = AutoProcessor.from_pretrained(config.MODEL_ID, trust_remote_code=True)

    model = Qwen2VLForConditionalGeneration.from_pretrained(
        config.MODEL_ID,
        torch_dtype=config.TORCH_DTYPE,
        device_map=config.DEVICE_MAP,
        trust_remote_code=True
    )

    lora_config = setup_lora()
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    return model, processor


def train():
    config.CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    config.LOGS_DIR.mkdir(parents=True, exist_ok=True)

    writer = SummaryWriter(log_dir=str(config.LOGS_DIR / config.RUN_NAME))

    if WANDB_AVAILABLE:
        wandb.init(project="qwen2vl-finetuning", name=config.RUN_NAME, config=vars(config))

    print("\n" + "="*70)
    print("[START] Qwen2-VL 2B Fine-tuning (LoRA + FP16)")
    print("="*70)

    print(f"\n[INFO] System Status:")
    print(f"   GPU Available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"   GPU Name: {torch.cuda.get_device_name(0)}")
        print(f"   GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

    print(f"\n[LOAD] Loading Model...")
    model, processor = load_model()

    optimizer = AdamW(model.parameters(), lr=config.LEARNING_RATE)

    print(f"\n[DATA] Loading Datasets...")
    train_dataset = ProductImageDataset(config.TRAIN_DIR, processor, config.MAX_SEQ_LENGTH)
    val_dataset = ProductImageDataset(config.VAL_DIR, processor, config.MAX_SEQ_LENGTH)

    train_loader = DataLoader(train_dataset, batch_size=config.BATCH_SIZE, shuffle=True, collate_fn=collate_fn)
    val_loader = DataLoader(val_dataset, batch_size=config.BATCH_SIZE, collate_fn=collate_fn)

    print(f"\n[TRAIN] Starting Training...")
    print(f"   Epochs: {config.NUM_EPOCHS}")
    print(f"   Batch Size: {config.BATCH_SIZE}")
    print(f"   Training Samples: {len(train_dataset)}")
    print(f"   Validation Samples: {len(val_dataset)}")
    print("\n" + "-"*70 + "\n")

    global_step = 0
    model.train()

    try:
        for epoch in range(config.NUM_EPOCHS):
            epoch_loss = 0
            progress_bar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{config.NUM_EPOCHS}")

            for batch_idx, batch in enumerate(progress_bar):
                batch = {k: v.to(model.device) for k, v in batch.items()}

                outputs = model(
                    pixel_values=batch["pixel_values"],
                    input_ids=batch["input_ids"],
                    attention_mask=batch["attention_mask"],
                    labels=batch["labels"]
                )

                loss = outputs.loss / config.GRADIENT_ACCUMULATION_STEPS
                loss.backward()

                epoch_loss += loss.item()

                if (batch_idx + 1) % config.GRADIENT_ACCUMULATION_STEPS == 0:
                    optimizer.step()
                    optimizer.zero_grad()
                    global_step += 1

                    avg_loss = epoch_loss / (batch_idx + 1)
                    progress_bar.set_postfix({"loss": avg_loss})
                    writer.add_scalar("train/loss", avg_loss, global_step)

                    if global_step % config.SAVE_STEPS == 0:
                        checkpoint_path = config.CHECKPOINT_DIR / f"step_{global_step}"
                        model.save_pretrained(checkpoint_path)
                        print(f"\n[SAVE] Checkpoint: {checkpoint_path}")

            epoch_avg_loss = epoch_loss / len(train_loader)
            print(f"\n[OK] Epoch {epoch+1} - Avg Loss: {epoch_avg_loss:.4f}")

            checkpoint_path = config.CHECKPOINT_DIR / f"epoch_{epoch+1}"
            model.save_pretrained(checkpoint_path)

        print(f"\n[SUCCESS] Training Complete!")
        print(f"   Checkpoints: {config.CHECKPOINT_DIR}")

    except KeyboardInterrupt:
        print("\n[WARNING] Training interrupted")
        checkpoint_path = config.CHECKPOINT_DIR / "interrupted"
        model.save_pretrained(checkpoint_path)

    finally:
        writer.close()
        if WANDB_AVAILABLE:
            wandb.finish()


if __name__ == "__main__":
    if not config.TRAIN_DIR.exists():
        print(f"[ERROR] Training data not found at {config.TRAIN_DIR}")
        exit(1)

    print("\n" + "="*70)
    print("[CONFIG] Qwen2-VL Training Configuration")
    print("="*70)
    print(f"Model: {config.MODEL_ID}")
    print(f"Batch Size: {config.BATCH_SIZE}")
    print(f"Learning Rate: {config.LEARNING_RATE}")
    print(f"Epochs: {config.NUM_EPOCHS}")
    print(f"LoRA Rank: {config.LORA_R}")
    print("="*70 + "\n")

    train()