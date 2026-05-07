from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse
from app.database import get_db
from app.models import Seller
from app.config import settings

router = APIRouter()

@router.get("/authorize")
async def authorize_shopify(shop: str = "myshop.myshopify.com") -> RedirectResponse:
    """
    Redirects the user to the Shopify OAuth consent screen.
    Since this is Sprint 1 (Mock implementation), we redirect to a mock consent URL.
    """
    redirect_uri = settings.shopify_redirect_uri
    client_id = settings.shopify_api_key

    # Standard Shopify OAuth URL format
    auth_url = (
        f"https://{shop}/admin/oauth/authorize?"
        f"client_id={client_id}&scope=read_products&redirect_uri={redirect_uri}"
    )

    return RedirectResponse(url=auth_url)

@router.get("/callback")
async def shopify_callback(code: str, shop: str, db: Session = Depends(get_db)) -> RedirectResponse:
    """
    Handles the OAuth callback from Shopify, exchanges the code for tokens,
    and stores the seller in the database.
    In Sprint 1, this mocks the token exchange.
    """
    # Mock token exchange
    mock_access_token = f"mock_access_{code}"
    mock_refresh_token = f"mock_refresh_{code}"

    # Check if seller exists, otherwise create
    seller = db.query(Seller).filter_by(shop=shop).first()
    if not seller:
        seller = Seller(shop=shop)
        db.add(seller)

    # Update tokens
    seller.access_token = mock_access_token
    seller.refresh_token = mock_refresh_token
    db.commit()

    # Redirect to the frontend dashboard (Vite is running on 5173)
    return RedirectResponse(url="http://localhost:5173/dashboard")
