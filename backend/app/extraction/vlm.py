"""
VLM-based attribute extraction backends.

Supports two backends:
- MockExtractor: Returns realistic mock attributes (free, instant)
- GPT4VisionExtractor: Uses OpenAI GPT-4o Vision for real extraction

Switch via EXTRACTION_BACKEND env var ("mock" or "gpt4v").
"""
import json
import random
from abc import ABC, abstractmethod
from typing import Dict, Any


class AttributeExtractor(ABC):
    """Base class for attribute extractors."""

    @abstractmethod
    async def extract(self, image_url: str, description: str, title: str) -> Dict[str, Any]:
        """
        Extract product attributes from an image and description.

        Returns a dict with keys: brand, size, color, material, category, confidence
        """
        ...


class MockExtractor(AttributeExtractor):
    """
    Returns realistic mock attributes based on product title/description.
    Used for testing and demos without API costs.
    """

    # Lookup tables for realistic mock data
    BRANDS = ["Nike", "Adidas", "Puma", "H&M", "Zara", "FabIndia", "W", "Biba", "Levi's", "Allen Solly"]
    SIZES = ["XS", "S", "M", "L", "XL", "XXL", "Free Size", "28", "30", "32", "34"]
    COLORS = ["Blue", "Red", "Black", "White", "Green", "Brown", "Navy", "Grey", "Pink", "Beige"]
    MATERIALS = ["Cotton", "Polyester", "Silk", "Denim", "Leather", "Linen", "Wool", "Nylon", "Sterling Silver"]
    CATEGORIES = [
        "T-Shirt", "Kurta", "Jeans", "Bag", "Shoes", "Jewelry",
        "Saree", "Shirt", "Dress", "Jacket", "Accessories"
    ]

    def _detect_from_text(self, text: str, options: list[str]) -> str:
        """Try to detect a value from text, falling back to random."""
        text_lower = text.lower()
        for option in options:
            if option.lower() in text_lower:
                return option
        return random.choice(options)

    async def extract(self, image_url: str, description: str, title: str) -> Dict[str, Any]:
        combined = f"{title} {description}"

        return {
            "brand": self._detect_from_text(combined, self.BRANDS),
            "size": self._detect_from_text(combined, self.SIZES),
            "color": self._detect_from_text(combined, self.COLORS),
            "material": self._detect_from_text(combined, self.MATERIALS),
            "category": self._detect_from_text(combined, self.CATEGORIES),
            "confidence": round(random.uniform(0.72, 0.98), 2),
        }


class GPT4VisionExtractor(AttributeExtractor):
    """
    Uses OpenAI GPT-4o Vision to extract product attributes from images.
    Requires OPENAI_API_KEY environment variable.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def extract(self, image_url: str, description: str, title: str) -> Dict[str, Any]:
        try:
            import httpx
        except ImportError:
            raise RuntimeError("httpx is required for GPT4VisionExtractor")

        prompt = (
            "You are a product attribute extractor. Analyze this product image and description, "
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
                    "model": "gpt-4o",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {"url": image_url, "detail": "low"},
                                },
                            ],
                        }
                    ],
                    "max_tokens": 300,
                },
            )

            if response.status_code != 200:
                # Fallback to mock if API fails
                fallback = MockExtractor()
                return await fallback.extract(image_url, description, title)

            data = response.json()
            content = data["choices"][0]["message"]["content"]

            # Parse JSON from response (handle markdown code blocks)
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1]
                content = content.rsplit("```", 1)[0]

            attrs = json.loads(content)

            # Ensure all required fields exist
            required = ["brand", "size", "color", "material", "category", "confidence"]
            for field in required:
                if field not in attrs:
                    attrs[field] = "" if field != "confidence" else 0.5

            return attrs


def get_extractor(backend: str = "mock", api_key: str = "") -> AttributeExtractor:
    """Factory function to get the configured extractor."""
    if backend == "gpt4v" and api_key:
        return GPT4VisionExtractor(api_key=api_key)
    return MockExtractor()
