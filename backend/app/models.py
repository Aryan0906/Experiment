from sqlalchemy import Column, Integer, String, DateTime, Float, JSON, ForeignKey
from sqlalchemy.orm import relationship, Mapped
from app.database import Base
from datetime import datetime, timezone
from typing import List


class Seller(Base):
    """Seller model for representing Shopify sellers."""
    __tablename__ = "sellers"

    id = Column(Integer, primary_key=True, index=True)
    shop = Column(String, unique=True, index=True)  # e.g., "myshop.myshopify.com"
    access_token = Column(String)  # Store encrypted in production
    refresh_token = Column(String)  # Store encrypted in production
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    products: Mapped[List["Product"]] = relationship("Product", back_populates="seller")
    jobs: Mapped[List["ExtractionJob"]] = relationship("ExtractionJob", back_populates="seller")


class Product(Base):
    """Product model for representing Shopify products."""
    __tablename__ = "products"

    id = Column(String, primary_key=True)  # Shopify product ID
    seller_id = Column(Integer, ForeignKey("sellers.id"), index=True)
    title = Column(String, index=True)
    description = Column(String)
    image_url = Column(String)
    price = Column(String)
    sku = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    seller: Mapped["Seller"] = relationship("Seller", back_populates="products")
    extracted_attributes: Mapped[List["ExtractedAttribute"]] = relationship(
        "ExtractedAttribute", back_populates="product"
    )


class ExtractionJob(Base):
    """ExtractionJob model representing background extraction processing."""
    __tablename__ = "extraction_jobs"

    id = Column(String, primary_key=True)  # UUID
    seller_id = Column(Integer, ForeignKey("sellers.id"), index=True)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    progress = Column(Integer, default=0)  # 0-100
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    seller: Mapped["Seller"] = relationship("Seller", back_populates="jobs")
    extracted_attributes: Mapped[List["ExtractedAttribute"]] = relationship(
        "ExtractedAttribute", back_populates="job"
    )


class ExtractedAttribute(Base):
    """ExtractedAttribute model holding the output from VLM extraction."""
    __tablename__ = "extracted_attributes"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String, ForeignKey("products.id"), index=True)
    job_id = Column(String, ForeignKey("extraction_jobs.id"), index=True)
    attributes = Column(JSON)  # {"brand": "Nike", "size": "M", ...}
    confidence = Column(Float)  # 0.0 - 1.0
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    product: Mapped["Product"] = relationship("Product", back_populates="extracted_attributes")
    job: Mapped["ExtractionJob"] = relationship(
        "ExtractionJob", back_populates="extracted_attributes"
    )
