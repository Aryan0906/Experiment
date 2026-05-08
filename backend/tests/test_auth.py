import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.database import SessionLocal, Base, engine
from app.models import Seller, OAuthSession

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

def test_shopify_oauth_authorize(client: TestClient, db_session: Session) -> None:
    """
    Test that authorization endpoint:
    - Accepts shop parameter
    - Generates state token
    - Redirects to Shopify OAuth URL
    """
    shop = "myshop.myshopify.com"
    
    # Act: Request the authorization URL
    response = client.get(f"/auth/shopify/authorize?shop={shop}", follow_redirects=False)

    # Assert: Should redirect to Shopify OAuth URL with 302
    assert response.status_code == 302
    assert "myshopify.com/admin/oauth/authorize" in response.headers["location"]
    assert "state=" in response.headers["location"]
    assert "client_id=" in response.headers["location"]
    
    # Assert: State token should be stored in DB
    oauth_session = db_session.query(OAuthSession).filter_by(shop=shop).first()
    assert oauth_session is not None
    assert oauth_session.state is not None


def test_shopify_oauth_authorize_missing_shop(client: TestClient) -> None:
    """Test that authorization fails gracefully without shop parameter."""
    # Act: Request authorization without shop parameter
    response = client.get("/auth/shopify/authorize", follow_redirects=False)

    # Assert: Should return 400 Bad Request
    assert response.status_code == 400


def test_shopify_oauth_authorize_invalid_shop(client: TestClient) -> None:
    """Test that authorization fails with invalid shop domain."""
    # Act: Request authorization with invalid shop domain
    response = client.get(
        "/auth/shopify/authorize?shop=invalid-domain.com",
        follow_redirects=False
    )

    # Assert: Should return 400 Bad Request
    assert response.status_code == 400


def test_shopify_oauth_callback_success(client: TestClient, db_session: Session) -> None:
    """
    Test successful OAuth callback:
    - Creates seller in DB
    - Stores mock tokens
    - Redirects to dashboard
    """
    shop = "myshop.myshopify.com"
    
    # Setup: Create OAuth session with state token
    from app.models import OAuthSession
    oauth_session = OAuthSession(shop=shop, state="test_state_token")
    db_session.add(oauth_session)
    db_session.commit()

    # Act: Simulate OAuth callback from Shopify
    callback_response = client.get(
        "/auth/shopify/callback",
        params={
            "code": "test_auth_code",
            "shop": shop,
            "state": "test_state_token"
        },
        follow_redirects=False
    )

    # Assert: Should redirect to dashboard with 302
    assert callback_response.status_code == 302
    assert "/dashboard" in callback_response.headers["location"]

    # Assert: Seller should exist in database with tokens
    seller = db_session.query(Seller).filter_by(shop=shop).first()
    assert seller is not None
    assert seller.access_token is not None
    assert seller.refresh_token is not None
    
    # Assert: State token should be deleted (used)
    deleted_session = db_session.query(OAuthSession).filter_by(state="test_state_token").first()
    assert deleted_session is None


def test_shopify_oauth_callback_invalid_state(client: TestClient, db_session: Session) -> None:
    """Test that callback fails with invalid state token (CSRF protection)."""
    # Act: Callback with state that doesn't exist in DB
    response = client.get(
        "/auth/shopify/callback",
        params={
            "code": "test_auth_code",
            "shop": "myshop.myshopify.com",
            "state": "invalid_state_token"
        },
        follow_redirects=False
    )

    # Assert: Should redirect to login with error
    assert response.status_code == 302
    assert "error=invalid_state" in response.headers["location"]


def test_shopify_oauth_callback_shop_mismatch(client: TestClient, db_session: Session) -> None:
    """Test that callback fails when shop doesn't match state token."""
    # Setup: Create OAuth session for different shop
    oauth_session = OAuthSession(shop="othershop.myshopify.com", state="test_state")
    db_session.add(oauth_session)
    db_session.commit()

    # Act: Callback with different shop
    response = client.get(
        "/auth/shopify/callback",
        params={
            "code": "test_auth_code",
            "shop": "myshop.myshopify.com",
            "state": "test_state"
        },
        follow_redirects=False
    )

    # Assert: Should redirect to login with error
    assert response.status_code == 302
    assert "error=shop_mismatch" in response.headers["location"]


def test_shopify_oauth_callback_missing_params(client: TestClient) -> None:
    """Test that callback fails gracefully with missing parameters."""
    # Act: Callback without required parameters
    response = client.get(
        "/auth/shopify/callback",
        follow_redirects=False
    )

    # Assert: Should redirect to login with error
    assert response.status_code == 302
    assert "error=missing_params" in response.headers["location"]

