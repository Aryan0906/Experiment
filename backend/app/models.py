from sqlalchemy import Column, Integer, String, DateTime, Float, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship, Mapped
from .database import Base
from datetime import datetime, timezone
from typing import List, Optional


class User(Base):
    """User model for authentication."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String)
    google_id = Column(String, unique=True, index=True)
    avatar_url = Column(String)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    products: Mapped[List["Product"]] = relationship("Product", back_populates="user")


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


class OAuthSession(Base):
    """OAuthSession model for storing temporary OAuth state tokens."""
    __tablename__ = "oauth_sessions"

    id = Column(Integer, primary_key=True, index=True)
    shop = Column(String, index=True)  # Shopify shop domain
    state = Column(String, unique=True, index=True)  # State token from OAuth flow
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Product(Base):
    """Product model for representing Shopify products with extraction results."""
    __tablename__ = "products"

    id = Column(String, primary_key=True)  # Shopify product ID or UUID for uploads
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=True)
    seller_id = Column(Integer, ForeignKey("sellers.id"), index=True, nullable=True)
    title = Column(String, index=True)
    description = Column(String)
    image_url = Column(String)
    image_path = Column(String)  # Local path for uploaded images
    price = Column(String)
    sku = Column(String)
    
    # Extraction status tracking
    status = Column(String, default="queued")  # queued, extracting_attributes, detecting_anomalies, done, error
    error_message = Column(String, nullable=True)
    
    # Extracted attributes from VLM
    attributes = Column(JSON, nullable=True)  # Raw extracted attributes
    
    # Anomaly detection results
    anomaly_result = Column(JSON, nullable=True)  # {is_blurry, blur_score, is_wrong_background, etc.}
    
    # User-corrected attributes
    corrected_attributes = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user: Mapped[Optional["User"]] = relationship("User", back_populates="products")
    seller: Mapped[Optional["Seller"]] = relationship("Seller", back_populates="products")
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
