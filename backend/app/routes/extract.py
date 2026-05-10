"""
Routes for extraction jobs and retrieved attributes.

POST /api/extract       — Start a new extraction job
GET  /api/jobs/{job_id} — Poll job status/progress
GET  /api/extracted     — Get all extracted attributes for a seller
"""
import uuid
import asyncio
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Seller, ExtractionJob, ExtractedAttribute
from ..extraction.processor import run_extraction_job

router = APIRouter()


def _run_async_extraction(job_id: str) -> None:
    """Helper to run the async extraction in a new event loop (for BackgroundTasks)."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_extraction_job(job_id))
    finally:
        loop.close()


@router.post("/extract")
async def start_extraction(
    seller_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Starts an extraction job for all products belonging to the seller.
    The job runs in the background; poll GET /api/jobs/{job_id} for progress.
    """
    seller = db.query(Seller).filter_by(id=seller_id).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found.")

    job_id = str(uuid.uuid4())
    job = ExtractionJob(id=job_id, seller_id=seller_id, status="pending", progress=0)
    db.add(job)
    db.commit()

    # Launch extraction in background
    background_tasks.add_task(_run_async_extraction, job_id)

    return {"job_id": job_id, "status": "pending"}


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """
    Returns the current status and progress of an extraction job.
    """
    job = db.query(ExtractionJob).filter_by(id=job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    return {
        "job_id": job.id,
        "status": job.status,
        "progress": job.progress,
    }


@router.get("/extracted")
async def get_extracted_attributes(seller_id: int, db: Session = Depends(get_db)):
    """
    Returns all extracted attributes for a seller's products.
    Uses the most recent extraction per product.
    """
    seller = db.query(Seller).filter_by(id=seller_id).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found.")

    # Get the latest extraction for each product
    from ..models import Product
    products = db.query(Product).filter_by(seller_id=seller.id).all()
    product_ids = [p.id for p in products]

    if not product_ids:
        return {"extracted": {}}

    # For each product, get the most recent extraction
    result = {}
    for pid in product_ids:
        attr = (
            db.query(ExtractedAttribute)
            .filter_by(product_id=pid)
            .order_by(ExtractedAttribute.created_at.desc())
            .first()
        )
        if attr:
            result[pid] = {
                "attributes": attr.attributes,
                "confidence": attr.confidence,
            }

    return {"extracted": result}
