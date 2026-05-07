import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.database import SessionLocal, Base, engine
from app.models import Seller, Product
from unittest.mock import patch, MagicMock

@pytest.fixture(autouse=True)
def db_session() -> Generator[Session, None, None]:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client

@patch("app.routes.products.httpx.AsyncClient.get")
def test_fetch_shopify_products(mock_get: MagicMock, client: TestClient, db_session: Session) -> None:
    # Given: Seller with OAuth token
    seller = Seller(shop="myshop.myshopify.com", access_token="fake_token")
    db_session.add(seller)
    db_session.commit()

    # Mock the Shopify API response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "products": [
            {
                "id": 12345,
                "title": "Blue T-Shirt",
                "body_html": "A nice blue shirt",
                "images": [{"src": "http://example.com/blue.jpg"}],
                "variants": [{"price": "19.99", "sku": "BLU-TS-M"}]
            }
        ]
    }
    mock_get.return_value = mock_response

    # When: GET /api/products
    response = client.get("/api/products/?shop=myshop.myshopify.com")

    # Then: Response contains list of products
    assert response.status_code == 200
    data = response.json()
    products = data.get("products", [])
    assert len(products) == 1
    
    # And: Each product has correct attributes
    assert products[0]["id"] == "12345"
    assert products[0]["title"] == "Blue T-Shirt"
    assert products[0]["image_url"] == "http://example.com/blue.jpg"
    assert products[0]["price"] == "19.99"
    assert products[0]["sku"] == "BLU-TS-M"

    # And: It should be saved to the database
    local_product = db_session.query(Product).filter_by(id="12345").first()
    assert local_product is not None
    assert local_product.title == "Blue T-Shirt"
