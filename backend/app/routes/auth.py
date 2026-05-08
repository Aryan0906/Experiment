import secrets
import base64
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse
from urllib.parse import urlencode

from app.database import get_db
from app.models import Seller, OAuthSession
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Shopify OAuth scopes needed for the app
SHOPIFY_SCOPES = [
    "read_products",
    "write_products",
    "read_inventory",
    "write_inventory",
]


@router.get("/authorize")
async def authorize_shopify(
    shop: str = None,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    """
    Redirect user to Shopify OAuth consent screen.
    
    Generates a secure state token, stores it in DB, and redirects to Shopify.
    This prevents CSRF attacks during OAuth flow.
    
    Args:
        shop: Shopify store domain (e.g., "myshop.myshopify.com")
        db: Database session
    
    Returns:
        RedirectResponse to Shopify OAuth URL
    """
    # Validate shop parameter
    if not shop or not shop.strip():
        logger.warning("authorize_shopify called without shop parameter")
        raise HTTPException(status_code=400, detail="shop parameter is required")
    
    shop = shop.strip()
    
    # Ensure shop has correct format
    if not shop.endswith(".myshopify.com"):
        logger.warning(f"Invalid shop domain format: {shop}")
        raise HTTPException(
            status_code=400,
            detail="Invalid shop domain. Must end with .myshopify.com"
        )
    
    try:
        # Generate secure random state token
        state_bytes = secrets.token_bytes(32)
        state = base64.urlsafe_b64encode(state_bytes).decode().rstrip("=")
        
        # Store state in DB for verification during callback
        oauth_session = OAuthSession(shop=shop, state=state)
        db.add(oauth_session)
        db.commit()
        
        logger.info(f"OAuth session created for shop: {shop}")
        
        # Build Shopify OAuth URL
        client_id = settings.shopify_api_key
        redirect_uri = settings.shopify_redirect_uri
        scope = ",".join(SHOPIFY_SCOPES)
        
        auth_params = {
            "client_id": client_id,
            "scope": scope,
            "redirect_uri": redirect_uri,
            "state": state,
        }
        
        auth_url = f"https://{shop}/admin/oauth/authorize?{urlencode(auth_params)}"
        
        logger.info(f"Redirecting to Shopify: {auth_url[:80]}...")
        return RedirectResponse(url=auth_url, status_code=302)
    
    except Exception as e:
        logger.error(f"Error in authorize_shopify: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="OAuth authorization failed")


@router.get("/callback")
async def shopify_callback(
    code: str = None,
    shop: str = None,
    state: str = None,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    """
    Handle OAuth callback from Shopify.
    
    Verifies state token, exchanges code for access token, and stores seller.
    In Sprint 1, this uses mock tokens for testing.
    
    Args:
        code: Authorization code from Shopify
        shop: Shop domain
        state: State token (must match what we stored)
        db: Database session
    
    Returns:
        RedirectResponse to frontend dashboard
    """
    # Validate required parameters
    if not code or not shop or not state:
        logger.warning(
            f"callback missing params: code={bool(code)}, shop={bool(shop)}, state={bool(state)}"
        )
        return RedirectResponse(
            url="http://localhost:5173/login?error=missing_params",
            status_code=302
        )
    
    try:
        # Verify state token (CSRF protection)
        oauth_session = db.query(OAuthSession).filter_by(state=state).first()
        if not oauth_session:
            logger.warning(f"Invalid state token: {state}")
            return RedirectResponse(
                url="http://localhost:5173/login?error=invalid_state",
                status_code=302
            )
        
        # Verify shop matches
        if oauth_session.shop != shop:
            logger.warning(f"Shop mismatch: expected {oauth_session.shop}, got {shop}")
            return RedirectResponse(
                url="http://localhost:5173/login?error=shop_mismatch",
                status_code=302
            )
        
        # Delete used state token
        db.delete(oauth_session)
        db.commit()
        
        logger.info(f"OAuth callback verified for shop: {shop}")
        
        # SPRINT 1: Mock token exchange
        # In production, you'd call Shopify API to exchange code for token
        mock_access_token = f"mock_access_{code[:20]}"
        mock_refresh_token = f"mock_refresh_{code[:20]}"
        
        # Create or update seller
        seller = db.query(Seller).filter_by(shop=shop).first()
        if not seller:
            seller = Seller(
                shop=shop,
                access_token=mock_access_token,
                refresh_token=mock_refresh_token,
            )
            db.add(seller)
            logger.info(f"Created new seller: {shop}")
        else:
            seller.access_token = mock_access_token
            seller.refresh_token = mock_refresh_token
            logger.info(f"Updated existing seller: {shop}")
        
        db.commit()
        
        # Redirect to frontend dashboard
        return RedirectResponse(
            url=f"http://localhost:5173/dashboard?shop={shop}",
            status_code=302
        )
    
    except Exception as e:
        logger.error(f"Error in shopify_callback: {str(e)}", exc_info=True)
        return RedirectResponse(
            url="http://localhost:5173/login?error=callback_failed",
            status_code=302
        )

