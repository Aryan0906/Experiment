# Gate 3: Bug-Free Code Generation (7-Gate Checklist)

## Purpose
Write code that passes 7 quality gates BEFORE being considered "done". Prevents bugs at the source.

## Trigger
Runs after Gate 2 (Test-First) completes. Code is written to make tests pass.

## The 7 Gates

### Gate 3.1: Type Safety
**Rule:** Every function parameter, return value, and variable has explicit type annotations.

```python
# ❌ BAD: No types
def extract_attributes(product_id, image_url):
    result = some_operation()
    return result

# ✅ GOOD: Full type safety
from typing import Optional, Dict, List, Literal
from uuid import UUID

def extract_attributes(
    product_id: UUID,
    image_url: str,
    model_version: str = "qwen2-vl-ft-v1",
    max_retries: int = 2
) -> ExtractionResult:
    # Implementation
    ...
```

**Checklist:**
- [ ] All function parameters have types
- [ ] All return values have types
- [ ] All class attributes have types
- [ ] No use of `Any` unless absolutely unavoidable (and documented why)
- [ ] Pydantic models used for all data structures crossing API boundaries

### Gate 3.2: Error Handling
**Rule:** Every external call (API, DB, file system, model inference) is wrapped in try-except with specific error types.

```python
# ❌ BAD: Bare except or no handling
try:
    response = requests.get(image_url)
    data = response.json()
except:
    pass

# ✅ GOOD: Specific error handling
from requests.exceptions import HTTPError, ConnectionError, Timeout
from json import JSONDecodeError

try:
    response = requests.get(image_url, timeout=10)
    response.raise_for_status()  # Raises HTTPError for 4xx/5xx
    data = response.json()
except HTTPError as e:
    if e.response.status_code == 404:
        return ExtractionResult(
            status="failed",
            error_message=f"Image not found: {image_url}"
        )
    elif e.response.status_code >= 500:
        return ExtractionResult(
            status="retry",
            error_message=f"Server error, will retry: {e}"
        )
    raise
except Timeout:
    return ExtractionResult(
        status="failed",
        error_message=f"Request timed out after 10s: {image_url}"
    )
except JSONDecodeError as e:
    return ExtractionResult(
        status="failed",
        error_message=f"Invalid JSON response: {e}"
    )
```

**Checklist:**
- [ ] All `requests` calls have timeout parameter
- [ ] All database queries handle `IntegrityError`, `OperationalError`
- [ ] All model inference handles `RuntimeError`, `CUDAOutOfMemoryError`
- [ ] No bare `except:` clauses
- [ ] Error messages are actionable (tell user what to do)

### Gate 3.3: Resource Management
**Rule:** All resources (DB connections, file handles, GPU memory) are properly acquired and released.

```python
# ❌ BAD: Resource leak
def process_image(image_url: str) -> bytes:
    response = requests.get(image_url)
    image_data = response.content
    # Response connection never closed if exception occurs
    return image_data

# ✅ GOOD: Context manager
from contextlib import contextmanager
import torch

@contextmanager
def managed_http_session():
    session = requests.Session()
    try:
        yield session
    finally:
        session.close()

def process_image(image_url: str) -> bytes:
    with managed_http_session() as session:
        response = session.get(image_url, timeout=10)
        response.raise_for_status()
        return response.content

def run_inference(model, input_tensor):
    try:
        with torch.no_grad():
            output = model(input_tensor)
        return output
    finally:
        # Always clear VRAM after inference
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
```

**Checklist:**
- [ ] All file operations use `with open(...)` context manager
- [ ] All HTTP sessions are closed (use `Session()` + `close()` or context manager)
- [ ] All database sessions are committed/rolled back in `finally` block
- [ ] GPU memory cleared after every inference (`torch.cuda.empty_cache()`)
- [ ] No temporary files left on disk (use `tempfile.NamedTemporaryFile(delete=True)`)

### Gate 3.4: Input Validation
**Rule:** Validate ALL inputs at function boundaries. Never trust external data.

```python
from pydantic import BaseModel, validator, HttpUrl
from typing import List
from uuid import UUID

class ExtractionRequest(BaseModel):
    product_ids: List[UUID]
    model_version: str = "qwen2-vl-ft-v1"
    
    @validator('product_ids')
    def validate_product_ids_not_empty(cls, v):
        if not v:
            raise ValueError("product_ids cannot be empty")
        if len(v) > 100:
            raise ValueError("Maximum 100 products per batch")
        # Deduplicate
        return list(set(v))
    
    @validator('model_version')
    def validate_model_version(cls, v):
        allowed_versions = ["qwen2-vl-ft-v1", "llava-1.5-7b"]
        if v not in allowed_versions:
            raise ValueError(f"model_version must be one of: {allowed_versions}")
        return v

# Usage
def extraction_batch(request: ExtractionRequest) -> JobResponse:
    # request is already validated by Pydantic
    # No need for manual checks
    ...
```

