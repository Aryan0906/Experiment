import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.database import SessionLocal, Base, engine
from app.models import Seller

@pytest.fixture(autouse=True)
def db_session() -> Generator[Session, None, None]:
    """Create a fresh DB session for each test."""
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client

from unittest.mock import patch, MagicMock

@patch("app.routes.auth.httpx.AsyncClient.post")
def test_shopify_oauth_flow(mock_post: MagicMock, client: TestClient, db_session: Session) -> None:
    """
    GIVEN: User at login page
    WHEN: User clicks 'Connect Shopify'
    THEN: Redirected to Shopify OAuth consent screen
    AND: After consent, seller_id + refresh_token stored in DB (encrypted)
    AND: User returned to dashboard with 'Connected: myshop.myshopify.com'
    """
    # Act: Request the authorization URL
    response = client.get("/auth/shopify/authorize", follow_redirects=False)

    # Assert: Should redirect to the Shopify OAuth URL
    assert response.status_code == 307
    assert "myshopify.com" in response.headers["location"]

    # Mock the Shopify Token Exchange response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": "mock_access_token_123",
        "refresh_token": "mock_refresh_token_123"
    }
    mock_post.return_value = mock_response

    # Act: Simulate the OAuth callback from Shopify
    callback_response = client.get(
        "/auth/shopify/callback",
        params={"code": "test_auth_code", "shop": "myshop.myshopify.com"},
        follow_redirects=False
    )

    # Assert: Should process and then redirect to the frontend dashboard
    assert callback_response.status_code == 307
    assert "/dashboard" in callback_response.headers["location"]

    # Assert: The seller should now exist in the database with mock tokens
    seller = db_session.query(Seller).filter_by(shop="myshop.myshopify.com").first()
    assert seller is not None
    assert seller.access_token is not None
    assert seller.refresh_token is not None
