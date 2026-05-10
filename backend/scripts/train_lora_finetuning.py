#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLaVA 1.5 7B Fine-tuning with LoRA + FP16
Week 5-6: Fine-tune model for product attribute extraction
RTX 3050 optimized (4GB VRAM) - FP16 Mode (No 4-bit quantization)
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

# ML Libraries
from transformers import LlavaForConditionalGeneration, AutoImageProcessor
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


# ============================================================================
# Configuration
# ============================================================================

class Config:
    """Training configuration optimized for RTX 3050"""
    
    MODEL_ID = "llava-hf/llava-1.5-7b-hf"
    
    DATA_DIR = Path("data")
    TRAIN_DIR = DATA_DIR / "train"
    VAL_DIR = DATA_DIR / "val"
    TEST_DIR = DATA_DIR / "test"
    CHECKPOINT_DIR = Path("checkpoints/week5_lora")
    LOGS_DIR = Path("logs/week5_training")
    
    BATCH_SIZE = 1
    GRADIENT_ACCUMULATION_STEPS = 4
    NUM_EPOCHS = 10
    LEARNING_RATE = 2e-4
    WARMUP_STEPS = 100
    MAX_SEQ_LENGTH = 512
    
    LORA_R = 8
    LORA_ALPHA = 16
    LORA_DROPOUT = 0.05
    
    USE_FP16 = True
    TORCH_DTYPE = torch.float16
    
    SAVE_STEPS = 100
    EVAL_STEPS = 50
    GRADIENT_CHECKPOINTING = True
    DEVICE_MAP = "auto"
    
    EXPERIMENT_NAME = "llava_product_extraction_week5"
    RUN_NAME = f"lora_fp16_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

config = Config()


# ============================================================================
# Custom Processor (Workaround for tokenizer issues)
# ============================================================================

class SimpleLLaVAProcessor:
    """Simplified processor that handles images and text manually"""
    
    def __init__(self, image_processor, tokenizer):
        self.image_processor = image_processor
        self.tokenizer = tokenizer
        self.image_token = "<image>"
        num_added = tokenizer.add_tokens(["<image>"])
        self.image_token_id = tokenizer.convert_tokens_to_ids("<image>")
    
    def __call__(self, text=None, images=None, return_tensors=None, padding=False):
        """Process text and images"""
        result = {}
        
        if text and images:
            # Replace <image> placeholder with image tokens
            text_with_tokens = text.replace(self.image_token, "<image>" * 576)
            
            # Tokenize text
            text_encoding = self.tokenizer(
                text_with_tokens,
                return_tensors=return_tensors,
                padding=padding,
                max_length=self.MAX_SEQ_LENGTH,
                truncation=True
            )
            
            result["input_ids"] = text_encoding["input_ids"]
            result["attention_mask"] = text_encoding["attention_mask"]
            
            # Process images
            if isinstance(images, Image.Image):
                images = [images]
            
            pixel_values = self.image_processor(images=images, return_tensors=return_tensors)
            result["pixel_values"] = pixel_values["pixel_values"]
        
        return result


# ============================================================================
# Dataset
# ============================================================================

def collate_fn(batch):
    """Custom collate function for LLaVA batches"""
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


class ProductImageDataset(Dataset):
    """Product image dataset with JSON labels"""
    
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
        
        text_prompt = f"""<image>
Extract product attributes:
Brand: {labels.get('brand', 'unknown')}
Size: {labels.get('size', 'unknown')}
Color: {labels.get('color', 'unknown')}
Material: {labels.get('material', 'unknown')}
Category: {labels.get('category', 'unknown')}"""
        
        inputs = self.processor(
            text=text_prompt,
            images=image,
            return_tensors="pt",
            padding=True
        )
        
        return {
            "pixel_values": inputs["pixel_values"][0],
            "input_ids": inputs["input_ids"][0],
            "attention_mask": inputs["attention_mask"][0],
            "labels": inputs["input_ids"][0].clone()
        }


# ============================================================================
# Model Setup
# ============================================================================

def setup_dtype():
    """Setup FP16 dtype config"""
    return config.TORCH_DTYPE


def setup_lora():
    """Setup LoRA configuration"""
    return LoraConfig(
        r=config.LORA_R,
        lora_alpha=config.LORA_ALPHA,
        target_modules=["q_proj", "v_proj"],
        lora_dropout=config.LORA_DROPOUT,
        bias="none",
        task_type=TaskType.CAUSAL_LM
    )


def load_model():
    """Load LLaVA model with FP16 and LoRA using workaround"""
    
    print("[LOAD] Loading model and processor...")
    print(f"   Model: {config.MODEL_ID}")
    print(f"   Mode: FP16 (Workaround mode)")
    print(f"   LoRA Rank: {config.LORA_R}")
    
    from transformers import AutoTokenizer
    
    # Load model
    model = LlavaForConditionalGeneration.from_pretrained(
        config.MODEL_ID,
        torch_dtype=config.TORCH_DTYPE,
        device_map=config.DEVICE_MAP,
        trust_remote_code=True
    )
    
    # Load image processor only (works reliably)
    try:
        image_processor = AutoImageProcessor.from_pretrained(config.MODEL_ID, trust_remote_code=True)
    except Exception as e:
        print(f"[WARNING] AutoImageProcessor failed: {e}")
        print("[INFO] Using default image processor settings...")
        from transformers import CLIPImageProcessor
        image_processor = CLIPImageProcessor.from_pretrained("openai/clip-vit-large-patch14-336")
    
    # Load tokenizer separately
    try:
        tokenizer = AutoTokenizer.from_pretrained(config.MODEL_ID, trust_remote_code=True)
    except Exception as e:
        print(f"[WARNING] Tokenizer failed: {e}")
        print("[INFO] Using gpt2 tokenizer as fallback...")
        tokenizer = AutoTokenizer.from_pretrained("gpt2")
        tokenizer.pad_token = tokenizer.eos_token
    
    # Add image token to tokenizer
    tokenizer.add_tokens(["<image>"])
    model.config.image_token_index = tokenizer.convert_tokens_to_ids("<image>")
    
    # Create simple processor
    processor = SimpleLLaVAProcessor(image_processor, tokenizer)
    processor.MAX_SEQ_LENGTH = config.MAX_SEQ_LENGTH
    
    # Setup LoRA
    lora_config = setup_lora()
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    
    return model, processor


