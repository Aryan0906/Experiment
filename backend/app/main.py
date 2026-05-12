from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine
from .api.endpoints import auth, products

# Create all tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Catalog AI Suite",
    description="Shopify product attribute extraction & anomaly detection",
    version="1.0.0"
)

# Add CORS middleware BEFORE routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Fallback
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "*",  # Allow Vercel deployments
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(products.router, prefix="/products", tags=["Products"])

# Admin router will be added inline
from .api.deps import get_current_admin_user
from .models import User
from sqlalchemy.orm import Session
from fastapi import Depends
import os
import json
from pathlib import Path

TRAINING_DATA_DIR = Path(os.getenv("TRAINING_DATA_DIR", "backend/app/ml/training_data"))

@app.get("/admin/export-feedback")
async def export_feedback(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(products.get_db)
):
    """
    Export all user corrections for model training (admin only).
    
    Returns the contents of corrections.jsonl file.
    """
    corrections_file = TRAINING_DATA_DIR / "corrections.jsonl"
    
    if not corrections_file.exists():
        return {"corrections": [], "message": "No corrections recorded yet"}
    
    try:
        corrections = []
        with open(corrections_file, "r") as f:
            for line in f:
                if line.strip():
                    corrections.append(json.loads(line))
        
        return {"corrections": corrections, "total": len(corrections)}
    except Exception as e:
        return {"error": str(e), "corrections": []}

@app.get("/health")
async def health_check() -> dict[str, str]:
    """Simple health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
