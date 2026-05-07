from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse
from app.database import get_db
from app.models import Seller
from app.config import settings
import httpx

router = APIRouter()

@router.get("/authorize")
async def authorize_shopify(shop: str = "myshop.myshopify.com") -> RedirectResponse:
    """
    Redirects the user to the Shopify OAuth consent screen.
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
    """
    client_id = settings.shopify_api_key
    client_secret = settings.shopify_api_secret

    token_url = f"https://{shop}/admin/oauth/access_token"
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, json=payload)
        
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Failed to exchange token with Shopify: {response.text}")
            
        data = response.json()
        access_token = data.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="Shopify response did not contain an access_token")
            
        refresh_token = data.get("refresh_token", "")

    # Check if seller exists, otherwise create
    seller = db.query(Seller).filter_by(shop=shop).first()
    if not seller:
        seller = Seller(shop=shop)
        db.add(seller)

    # Update tokens
    seller.access_token = access_token
    seller.refresh_token = refresh_token
    db.commit()

    # Redirect to the frontend dashboard (Vite is running on 5173)
    # Adding the shop parameter so the frontend knows who logged in
    return RedirectResponse(url=f"http://localhost:5173/dashboard?shop={shop}")
