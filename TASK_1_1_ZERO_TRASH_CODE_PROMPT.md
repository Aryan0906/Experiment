# ZERO-TRASH-CODE EXECUTION PROMPT #1
## Task 1.1: Backend Setup (FastAPI + SQLAlchemy + PostgreSQL)

---

## 🔒 FEATURE SCOPE LOCK

**Feature Name:** Backend Infrastructure (FastAPI app, DB models, migrations)

**What's In Scope:**
- FastAPI app initialization (`main.py`)
- SQLAlchemy models: `Seller`, `Product`, `ExtractedAttribute`, `ExtractionJob`
- PostgreSQL connection via `.env`
- Alembic migrations setup
- Database initialization script

**What's NOT In Scope:**
- OAuth routes (done in Task 1.2)
- Shopify API client (done in Task 1.3)
- VLM inference (done in Task 2.1)
- Any business logic beyond models

---

## 🧪 TEST-FIRST CONTRACT

**GIVEN:** A FastAPI app with SQLAlchemy ORM  
**WHEN:** I connect to PostgreSQL and create tables  
**THEN:** I can query Seller, Product, ExtractedAttribute, ExtractionJob models  
**AND:** All tables exist in the database

```python
def test_db_models():
    """Test that all models are created and queryable."""
    # Arrange
    from app.database import SessionLocal, Base, engine
    from app.models import Seller, Product, ExtractedAttribute, ExtractionJob
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Act
    db = SessionLocal()
    
    # Assert: Can create and query a Seller
    test_seller = Seller(
        shop="test.myshopify.com",
        access_token="encrypted_token",
        refresh_token="encrypted_token"
    )
    db.add(test_seller)
    db.commit()
    
    queried_seller = db.query(Seller).filter_by(shop="test.myshopify.com").first()
    assert queried_seller is not None
    assert queried_seller.shop == "test.myshopify.com"
    
    # Clean up
    db.delete(queried_seller)
    db.commit()
    db.close()

def test_fastapi_app_starts():
    """Test that FastAPI app initializes without errors."""
    from app.main import app
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
```

---

## 💻 BUG-FREE CODE RULES (For This Task)

1. **No hardcoded database URLs** → Use `.env` and `os.getenv()`
2. **No unused imports** → Every import must be used
3. **No commented-out code** → Delete or create a ticket
4. **Type hints everywhere** → `seller: Seller`, `db: Session`, etc.
5. **Error handling** → DB connection failures logged, not silently failing
6. **No magic strings** → `"postgres://..."` goes to `.env`

---

## 📋 DELIVERABLES (For This Task)

### File 1: `backend/app/main.py`
```python
from fastapi import FastAPI
from app.database import Base, engine
from app.config import settings

# Create all tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Catalog Sync",
    description="Shopify catalog automation tool",
    version="0.1.0"
)

@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### File 2: `backend/app/config.py`
```python
from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    database_url: str = os.getenv("DATABASE_URL", "postgresql://localhost/catalog_sync")
    shopify_api_key: str = os.getenv("SHOPIFY_API_KEY", "")
    shopify_api_secret: str = os.getenv("SHOPIFY_API_SECRET", "")
    shopify_redirect_uri: str = os.getenv("SHOPIFY_REDIRECT_URI", "http://localhost:3000/auth/callback")
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### File 3: `backend/app/database.py`
```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency for FastAPI to inject database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### File 4: `backend/app/models.py`
```python
from sqlalchemy import Column, Integer, String, DateTime, Float, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class Seller(Base):
    __tablename__ = "sellers"
    
    id = Column(Integer, primary_key=True, index=True)
    shop = Column(String, unique=True, index=True)  # e.g., "myshop.myshopify.com"
    access_token = Column(String)  # Store encrypted in production
    refresh_token = Column(String)  # Store encrypted in production
    created_at = Column(DateTime, default=datetime.utcnow)
    
    products = relationship("Product", back_populates="seller")
    jobs = relationship("ExtractionJob", back_populates="seller")

class Product(Base):
    __tablename__ = "products"
    
    id = Column(String, primary_key=True)  # Shopify product ID
    seller_id = Column(Integer, ForeignKey("sellers.id"), index=True)
    title = Column(String, index=True)
    description = Column(String)
    image_url = Column(String)
    price = Column(String)
    sku = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    seller = relationship("Seller", back_populates="products")
    extracted_attributes = relationship("ExtractedAttribute", back_populates="product")

class ExtractionJob(Base):
    __tablename__ = "extraction_jobs"
    
    id = Column(String, primary_key=True)  # UUID
    seller_id = Column(Integer, ForeignKey("sellers.id"), index=True)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    progress = Column(Integer, default=0)  # 0-100
    created_at = Column(DateTime, default=datetime.utcnow)
    
    seller = relationship("Seller", back_populates="jobs")
    extracted_attributes = relationship("ExtractedAttribute", back_populates="job")

class ExtractedAttribute(Base):
    __tablename__ = "extracted_attributes"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String, ForeignKey("products.id"), index=True)
    job_id = Column(String, ForeignKey("extraction_jobs.id"), index=True)
    attributes = Column(JSON)  # {"brand": "Nike", "size": "M", ...}
    confidence = Column(Float)  # 0.0 - 1.0
    created_at = Column(DateTime, default=datetime.utcnow)
    
    product = relationship("Product", back_populates="extracted_attributes")
    job = relationship("ExtractionJob", back_populates="extracted_attributes")
