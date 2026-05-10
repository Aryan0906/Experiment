"""
Background processor for extraction jobs.

Iterates through a seller's products, extracts attributes using the
configured VLM backend, and saves results to the database.
"""
import asyncio
import os
from pathlib import Path
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models import Product, ExtractionJob, ExtractedAttribute
from .vlm import get_extractor
from ..config import settings


async def run_extraction_job(job_id: str) -> None:
    """Process an extraction job."""
    db: Session = SessionLocal()
    try:
        job = db.query(ExtractionJob).filter_by(id=job_id).first()
        if not job:
            return

        job.status = "processing"
        job.progress = 0
        db.commit()

        products = db.query(Product).filter_by(seller_id=job.seller_id).all()
        if not products:
            job.status = "completed"
            job.progress = 100
            db.commit()
            return

        extractor = get_extractor(
            backend=settings.extraction_backend,
            api_key=settings.openai_api_key,
            model_path=settings.fine_tuned_model_path,
        )

        total = len(products)
        for i, product in enumerate(products):
            try:
                # Try local image path first
                image_path = None
                if product.image_url:
                    # If it's a local file path, use it
                    if os.path.exists(product.image_url):
                        image_path = product.image_url
                    else:
                        # Try to find image in uploads folder
                        filename = Path(product.image_url).name
                        potential_paths = [
                            f"uploads/{filename}",
                            f"backend/uploads/{filename}",
                            f"../uploads/{filename}",
                        ]
                        for p in potential_paths:
                            if os.path.exists(p):
                                image_path = p
                                break

                if image_path:
                    attrs = await extractor.extract(
                        image_path=image_path,
                        description=product.description or "",
                        title=product.title or "",
                    )
                else:
                    # Fallback: use mock for products without images
                    from .vlm import MockExtractor
                    mock = MockExtractor()
                    attrs = await mock.extract(
                        image_path="",
                        description=product.description or "",
                        title=product.title or "",
                    )

                confidence = attrs.pop("confidence", 0.0)

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

            except Exception as e:
                print(f"[EXTRACT] Error for product {product.id}: {e}")
                pass

            job.progress = int(((i + 1) / total) * 100)
            db.commit()

            # Small delay to avoid overwhelming the API
            await asyncio.sleep(0.1)

        job.status = "completed"
        job.progress = 100
        db.commit()

    except Exception as e:
        print(f"[EXTRACT] Job failed: {e}")
        try:
            job = db.query(ExtractionJob).filter_by(id=job_id).first()
            if job:
                job.status = "failed"
                db.commit()
        except Exception:
            pass
    finally:
        db.close()