"""
Background processor for extraction jobs.

Iterates through a seller's products, extracts attributes using the
configured VLM backend, and saves results to the database.
"""
import asyncio
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Product, ExtractionJob, ExtractedAttribute
from app.extraction.vlm import get_extractor
from app.config import settings


async def run_extraction_job(job_id: str) -> None:
    """
    Process an extraction job: extract attributes for every product
    belonging to the job's seller, updating progress as we go.
    """
    db: Session = SessionLocal()
    try:
        job = db.query(ExtractionJob).filter_by(id=job_id).first()
        if not job:
            return

        job.status = "processing"
        job.progress = 0
        db.commit()

        # Get all products for this seller
        products = db.query(Product).filter_by(seller_id=job.seller_id).all()
        if not products:
            job.status = "completed"
            job.progress = 100
            db.commit()
            return

        extractor = get_extractor(
            backend=settings.extraction_backend,
            api_key=settings.openai_api_key,
        )

        total = len(products)
        for i, product in enumerate(products):
            try:
                attrs = await extractor.extract(
                    image_url=product.image_url or "",
                    description=product.description or "",
                    title=product.title or "",
                )

                confidence = attrs.pop("confidence", 0.0)

                # Upsert: delete old extraction for this product+job, insert new
                db.query(ExtractedAttribute).filter_by(
                    product_id=product.id, job_id=job_id
                ).delete()

                extracted = ExtractedAttribute(
                    product_id=product.id,
                    job_id=job_id,
                    attributes=attrs,
                    confidence=confidence,
                )
                db.add(extracted)

            except Exception:
                # Skip failed products, continue with the rest
                pass

            # Update progress
            job.progress = int(((i + 1) / total) * 100)
            db.commit()

            # Small delay to avoid overwhelming the API (especially for GPT-4o)
            await asyncio.sleep(0.1)

        job.status = "completed"
        job.progress = 100
        db.commit()

    except Exception:
        # Mark job as failed on unexpected errors
        try:
            job = db.query(ExtractionJob).filter_by(id=job_id).first()
            if job:
                job.status = "failed"
                db.commit()
        except Exception:
            pass
    finally:
        db.close()
