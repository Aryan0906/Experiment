"""
Product endpoints for upload, retrieval, and attribute management.
Supports multi-user isolation via user_id filtering.
"""
import os
import uuid
import csv
import io
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query, Form, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import get_db, SessionLocal
from ..models import User, Product
from ..api.deps import get_current_user
from ..ml.model_cache import get_qwen_model, get_ccvae_model

router = APIRouter()

# Configuration
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "backend/uploads"))
TRAINING_DATA_DIR = Path(os.getenv("TRAINING_DATA_DIR", "backend/app/ml/training_data"))
ANOMALY_THRESHOLD = float(os.getenv("ANOMALY_THRESHOLD", "0.7"))

# Ensure directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
TRAINING_DATA_DIR.mkdir(parents=True, exist_ok=True)


class ProductCreate(BaseModel):
    """Request body for creating a product."""
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[str] = None
    sku: Optional[str] = None


class AttributeUpdate(BaseModel):
    """Request body for updating attributes."""
    attributes: Dict[str, Any]


class ProductResponse(BaseModel):
    """Product response with all fields."""
    id: str
    user_id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    price: Optional[str] = None
    sku: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None
    anomaly_result: Optional[Dict[str, Any]] = None
    corrected_attributes: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    """Paginated product list response."""
    products: List[ProductResponse]
    total: int
    page: int
    limit: int
    has_more: bool


