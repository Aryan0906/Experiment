from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine
from .routes import auth, products, extract

# Create all tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Catalog Sync",
    description="Shopify catalog automation tool",
    version="0.1.0"
)

# Add CORS middleware BEFORE routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Fallback
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(auth.router, prefix="/auth/shopify", tags=["auth"])
app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(extract.router, prefix="/api", tags=["extraction"])

@app.get("/health")
async def health_check() -> dict[str, str]:
    """Simple health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
