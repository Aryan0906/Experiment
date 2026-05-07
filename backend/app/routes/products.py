from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Seller, Product
import httpx
import csv
import io

router = APIRouter()

@router.get("")
async def get_products(seller_id: int, db: Session = Depends(get_db)):
    """
    Returns products for the dashboard.
    Attempts to sync from Shopify first; falls back to locally-cached products
    if the Shopify API is unreachable or the token is invalid.
    """
    seller = db.query(Seller).filter_by(id=seller_id).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found. Please connect your store first.")

    synced_from_shopify = False

    # Only attempt Shopify sync if we have a token
    if seller.access_token and seller.shop:
        shopify_api_url = f"https://{seller.shop}/admin/api/2024-04/products.json"
        headers = {
            "X-Shopify-Access-Token": seller.access_token,
            "Content-Type": "application/json"
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(shopify_api_url, headers=headers, params={"limit": 50})

                if response.status_code == 200:
                    data = response.json()
                    shopify_products = data.get("products", [])

                    for sp in shopify_products:
                        prod_id = str(sp.get("id"))
                        title = sp.get("title", "")
                        description = sp.get("body_html", "")

                        images = sp.get("images", [])
                        image_url = images[0].get("src", "") if images else ""

                        variants = sp.get("variants", [])
                        price = variants[0].get("price", "0.00") if variants else "0.00"
                        sku = variants[0].get("sku", "") if variants else ""

                        local_product = db.query(Product).filter_by(id=prod_id).first()
                        if not local_product:
                            local_product = Product(
                                id=prod_id,
                                seller_id=seller.id,
                                title=title,
                                description=description,
                                image_url=image_url,
                                price=price,
                                sku=sku
                            )
                            db.add(local_product)
                        else:
                            local_product.title = title
                            local_product.description = description
                            local_product.image_url = image_url
                            local_product.price = price
                            local_product.sku = sku

                    db.commit()
                    synced_from_shopify = True
        except Exception:
            # Shopify unreachable or error – fall back to local data
            pass

    # Always return whatever we have in the local DB
    local_products = db.query(Product).filter_by(seller_id=seller.id).all()

    return {
        "synced": synced_from_shopify,
        "products": [
            {
                "id": p.id,
                "title": p.title,
                "description": p.description,
                "image_url": p.image_url,
                "price": p.price,
                "sku": p.sku
            }
            for p in local_products
        ]
    }

@router.get("/csv")
async def download_csv(seller_id: int, db: Session = Depends(get_db)):
    """
    Returns products + extracted attributes for the seller as a CSV download.
    Includes: product_id, title, brand, color, size, material, category, price, sku, confidence
    """
    from app.models import ExtractedAttribute as EA

    seller = db.query(Seller).filter_by(id=seller_id).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found.")

    products = db.query(Product).filter_by(seller_id=seller.id).all()

    # Build a map of product_id → latest extraction
    attr_map = {}
    for p in products:
        attr = (
            db.query(EA)
            .filter_by(product_id=p.id)
            .order_by(EA.created_at.desc())
            .first()
        )
        if attr:
            attr_map[p.id] = attr

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "product_id", "title", "sku", "price",
        "brand", "color", "size", "material", "category", "confidence"
    ])

    for p in products:
        attr = attr_map.get(p.id)
        attrs = attr.attributes if attr else {}
        writer.writerow([
            p.id,
            p.title,
            p.sku,
            p.price,
            attrs.get("brand", ""),
            attrs.get("color", ""),
            attrs.get("size", ""),
            attrs.get("material", ""),
            attrs.get("category", ""),
            f"{attr.confidence:.2f}" if attr else "",
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=catalog_{seller_id}.csv"},
    )