@router.post("/upload", response_model=ProductResponse)
async def upload_product(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    price: Optional[str] = Form(None),
    sku: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a product image for attribute extraction and anomaly detection.
    
    The image is saved locally and a background task processes it.
    Client should poll GET /products/{id} to check status.
    
    Args:
        file: Product image file
        title: Optional product title
        description: Optional product description
        price: Optional product price
        sku: Optional SKU
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Created product with status 'queued'
    """
    from fastapi import Form
    
    # Generate unique product ID
    product_id = str(uuid.uuid4())
    
    # Save uploaded file
    filename = f"{product_id}_{file.filename}"
    file_path = UPLOAD_DIR / filename
    
    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save image: {str(e)}"
        )
    
    # Create product record
    product = Product(
        id=product_id,
        user_id=current_user.id,
        title=title,
        description=description,
        image_url=f"/uploads/{filename}",
        image_path=str(file_path),
        price=price,
        sku=sku,
        status="queued"
    )
    
    db.add(product)
    db.commit()
    db.refresh(product)
    
    # Start background processing using FastAPI BackgroundTasks
    if background_tasks:
        background_tasks.add_task(process_product_image, product_id, str(file_path))
    
    return ProductResponse.model_validate(product)


async def process_product_image(product_id: str, image_path: str):
    """
    Background task to process product image.
    
    Steps:
    1. Extract attributes using Qwen2-VL
    2. Detect anomalies using CC-VAE
    3. Update product record with results
    """
    from sqlalchemy.orm import Session
    from ..database import SessionLocal
    
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return
        
        # Step 1: Extract attributes
        product.status = "extracting_attributes"
        db.commit()
        
        try:
            model, processor = get_qwen_model()
            attributes = await extract_attributes_with_qwen(
                image_path, model, processor
            )
            product.attributes = attributes
        except Exception as e:
            print(f"[PROCESS] Attribute extraction failed: {e}")
            product.attributes = {
                "brand": "Unknown",
                "color": "Unknown",
                "size": "Unknown",
                "material": "Unknown",
                "category": "Unknown",
                "confidence": 0.5,
                "error": str(e)
            }
        
        db.commit()
        
        # Step 2: Detect anomalies
        product.status = "detecting_anomalies"
        db.commit()
        
        try:
            ccvae_model = get_ccvae_model()
            anomaly_result = ccvae_model.detect_anomalies(image_path)
            product.anomaly_result = anomaly_result
        except Exception as e:
            print(f"[PROCESS] Anomaly detection failed: {e}")
            product.anomaly_result = {
                "is_blurry": False,
                "blur_score": 0.0,
                "is_wrong_background": False,
                "background_score": 0.0,
                "is_counterfeit": False,
                "counterfeit_score": 0.0,
                "anomaly_score": 0.0,
                "error": str(e)
            }
        
        db.commit()
        
        # Step 3: Mark as done
        product.status = "done"
        db.commit()
        
        print(f"[PROCESS] Product {product_id} processing complete")
        
    except Exception as e:
        print(f"[PROCESS] Fatal error processing {product_id}: {e}")
        if product:
            product.status = "error"
            product.error_message = str(e)
            db.commit()
    finally:
        db.close()


async def extract_attributes_with_qwen(
    image_path: str,
    model,
    processor
) -> Dict[str, Any]:
    """Extract product attributes using Qwen2-VL model."""
    import torch
    from PIL import Image
    
    # Load image
    image = Image.open(image_path).convert("RGB")
    
    # Create prompt
    prompt = (
        "Extract product attributes from this image. "
        "Return ONLY a JSON object with: brand, size, color, material, category, confidence. "
        "Use null or \"Unknown\" for attributes you cannot determine. "
        "Set confidence between 0.0 and 1.0."
    )
    
    # Format messages for Qwen2-VL
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image"},
                {"type": "text", "text": prompt}
            ]
        }
    ]
    
    # Apply chat template
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    
    # Process inputs
    inputs = processor(text=text, images=image, return_tensors="pt")
    inputs = {k: v.to(model.device) if isinstance(v, torch.Tensor) else v for k, v in inputs.items()}
    
    # Generate
    with torch.no_grad():
        output = model.generate(**inputs, max_new_tokens=200, do_sample=False)
    
    result = processor.decode(output[0], skip_special_tokens=True)
    
    # Parse JSON from response
    import json as json_module
    try:
        # Find JSON in response
        start = result.find("{")
        end = result.rfind("}") + 1
        if start != -1 and end != 0:
            json_str = result[start:end]
            attrs = json_module.loads(json_str)
        else:
            attrs = {}
        
        # Ensure all required fields
        required = ["brand", "size", "color", "material", "category", "confidence"]
        for field in required:
            if field not in attrs:
                attrs[field] = "Unknown" if field != "confidence" else 0.5
        
        return attrs
        
    except json_module.JSONDecodeError:
        return {
            "brand": "Unknown",
            "size": "Unknown",
            "color": "Unknown",
            "material": "Unknown",
            "category": "Unknown",
            "confidence": 0.5,
        }


@router.get("", response_model=ProductListResponse)
async def list_products(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List products for the current user with pagination.
    
    Args:
        page: Page number (1-indexed)
        limit: Items per page
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Paginated list of products
    """
    # Calculate offset
    offset = (page - 1) * limit
    
    # Query products for current user only
    query = db.query(Product).filter(Product.user_id == current_user.id)
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    products = query.order_by(Product.created_at.desc()).offset(offset).limit(limit).all()
    
    return ProductListResponse(
        products=[ProductResponse.model_validate(p) for p in products],
        total=total,
        page=page,
        limit=limit,
        has_more=offset + len(products) < total
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific product by ID.
    
    Only returns products belonging to the current user.
    
    Args:
        product_id: Product UUID
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Product details including status, attributes, and anomaly results
        
    Raises:
        HTTPException: If product not found or doesn't belong to user
    """
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.user_id == current_user.id
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return ProductResponse.model_validate(product)


@router.put("/{product_id}/attributes", response_model=ProductResponse)
async def update_product_attributes(
    product_id: str,
    attribute_update: AttributeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update product attributes (user corrections).
    
    Saves corrected attributes and logs them for future model training.
    
    Args:
        product_id: Product UUID
        attribute_update: New attribute values
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Updated product
        
    Raises:
        HTTPException: If product not found or doesn't belong to user
    """
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.user_id == current_user.id
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Store original attributes before update
    original_attributes = product.corrected_attributes or product.attributes or {}
    corrected_attributes = attribute_update.attributes
    
    # Update corrected attributes
    product.corrected_attributes = corrected_attributes
    product.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(product)
    
    # Log correction for training data
    log_training_correction(
        image_path=product.image_path or product.image_url or "",
        original_attributes=original_attributes,
        corrected_attributes=corrected_attributes
    )
    
    return ProductResponse.model_validate(product)


def log_training_correction(
    image_path: str,
    original_attributes: Dict[str, Any],
    corrected_attributes: Dict[str, Any]
):
    """Log user corrections for future model training."""
    corrections_file = TRAINING_DATA_DIR / "corrections.jsonl"
    
    entry = {
        "image_path": image_path,
        "original_attributes": original_attributes,
        "corrected_attributes": corrected_attributes,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    try:
        with open(corrections_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        print(f"[TRAINING] Failed to log correction: {e}")


@router.get("/{product_id}/csv")
async def download_product_csv(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Download product attributes as CSV.
    
    Uses corrected_attributes if available, otherwise uses extracted attributes.
    
    Args:
        product_id: Product UUID
        db: Database session
        current_user: Authenticated user
        
    Returns:
        CSV file download
    """
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.user_id == current_user.id
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Use corrected attributes if available, otherwise extracted
    attrs = product.corrected_attributes or product.attributes or {}
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        "product_id", "title", "sku", "price",
        "brand", "color", "size", "material", "category", "confidence"
    ])
    
    # Data row
    writer.writerow([
        product.id,
        product.title or "",
        product.sku or "",
        product.price or "",
        attrs.get("brand", ""),
        attrs.get("color", ""),
        attrs.get("size", ""),
        attrs.get("material", ""),
        attrs.get("category", ""),
        attrs.get("confidence", "")
    ])
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=product_{product_id}.csv"
        }
    )


@router.delete("/{product_id}")
async def delete_product(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a product.
    
    Args:
        product_id: Product UUID
        db: Database session
        current_user: Authenticated user
        
    Raises:
        HTTPException: If product not found or doesn't belong to user
    """
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.user_id == current_user.id
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Delete image file if exists
    if product.image_path and os.path.exists(product.image_path):
        try:
            os.remove(product.image_path)
        except Exception as e:
            print(f"[DELETE] Failed to remove image file: {e}")
    
    # Delete product record
    db.delete(product)
    db.commit()
    
    return {"message": "Product deleted successfully"}


@router.get("/{product_id}/status")
async def get_product_status(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get only the status of a product (lightweight endpoint for polling).

    Args:
        product_id: Product UUID
        db: Database session
        current_user: Authenticated user

    Returns:
        Product status and basic info
    """
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.user_id == current_user.id
    ).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    return {
        "id": product.id,
        "status": product.status,
        "error_message": product.error_message,
        "has_attributes": product.attributes is not None,
        "has_anomaly_result": product.anomaly_result is not None,
    }
