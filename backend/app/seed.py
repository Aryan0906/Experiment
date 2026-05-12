"""
Seed script to populate the local database with sample products for testing.
Supports multi-user isolation with user_id foreign key.

Run with: python -m backend.app.seed --email demo@example.com
"""
import argparse
import uuid
from .database import SessionLocal, Base, engine
from .models import User, Product
from datetime import datetime, timezone


DEMO_USER_EMAIL = "demo@example.com"
DEMO_USER_NAME = "Demo User"

SAMPLE_PRODUCTS = [
    {
        "title": "Classic Blue Cotton T-Shirt",
        "description": "Premium 100% cotton crew-neck t-shirt in navy blue.",
        "image_url": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400",
        "price": "29.99",
        "sku": "TEE-BLU-001",
        "attributes": {
            "brand": "ComfortWear",
            "color": "Navy Blue",
            "size": "M",
            "material": "100% Cotton",
            "category": "Apparel",
            "confidence": 0.92
        },
        "anomaly_result": {
            "is_blurry": False,
            "blur_score": 0.12,
            "is_wrong_background": False,
            "background_score": 0.08,
            "is_counterfeit": False,
            "counterfeit_score": 0.05,
            "anomaly_score": 0.12
        },
        "status": "done"
    },
    {
        "title": "Women's Red Silk Dress",
        "description": "Elegant evening dress in deep red silk with flowing design.",
        "image_url": "https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=400",
        "price": "89.99",
        "sku": "DRS-RED-002",
        "attributes": {
            "brand": "Elegance",
            "color": "Red",
            "size": "S",
            "material": "Silk",
            "category": "Dresses",
            "confidence": 0.88
        },
        "anomaly_result": {
            "is_blurry": True,
            "blur_score": 0.78,
            "is_wrong_background": False,
            "background_score": 0.15,
            "is_counterfeit": False,
            "counterfeit_score": 0.10,
            "anomaly_score": 0.78
        },
        "status": "done"
    },
    {
        "title": "Men's Leather Wallet - Brown",
        "description": "Genuine leather bifold wallet with multiple card slots.",
        "image_url": "https://images.unsplash.com/photo-1627123424574-18bd083315a4?w=400",
        "price": "49.99",
        "sku": "WAL-BRN-003",
        "attributes": {
            "brand": "LeatherCraft",
            "color": "Brown",
            "size": "Standard",
            "material": "Genuine Leather",
            "category": "Accessories",
            "confidence": 0.95
        },
        "anomaly_result": {
            "is_blurry": False,
            "blur_score": 0.08,
            "is_wrong_background": True,
            "background_score": 0.82,
            "is_counterfeit": False,
            "counterfeit_score": 0.12,
            "anomaly_score": 0.82
        },
        "status": "done"
    },
    {
        "title": "Running Sneakers - White/Grey",
        "description": "Lightweight athletic sneakers with breathable mesh upper.",
        "image_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400",
        "price": "79.99",
        "sku": "SNK-WHT-004",
        "attributes": {
            "brand": "SportMax",
            "color": "White/Grey",
            "size": "10",
            "material": "Mesh/Synthetic",
            "category": "Footwear",
            "confidence": 0.91
        },
        "anomaly_result": {
            "is_blurry": False,
            "blur_score": 0.05,
            "is_wrong_background": False,
            "background_score": 0.10,
            "is_counterfeit": False,
            "counterfeit_score": 0.08,
            "anomaly_score": 0.10
        },
        "status": "done"
    },
    {
        "title": "Gold Plated Necklace",
        "description": "18K gold plated chain necklace with pendant.",
        "image_url": "https://images.unsplash.com/photo-1599643478518-a5f3899e7b2e?w=400",
        "price": "129.99",
        "sku": "NCK-GLD-005",
        "attributes": {
            "brand": "LuxeJewels",
            "color": "Gold",
            "size": "18 inches",
            "material": "Gold Plated",
            "category": "Jewelry",
            "confidence": 0.89
        },
        "anomaly_result": {
            "is_blurry": False,
            "blur_score": 0.11,
            "is_wrong_background": False,
            "background_score": 0.09,
            "is_counterfeit": True,
            "counterfeit_score": 0.88,
            "anomaly_score": 0.88
        },
        "status": "done"
    },
]


def seed_database(email: str = DEMO_USER_EMAIL) -> None:
    """Populate the database with sample data for testing."""
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Create or get demo user
        user = db.query(User).filter_by(email=email).first()
        if not user:
            user = User(
                email=email,
                name=DEMO_USER_NAME,
                google_id=f"demo_google_id_{email.replace('@', '_').replace('.', '_')}",
                avatar_url=None,
                is_admin=True  # Demo user is admin for testing
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"[OK] Created demo user: {email} (id={user.id})")
        else:
            print(f"[INFO] Demo user already exists: {email} (id={user.id})")
            # Make sure demo user is admin
            if not user.is_admin:
                user.is_admin = True
                db.commit()
                print(f"[OK] Updated demo user to admin")

        # Insert sample products for this user
        added = 0
        for idx, prod_data in enumerate(SAMPLE_PRODUCTS):
            product_id = f"demo_{user.id}_{idx + 1}"
            existing = db.query(Product).filter_by(id=product_id).first()
            
            if not existing:
                product = Product(
                    id=product_id,
                    user_id=user.id,
                    title=prod_data["title"],
                    description=prod_data["description"],
                    image_url=prod_data["image_url"],
                    price=prod_data["price"],
                    sku=prod_data["sku"],
                    status=prod_data["status"],
                    attributes=prod_data["attributes"],
                    anomaly_result=prod_data["anomaly_result"],
                    corrected_attributes=None
                )
                db.add(product)
                added += 1
            else:
                # Update existing product with latest data
                existing.title = prod_data["title"]
                existing.description = prod_data["description"]
                existing.image_url = prod_data["image_url"]
                existing.price = prod_data["price"]
                existing.sku = prod_data["sku"]
                existing.status = prod_data["status"]
                existing.attributes = prod_data["attributes"]
                existing.anomaly_result = prod_data["anomaly_result"]

        db.commit()
        print(f"[OK] Added/updated {added} sample products for user {email}")

        # Print summary
        total_users = db.query(User).count()
        total_products = db.query(Product).filter_by(user_id=user.id).count()
        print(f"\n{'='*50}")
        print(f"Database Summary:")
        print(f"   Total Users:     {total_users}")
        print(f"   Demo User ID:    {user.id}")
        print(f"   Demo Products:   {total_products}")
        print(f"{'='*50}")
        print(f"\nReady! Login with Google using: {email}")
        print(f"Start the server with: python -m app.main")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Failed to seed database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed database with demo data")
    parser.add_argument(
        "--email",
        type=str,
        default=DEMO_USER_EMAIL,
        help=f"Email for demo user (default: {DEMO_USER_EMAIL})"
    )
    args = parser.parse_args()
    
    seed_database(email=args.email)