```

### File 5: `backend/requirements.txt`
```
fastapi==0.104.1
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.12.1
python-dotenv==1.0.0
pydantic-settings==2.1.0
pytest==7.4.3
httpx==0.25.1
uvicorn==0.24.0
```

### File 6: `backend/.env.example`
```
DATABASE_URL=postgresql://user:password@localhost:5432/catalog_sync
SHOPIFY_API_KEY=your_api_key_here
SHOPIFY_API_SECRET=your_api_secret_here
SHOPIFY_REDIRECT_URI=http://localhost:3000/auth/callback
```

### File 7: `backend/pytest.ini`
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

### File 8: `backend/tests/test_models.py`
```python
import pytest
from app.database import SessionLocal, Base, engine
from app.models import Seller, Product, ExtractionJob, ExtractedAttribute

@pytest.fixture
def db_session():
    """Create a fresh DB session for each test."""
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

def test_seller_model(db_session):
    """Test Seller model creation and retrieval."""
    seller = Seller(
        shop="test.myshopify.com",
        access_token="token123",
        refresh_token="refresh123"
    )
    db_session.add(seller)
    db_session.commit()
    
    queried = db_session.query(Seller).filter_by(shop="test.myshopify.com").first()
    assert queried is not None
    assert queried.shop == "test.myshopify.com"

def test_product_model(db_session):
    """Test Product model with seller relationship."""
    seller = Seller(
        shop="test.myshopify.com",
        access_token="token123",
        refresh_token="refresh123"
    )
    db_session.add(seller)
    db_session.commit()
    
    product = Product(
        id="prod_123",
        seller_id=seller.id,
        title="Test Product",
        description="A test product",
        image_url="https://example.com/image.jpg",
        price="₹500",
        sku="SKU-123"
    )
    db_session.add(product)
    db_session.commit()
    
    queried = db_session.query(Product).filter_by(id="prod_123").first()
    assert queried.title == "Test Product"
    assert queried.seller_id == seller.id

def test_extraction_job_model(db_session):
    """Test ExtractionJob model."""
    seller = Seller(
        shop="test.myshopify.com",
        access_token="token123",
        refresh_token="refresh123"
    )
    db_session.add(seller)
    db_session.commit()
    
    job = ExtractionJob(
        id="job_123",
        seller_id=seller.id,
        status="pending"
    )
    db_session.add(job)
    db_session.commit()
    
    queried = db_session.query(ExtractionJob).filter_by(id="job_123").first()
    assert queried.status == "pending"
    assert queried.seller_id == seller.id

def test_extracted_attribute_model(db_session):
    """Test ExtractedAttribute model."""
    seller = Seller(
        shop="test.myshopify.com",
        access_token="token123",
        refresh_token="refresh123"
    )
    db_session.add(seller)
    db_session.commit()
    
    product = Product(
        id="prod_123",
        seller_id=seller.id,
        title="Test Product",
        description="A test product",
        image_url="https://example.com/image.jpg",
        price="₹500",
        sku="SKU-123"
    )
    db_session.add(product)
    db_session.commit()
    
    job = ExtractionJob(id="job_123", seller_id=seller.id)
    db_session.add(job)
    db_session.commit()
    
    attr = ExtractedAttribute(
        product_id="prod_123",
        job_id="job_123",
        attributes={"brand": "Nike", "color": "Blue"},
        confidence=0.92
    )
    db_session.add(attr)
    db_session.commit()
    
    queried = db_session.query(ExtractedAttribute).first()
    assert queried.attributes["brand"] == "Nike"
    assert queried.confidence == 0.92
```

---

## 🗑️ TRASH DETECTOR CHECKLIST

- [ ] No commented-out code in any file
- [ ] No unused imports (e.g., don't import `List` if not used)
- [ ] No hardcoded database URLs (all in `.env`)
- [ ] No magic strings (e.g., "postgresql://..." → DATABASE_URL)
- [ ] All type hints present (no `any`)
- [ ] No `print()` statements (use logging instead)
- [ ] No TODOs without tickets

---

## ✅ TEST RUNNER

**Run these commands to verify everything works:**

```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Copy .env.example to .env and fill in PostgreSQL URL
cp .env.example .env
# Edit .env with your DATABASE_URL

# Run tests
pytest tests/test_models.py -v

# Expected output:
# test_seller_model PASSED
# test_product_model PASSED
# test_extraction_job_model PASSED
# test_extracted_attribute_model PASSED

# Type check
mypy app/ --strict  # Should pass with no errors

# Lint
flake8 app/ --max-line-length=100  # Should pass with no warnings
```

---

## 🎯 SUCCESS CRITERIA

- [ ] `pytest tests/test_models.py` passes (all 4 tests green)
- [ ] `mypy app/ --strict` passes (no type errors)
- [ ] `flake8 app/` passes (no style warnings)
- [ ] Can start FastAPI app: `python -m app.main` (no errors)
- [ ] Health check works: `curl http://localhost:8000/health` → `{"status": "healthy"}`
- [ ] PostgreSQL connection string works (no DB errors in logs)
- [ ] All files have docstrings (class-level at minimum)

---

## 🚀 NEXT STEP

Once Task 1.1 is done (test passes, app starts, DB connects):
→ Move to **Task 1.2: Shopify OAuth** (see SPRINT_1_BREAKDOWN.md)

