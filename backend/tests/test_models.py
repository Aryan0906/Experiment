import pytest
from typing import Generator
from app.database import SessionLocal, Base, engine
from app.models import Seller, Product, ExtractionJob, ExtractedAttribute
from sqlalchemy.orm import Session

@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Create a fresh DB session for each test."""
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

def test_seller_model(db_session: Session) -> None:
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

def test_product_model(db_session: Session) -> None:
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
    assert queried is not None
    assert queried.title == "Test Product"
    assert queried.seller_id == seller.id

def test_extraction_job_model(db_session: Session) -> None:
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
    assert queried is not None
    assert queried.status == "pending"
    assert queried.seller_id == seller.id

def test_extracted_attribute_model(db_session: Session) -> None:
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
    assert queried is not None
    assert queried.attributes["brand"] == "Nike"  # type: ignore
    assert queried.confidence == 0.92

def test_db_models() -> None:
    """Test that all models are created and queryable."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

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

    db.delete(queried_seller)
    db.commit()
    db.close()

def test_fastapi_app_starts() -> None:
    """Test that FastAPI app initializes without errors."""
    from app.main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
