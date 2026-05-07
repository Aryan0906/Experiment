from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app.routes import auth, products, extract

# Create all tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Catalog Sync",
    description="Shopify catalog automation tool",
    version="0.1.0",
    redirect_slashes=False,
)

# CORS – allow the Vite frontend to call the backend directly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth/shopify", tags=["auth"])
app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(extract.router, prefix="/api", tags=["extract"])

@app.get("/health")
async def health_check() -> dict[str, str]:
    """Simple health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
