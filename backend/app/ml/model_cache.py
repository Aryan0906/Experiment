"""
Model caching for ML models to avoid reloading on every request.
Implements thread-safe singleton pattern for Qwen2-VL and CC-VAE models.
"""
import threading
from typing import Optional, Any


class ModelCache:
    """
    Singleton cache for ML models.
    
    Loads models once and reuses them across requests to avoid
    expensive model loading overhead. Thread-safe implementation.
    """
    
    _instance: Optional["ModelCache"] = None
    _lock = threading.Lock()
    
    def __init__(self):
        self._qwen_model: Any = None
        self._ccvae_model: Any = None
        self._qwen_processor: Any = None
        self._models_loaded = False
        self._load_lock = threading.Lock()
    
    @classmethod
    def get_instance(cls) -> "ModelCache":
        """Get or create the singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def get_qwen_model(self) -> tuple[Any, Any]:
        """
        Get the Qwen2-VL model and processor.
        
        Returns:
            Tuple of (model, processor)
        """
        if not self._models_loaded:
            self._load_models()
        return self._qwen_model, self._qwen_processor
    
    def get_ccvae_model(self) -> Any:
        """
        Get the CC-VAE anomaly detection model.
        
        Returns:
            The CC-VAE model
        """
        if not self._models_loaded:
            self._load_models()
        return self._ccvae_model
    
    def _load_models(self) -> None:
        """Load all models in a thread-safe manner."""
        with self._load_lock:
            if self._models_loaded:
                return
            
            print("[ModelCache] Loading ML models...")
            
            try:
                # Load Qwen2-VL model
                import torch
                from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
                
                model_id = "Qwen/Qwen2-VL-2B-Instruct"
                print(f"[ModelCache] Loading Qwen2-VL from {model_id}...")
                
                self._qwen_model = Qwen2VLForConditionalGeneration.from_pretrained(
                    model_id,
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                    device_map="auto" if torch.cuda.is_available() else None,
                    trust_remote_code=True
                )
                
                self._qwen_processor = AutoProcessor.from_pretrained(
                    model_id,
                    trust_remote_code=True
                )
                
                print("[ModelCache] Qwen2-VL loaded successfully")
                
                # Load CC-VAE model (anomaly detection)
                # For now, we'll use a simple mock - replace with actual model loading
                print("[ModelCache] Loading CC-VAE anomaly detection model...")
                self._ccvae_model = self._load_ccvae_model()
                print("[ModelCache] CC-VAE loaded successfully")
                
                self._models_loaded = True
                print("[ModelCache] All models loaded!")
                
            except Exception as e:
                print(f"[ModelCache] Error loading models: {e}")
                raise
    
    def _load_ccvae_model(self) -> Any:
        """
        Load the CC-VAE anomaly detection model.
        
        In production, this would load the actual trained model.
        For now, returns a placeholder that can be replaced.
        """
        # Placeholder - replace with actual model loading logic
        # Example: 
        # from app.ml.ccvae import CCVAEModel
        # return CCVAEModel.load_from_checkpoint("path/to/checkpoint")
        
        class MockCCVAE:
            """Mock CC-VAE for development/testing."""
            
            def detect_anomalies(self, image_path: str) -> dict:
                """
                Detect anomalies in an image.
                
                Returns dict with:
                - is_blurry: bool
                - blur_score: float (0-1, higher = more blurry)
                - is_wrong_background: bool
                - background_score: float (0-1, higher = wrong background)
                - is_counterfeit: bool
                - counterfeit_score: float (0-1, higher = likely counterfeit)
                - anomaly_score: float (overall anomaly score 0-1)
                """
                import random
                # Mock results - replace with actual model inference
                blur_score = random.uniform(0.0, 0.3)  # Most images not blurry
                bg_score = random.uniform(0.0, 0.2)  # Most have correct background
                cf_score = random.uniform(0.0, 0.15)  # Most are genuine
                
                return {
                    "is_blurry": blur_score > 0.7,
                    "blur_score": round(blur_score, 3),
                    "is_wrong_background": bg_score > 0.8,
                    "background_score": round(bg_score, 3),
                    "is_counterfeit": cf_score > 0.85,
                    "counterfeit_score": round(cf_score, 3),
                    "anomaly_score": round(max(blur_score, bg_score, cf_score), 3),
                }
        
        return MockCCVAE()


# Global convenience functions
def get_qwen_model() -> tuple[Any, Any]:
    """Get Qwen2-VL model and processor from cache."""
    cache = ModelCache.get_instance()
    return cache.get_qwen_model()


def get_ccvae_model() -> Any:
    """Get CC-VAE model from cache."""
    cache = ModelCache.get_instance()
    return cache.get_ccvae_model()