# ============================================================================
# Training
# ============================================================================

def train():
    """Main training loop"""
    
    config.CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    writer = SummaryWriter(log_dir=str(config.LOGS_DIR / config.RUN_NAME))
    
    if WANDB_AVAILABLE:
        wandb.init(
            project="llava-finetuning",
            name=config.RUN_NAME,
            config=vars(config)
        )
    
    print("\n" + "="*70)
    print("[START] LLaVA 1.5 Fine-tuning (LoRA + FP16)")
    print("="*70)
    
    print(f"\n[INFO] System Status:")
    print(f"   GPU Available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"   GPU Name: {torch.cuda.get_device_name(0)}")
        print(f"   GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
    print(f"   Device Map: {config.DEVICE_MAP}")
    
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
    print(f"   Batch Size: {config.BATCH_SIZE} (Gradient Accumulation: {config.GRADIENT_ACCUMULATION_STEPS})")
    print(f"   Effective Batch Size: {config.BATCH_SIZE * config.GRADIENT_ACCUMULATION_STEPS}")
    print(f"   Training Samples: {len(train_dataset)}")
    print(f"   Validation Samples: {len(val_dataset)}")
    print(f"   Total Steps: {len(train_loader) * config.NUM_EPOCHS}")
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
                    
                    if WANDB_AVAILABLE:
                        wandb.log({"train/loss": avg_loss}, step=global_step)
                    
                    if global_step % config.SAVE_STEPS == 0:
                        checkpoint_path = config.CHECKPOINT_DIR / f"step_{global_step}"
                        model.save_pretrained(checkpoint_path)
                        print(f"\n[SAVE] Checkpoint saved: {checkpoint_path}")
                
                if global_step % config.EVAL_STEPS == 0 and global_step > 0:
                    print(f"\n[VALIDATE] Validating at step {global_step}...")
                    val_loss = validate(model, val_loader)
                    writer.add_scalar("val/loss", val_loss, global_step)
                    
                    if WANDB_AVAILABLE:
                        wandb.log({"val/loss": val_loss}, step=global_step)
                    
                    model.train()
            
            epoch_avg_loss = epoch_loss / len(train_loader)
            print(f"\n[OK] Epoch {epoch+1} - Avg Loss: {epoch_avg_loss:.4f}")
            
            checkpoint_path = config.CHECKPOINT_DIR / f"epoch_{epoch+1}"
            model.save_pretrained(checkpoint_path)
            print(f"[SAVE] Epoch checkpoint saved: {checkpoint_path}")
        
        print(f"\n[VALIDATE] Final Validation...")
        final_val_loss = validate(model, val_loader)
        print(f"[OK] Final Validation Loss: {final_val_loss:.4f}")
        
        final_path = config.CHECKPOINT_DIR / "final"
        model.save_pretrained(final_path)
        print(f"\n[SUCCESS] Training Complete!")
        print(f"   Final model saved: {final_path}")
        print(f"   Checkpoints: {config.CHECKPOINT_DIR}")
        print(f"   Logs: {config.LOGS_DIR}")
    
    except KeyboardInterrupt:
        print("\n[WARNING] Training interrupted by user")
        checkpoint_path = config.CHECKPOINT_DIR / "interrupted"
        model.save_pretrained(checkpoint_path)
        print(f"   Last checkpoint saved: {checkpoint_path}")
    
    finally:
        writer.close()
        if WANDB_AVAILABLE:
            wandb.finish()


def validate(model, val_loader):
    """Validation loop"""
    model.eval()
    total_loss = 0
    
    with torch.no_grad():
        for batch in val_loader:
            batch = {k: v.to(model.device) for k, v in batch.items()}
            
            outputs = model(
                pixel_values=batch["pixel_values"],
                input_ids=batch["input_ids"],
                attention_mask=batch["attention_mask"],
                labels=batch["labels"]
            )
            
            total_loss += outputs.loss.item()
    
    avg_loss = total_loss / len(val_loader)
    return avg_loss


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    if not config.TRAIN_DIR.exists():
        print(f"[ERROR] Training data not found at {config.TRAIN_DIR}")
        exit(1)
    
    if not config.VAL_DIR.exists():
        print(f"[ERROR] Validation data not found at {config.VAL_DIR}")
        exit(1)
    
    print("\n" + "="*70)
    print("[CONFIG] Training Configuration")
    print("="*70)
    print(f"Model: {config.MODEL_ID}")
    print(f"Batch Size: {config.BATCH_SIZE}")
    print(f"Learning Rate: {config.LEARNING_RATE}")
    print(f"Epochs: {config.NUM_EPOCHS}")
    print(f"LoRA Rank: {config.LORA_R}")
    print(f"Mode: FP16 (Workaround)")
    print(f"Checkpoint Dir: {config.CHECKPOINT_DIR}")
    print("="*70 + "\n")
    
    train()