**Checklist:**
- [ ] All API endpoints validate input with Pydantic
- [ ] All lists have max length limits (prevent DoS)
- [ ] All URLs validated as valid HTTP/HTTPS URLs
- [ ] All UUIDs validated as proper format
- [ ] All enum values validated against allowed set
- [ ] SQL injection prevented (use ORM, never string concatenation)

### Gate 3.5: Logging & Observability
**Rule:** Every significant action is logged with structured logging. No print statements.

```python
# ❌ BAD: Print statements
def extract_attributes(product_id, image_url):
    print(f"Starting extraction for {product_id}")
    ...
    print("Done")

# ✅ GOOD: Structured logging
import logging
from contextvars import ContextVar

logger = logging.getLogger(__name__)
request_id_ctx = ContextVar('request_id', default=None)

def extract_attributes(product_id: UUID, image_url: str, request_id: str) -> ExtractionResult:
    token = request_id_ctx.set(request_id)
    try:
        logger.info(
            "extraction_started",
            extra={
                "product_id": str(product_id),
                "image_url": image_url,
                "request_id": request_id
            }
        )
        
        start_time = time.time()
        result = _do_extraction(product_id, image_url)
        elapsed_ms = (time.time() - start_time) * 1000
        
        logger.info(
            "extraction_completed",
            extra={
                "product_id": str(product_id),
                "status": result.status,
                "processing_time_ms": elapsed_ms,
                "request_id": request_id
            }
        )
        
        return result
    except Exception as e:
        logger.error(
            "extraction_failed",
            extra={
                "product_id": str(product_id),
                "error": str(e),
                "request_id": request_id
            },
            exc_info=True
        )
        raise
    finally:
        request_id_ctx.reset(token)
```

**Checklist:**
- [ ] No `print()` statements in production code
- [ ] All logs include correlation ID (request_id) for tracing
- [ ] All errors logged with `exc_info=True` for stack traces
- [ ] Log levels used correctly: DEBUG (verbose), INFO (normal ops), WARNING (recoverable), ERROR (failure)
- [ ] Sensitive data (tokens, passwords) NEVER logged

### Gate 3.6: Idempotency & Retry Safety
**Rule:** Operations can be safely retried without side effects.

```python
# ❌ BAD: Not idempotent
def save_extraction(product_id, attributes):
    # If called twice, creates duplicate records
    db.add(Extraction(product_id=product_id, attributes=attributes))
    db.commit()

# ✅ GOOD: Idempotent with upsert
from sqlalchemy.dialects.postgresql import insert

def save_extraction(product_id: UUID, attributes: dict, request_id: str) -> Extraction:
    stmt = insert(Extraction).values(
        product_id=product_id,
        attributes=attributes,
        request_id=request_id,  # Unique per attempt
        created_at=datetime.utcnow()
    ).on_conflict_do_update(
        index_elements=['product_id', 'request_id'],
        set_={
            "attributes": attributes,
            "updated_at": datetime.utcnow()
        }
    )
    db.execute(stmt)
    db.commit()
    return db.query(Extraction).filter_by(product_id=product_id, request_id=request_id).first()
```

**Checklist:**
- [ ] Database writes use upsert (INSERT ... ON CONFLICT) where appropriate
- [ ] Celery tasks have idempotency keys to prevent duplicate processing
- [ ] External API calls check if operation already completed before retrying
- [ ] No increment operations (`count += 1`) without locks

### Gate 3.7: Security Hardening
**Rule:** Follow OWASP Top 10. No hardcoded secrets. Input sanitization.

```python
# ❌ BAD: Security vulnerabilities
API_KEY = "sk-1234567890"  # Hardcoded secret

@app.get("/products/{product_id}")
def get_product(product_id: str):
    query = f"SELECT * FROM products WHERE id = '{product_id}'"  # SQL injection
    result = db.execute(query)
    return result

# ✅ GOOD: Secure
from app.core.config import settings  # Loads from environment
from app.core.security import decrypt_token

@app.get("/products/{product_id}")
def get_product(product_id: UUID, current_user: User = Depends(get_current_user)):
    # Authorization check
    if product_id not in current_user.allowed_product_ids:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # ORM prevents SQL injection
    product = db.query(Product).filter_by(id=product_id, seller_id=current_user.seller_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return product
```

**Checklist:**
- [ ] No hardcoded secrets (use environment variables via `settings`)
- [ ] All SQL uses ORM (no raw queries with string interpolation)
- [ ] All user input sanitized (Pydantic validators)
- [ ] Authentication required for all protected endpoints
- [ ] Authorization checks verify user owns the resource
- [ ] Rate limiting enabled on all public endpoints
- [ ] CORS configured to allow only trusted domains
- [ ] HTTPS enforced (HSTS header)

## Code Sign-Off
**Code is READY when:**
- ✅ All 7 gates passed
- ✅ All tests from Gate 2 pass
- ✅ No linting errors (ruff, mypy, black)
- ✅ No security warnings (bandit)
- ✅ Code reviewed against this checklist

**If any gate fails → FIX before proceeding to Gate 4.**
