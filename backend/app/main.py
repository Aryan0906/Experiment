from fastapi import FastAPI
from app.database import Base, engine
from app.routes import auth

# Create all tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Catalog Sync",
    description="Shopify catalog automation tool",
    version="0.1.0"
)

app.include_router(auth.router, prefix="/auth/shopify", tags=["auth"])

@app.get("/health")
async def health_check() -> dict[str, str]:
    """Simple health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
