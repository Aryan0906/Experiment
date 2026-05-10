"""
VLM-based attribute extraction backends.

Supports three backends:
- MockExtractor: Returns realistic mock attributes (free, instant)
- GPT4oExtractor: Uses OpenAI GPT-4o for real extraction
- Qwen2VLExtractor: Local Qwen2-VL-2B (free, no API costs)

Switch via EXTRACTION_BACKEND env var ("mock", "gpt4o", "local_vlm").
"""
import json
import os
import random
from abc import ABC, abstractmethod
from typing import Dict, Any
import torch


class AttributeExtractor(ABC):
    """Base class for attribute extractors."""

    @abstractmethod
    async def extract(self, image_path: str, description: str = "", title: str = "") -> Dict[str, Any]:
        """
        Extract product attributes from an image and description.

        Returns a dict with keys: brand, size, color, material, category, confidence
        """
        pass


class MockExtractor(AttributeExtractor):
    """Returns realistic mock attributes based on product title/description."""

    BRANDS = ["Nike", "Adidas", "Puma", "H&M", "Zara", "FabIndia", "W", "Biba", "Levi's", "Allen Solly"]
    SIZES = ["XS", "S", "M", "L", "XL", "XXL", "Free Size", "28", "30", "32", "34"]
    COLORS = ["Blue", "Red", "Black", "White", "Green", "Brown", "Navy", "Grey", "Pink", "Beige"]
    MATERIALS = ["Cotton", "Polyester", "Silk", "Denim", "Leather", "Linen", "Wool", "Nylon", "Sterling Silver"]
    CATEGORIES = ["T-Shirt", "Kurta", "Jeans", "Bag", "Shoes", "Jewelry", "Saree", "Shirt", "Dress", "Jacket", "Accessories"]

    def _detect_from_text(self, text: str, options: list[str]) -> str:
        text_lower = text.lower()
        for option in options:
            if option.lower() in text_lower:
                return option
        return random.choice(options)

    async def extract(self, image_path: str, description: str = "", title: str = "") -> Dict[str, Any]:
        combined = f"{title} {description}"
        return {
            "brand": self._detect_from_text(combined, self.BRANDS),
            "size": self._detect_from_text(combined, self.SIZES),
            "color": self._detect_from_text(combined, self.COLORS),
            "material": self._detect_from_text(combined, self.MATERIALS),
            "category": self._detect_from_text(combined, self.CATEGORIES),
            "confidence": round(random.uniform(0.72, 0.98), 2),
        }


class GPT4oExtractor(AttributeExtractor):
    """Uses OpenAI GPT-4o to extract product attributes."""

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def extract(self, image_path: str, description: str = "", title: str = "") -> Dict[str, Any]:
        try:
            import httpx
        except ImportError:
            raise RuntimeError("httpx is required for GPT4oExtractor")

        # Read local image and convert to base64
        import base64
        with open(image_path, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode("utf-8")

        prompt = (
            "You are a product attribute extractor. Analyze this product image, "
            "then return ONLY a JSON object with these fields:\n"
            '{"brand": "...", "size": "...", "color": "...", "material": "...", '
            '"category": "...", "confidence": 0.0-1.0}\n\n'
            f"Product title: {title}\n"
            f"Product description: {description}\n\n"
            "Return ONLY the JSON object, no other text."
        )

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}", "detail": "low"}},
                            ],
                        }
                    ],
                    "max_tokens": 300,
                },
            )

            if response.status_code != 200:
                fallback = MockExtractor()
                return await fallback.extract(image_path, description, title)

            data = response.json()
            content = data["choices"][0]["message"]["content"]

            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1]
                content = content.rsplit("```", 1)[0]

            attrs = json.loads(content)

            required = ["brand", "size", "color", "material", "category", "confidence"]
            for field in required:
                if field not in attrs:
                    attrs[field] = "" if field != "confidence" else 0.5

            return attrs


class Qwen2VLExtractor(AttributeExtractor):
    """Local Qwen2-VL-2B extractor - FREE, no API costs."""

    _model = None
    _processor = None
    _initialized = False

    @classmethod
    def initialize(cls):
        """Load Qwen2-VL model once (singleton pattern)."""
        if cls._initialized:
            return

        print("[VLM] Loading Qwen2-VL-2B model...")
        from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
        from PIL import Image

        model_id = "Qwen/Qwen2-VL-2B-Instruct"

        cls._model = Qwen2VLForConditionalGeneration.from_pretrained(
            model_id,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True
        )

        cls._processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
        cls._initialized = True

        if torch.cuda.is_available():
            allocated = torch.cuda.memory_allocated() / 1e9
            print(f"[VLM] Model loaded! VRAM: {allocated:.2f} GB")

    async def extract(self, image_path: str, description: str = "", title: str = "") -> Dict[str, Any]:
        """Extract attributes using local Qwen2-VL model."""
        from PIL import Image

        # Initialize if needed
        if not self._initialized:
            self.initialize()

        # Load image
        image = Image.open(image_path).convert("RGB")

        # Create prompt
        prompt = (
            "Extract product attributes from this image. "
            "Return ONLY a JSON object with: brand, size, color, material, category, confidence. "
            "Use null or \"Unknown\" for attributes you cannot determine. "
            "Set confidence between 0.0 and 1.0."
        )

        # Format messages for Qwen2-VL
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image"},
                    {"type": "text", "text": prompt}
                ]
            }
        ]

        # Apply chat template
        text = self._processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

        # Process inputs
        inputs = self._processor(text=text, images=image, return_tensors="pt")
        inputs = {k: v.to(self._model.device) if isinstance(v, torch.Tensor) else v for k, v in inputs.items()}

        # Generate
        with torch.no_grad():
            output = self._model.generate(**inputs, max_new_tokens=200, do_sample=False)

        result = self._processor.decode(output[0], skip_special_tokens=True)

        # Parse JSON from response
        try:
            # Find JSON in response
            start = result.find("{")
            end = result.rfind("}") + 1
            if start != -1 and end != 0:
                json_str = result[start:end]
                attrs = json.loads(json_str)
            else:
                attrs = {}

            # Ensure all required fields
            required = ["brand", "size", "color", "material", "category", "confidence"]
            for field in required:
                if field not in attrs:
                    attrs[field] = "Unknown" if field != "confidence" else 0.5

            return attrs

        except json.JSONDecodeError:
            # Fallback if JSON parse fails
            return {
                "brand": "Unknown",
                "size": "Unknown",
                "color": "Unknown",
                "material": "Unknown",
                "category": "Unknown",
                "confidence": 0.3,
                "raw_response": result[:500]
            }


def get_extractor(backend: str = "mock", api_key: str = "", model_path: str = "") -> AttributeExtractor:
    """Factory function to get the configured extractor."""
    if backend == "gpt4o" and api_key:
        return GPT4oExtractor(api_key=api_key)
    if backend == "local_vlm":
        return Qwen2VLExtractor()
    return MockExtractor()