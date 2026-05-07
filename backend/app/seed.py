"""
Seed script to populate the local database with sample products for testing.
Run with: python -m app.seed
"""
from app.database import SessionLocal, Base, engine
from app.models import Seller, Product
from datetime import datetime, timezone


SAMPLE_PRODUCTS = [
    {
        "id": "seed_001",
        "title": "Classic Blue Cotton T-Shirt",
        "description": "Premium 100% cotton crew-neck t-shirt in navy blue. Comfortable fit, pre-shrunk fabric. Available in sizes S-XXL.",
        "image_url": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400",
        "price": "799.00",
        "sku": "TEE-BLU-001",
    },
    {
        "id": "seed_002",
        "title": "Women's Red Kurta with Embroidery",
        "description": "Elegant hand-embroidered kurta in deep red cotton silk. Traditional Indian design with mirror work and zari border.",
        "image_url": "https://images.unsplash.com/photo-1610030469983-98e550d6193c?w=400",
        "price": "2499.00",
        "sku": "KRT-RED-002",
    },
    {
        "id": "seed_003",
        "title": "Men's Slim Fit Denim Jeans",
        "description": "Dark wash slim fit jeans with stretch. 98% cotton, 2% elastane. Five-pocket design, zip fly.",
        "image_url": "https://images.unsplash.com/photo-1542272604-787c3835535d?w=400",
        "price": "1899.00",
        "sku": "JNS-DRK-003",
    },
    {
        "id": "seed_004",
        "title": "Leather Crossbody Bag - Brown",
        "description": "Genuine leather crossbody bag with adjustable strap. Interior zip pocket, magnetic closure. Dimensions: 25x18x8 cm.",
        "image_url": "https://images.unsplash.com/photo-1548036328-c9fa89d128fa?w=400",
        "price": "3499.00",
        "sku": "BAG-BRN-004",
    },
    {
        "id": "seed_005",
        "title": "Running Shoes - Black/White",
        "description": "Lightweight mesh upper running shoes with EVA midsole. Rubber outsole for grip. Breathable and cushioned.",
        "image_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400",
        "price": "4999.00",
        "sku": "SHO-BLK-005",
    },
    {
        "id": "seed_006",
        "title": "Silver Pendant Necklace",
        "description": "925 sterling silver pendant with cubic zirconia stones. Chain length: 18 inches. Lobster clasp closure.",
        "image_url": "https://images.unsplash.com/photo-1599643478518-a5f3899e7b2e?w=400",
        "price": "1299.00",
        "sku": "JWL-SLV-006",
    },
    {
        "id": "seed_007",
        "title": "Cotton Printed Saree - Green Floral",
        "description": "Soft cotton saree with digital floral print. Includes matching blouse piece. Length: 5.5 meters.",
        "image_url": "https://images.unsplash.com/photo-1610189352649-89654e491d10?w=400",
        "price": "1599.00",
        "sku": "SAR-GRN-007",
    },
    {
        "id": "seed_008",
        "title": "Men's Formal White Shirt",
        "description": "Crisp white formal shirt in Egyptian cotton. Spread collar, French cuffs. Wrinkle-resistant finish.",
        "image_url": "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=400",
        "price": "1499.00",
        "sku": "SHR-WHT-008",
    },
]


def seed_database() -> None:
    """Populate the database with sample data for testing."""
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Create or get demo seller
        seller = db.query(Seller).filter_by(shop="demo-store.myshopify.com").first()
        if not seller:
            seller = Seller(
                shop="demo-store.myshopify.com",
                access_token="demo_token",
                refresh_token="",
            )
            db.add(seller)
            db.commit()
            db.refresh(seller)
            print(f"[OK] Created demo seller (id={seller.id})")
        else:
            print(f"[INFO] Demo seller already exists (id={seller.id})")

        # Insert sample products
        added = 0
        for prod_data in SAMPLE_PRODUCTS:
            existing = db.query(Product).filter_by(id=prod_data["id"]).first()
            if not existing:
                product = Product(
                    id=prod_data["id"],
                    seller_id=seller.id,
                    title=prod_data["title"],
                    description=prod_data["description"],
                    image_url=prod_data["image_url"],
                    price=prod_data["price"],
                    sku=prod_data["sku"],
                )
                db.add(product)
                added += 1

        db.commit()
        print(f"[OK] Added {added} sample products (total: {len(SAMPLE_PRODUCTS)})")

        # Print summary
        total_sellers = db.query(Seller).count()
        total_products = db.query(Product).count()
        print(f"\nDatabase summary:")
        print(f"   Sellers:  {total_sellers}")
        print(f"   Products: {total_products}")
        print(f"\nReady! Start the server with: python -m app.main")

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
