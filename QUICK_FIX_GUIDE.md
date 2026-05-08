# Immediate Action Plan: Fix 3 Critical Issues (45 minutes total)

---

## Issue #1: Dashboard Uses Mock Data Instead of Real API (5 minutes)

**File:** `frontend/src/pages/DashboardPage.tsx`

**Problem:** Lines 31-40 use hardcoded mock data instead of calling the real API endpoint.

**Current Code:**
```typescript
const fetchExtractedAttributes = () => {
    const mockExtracted: Record<string, ...> = {};
    products.forEach(p => {
        mockExtracted[p.id] = {
            attributes: { brand: "Nike", size: "M", color: "Blue", material: "Cotton", category: "T-Shirt", confidence: 0.92 },
            confidence: 0.92
        };
    });
    setExtracted(mockExtracted);
};
```

**Fixed Code:**
```typescript
const fetchExtractedAttributes = async () => {
    try {
        const res = await fetch(`${API_URL}/api/extracted?seller_id=${sellerId}`);
        if (res.ok) {
            const data = await res.json();
            setExtracted(data.extracted || {});
        }
    } catch (e) {
        console.error("Failed to fetch extracted attributes", e);
        setExtracted({});
    }
};
```

**Then Update the useEffect to await it:**
```typescript
useEffect(() => { 
    Promise.resolve()
        .then(() => fetchProducts())
        .then(() => fetchExtractedAttributes()); 
}, []);
```

**Why This Matters:**
- Connects the dashboard to real extraction data
- Allows you to test the end-to-end flow
- Shows actual mock attributes from the backend

---

## Issue #2: CSV Export Missing Extracted Attributes (10 minutes)

**File:** `backend/app/routes/products.py`

**Problem:** CSV export only includes raw product fields (title, price, SKU). Should include extracted attributes (brand, color, size, etc.).

**Current Code (Approximate):**
```python
@router.get("/products/csv")
def export_csv(seller_id: int, db: Session = Depends(get_db)):
    products = db.query(Product).filter_by(seller_id=seller_id).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow(["id", "title", "price", "sku", "seller_id"])
    
    # Rows
    for product in products:
        writer.writerow([product.id, product.title, product.price, product.sku, product.seller_id])
    
    # Return response
    ...
```

**Fixed Code:**
```python
@router.get("/products/csv")
def export_csv(seller_id: int, db: Session = Depends(get_db)):
    from app.models import ExtractedAttribute
    
    products = db.query(Product).filter_by(seller_id=seller_id).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Headers (includes extracted attributes)
    writer.writerow([
        "id", "title", "price", "sku", 
        "brand", "size", "color", "material", "category", "confidence",
        "seller_id"
    ])
    
    # Rows
    for product in products:
        # Get the most recent extraction for this product
        extraction = db.query(ExtractedAttribute)\
            .filter_by(product_id=product.id)\
            .order_by(ExtractedAttribute.created_at.desc())\
            .first()
        
        if extraction:
            attrs = extraction.attributes
            writer.writerow([
                product.id, 
                product.title, 
                product.price, 
                product.sku,
                attrs.get("brand", ""),
                attrs.get("size", ""),
                attrs.get("color", ""),
                attrs.get("material", ""),
                attrs.get("category", ""),
                extraction.confidence,
                product.seller_id
            ])
        else:
            # No extraction yet — empty cells
            writer.writerow([
                product.id, 
                product.title, 
                product.price, 
                product.sku,
                "", "", "", "", "", "",  # Empty extracted fields
                product.seller_id
            ])
    
    # Return response
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment;filename=products.csv"}
    )
```

**Why This Matters:**
- CSV now contains the extracted attributes
- Sellers can see brand, color, size, etc. in their export
- Validates that extraction data is being stored correctly

---

## Issue #3: Config Missing VLM Settings (5 minutes)

**File:** `backend/app/config.py`

**Current Code:**
```python
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    """Configuration settings for the application."""
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")
    shopify_api_key: str = os.getenv("SHOPIFY_API_KEY", "test_key")
    shopify_api_secret: str = os.getenv("SHOPIFY_API_SECRET", "test_secret")
    shopify_redirect_uri: str = os.getenv(
        "SHOPIFY_REDIRECT_URI", "http://localhost:8000/auth/shopify/callback"
    )

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
```

**Fixed Code:**
```python
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    """Configuration settings for the application."""
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")
    shopify_api_key: str = os.getenv("SHOPIFY_API_KEY", "test_key")
    shopify_api_secret: str = os.getenv("SHOPIFY_API_SECRET", "test_secret")
    shopify_redirect_uri: str = os.getenv(
        "SHOPIFY_REDIRECT_URI", "http://localhost:8000/auth/shopify/callback"
    )
    
    # VLM Extraction Settings
    extraction_backend: str = os.getenv("EXTRACTION_BACKEND", "mock")  # "mock" | "gpt4v" | "local_vlm"
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")  # Only needed for GPT-4o
    fine_tuned_model_path: str = os.getenv("FINE_TUNED_MODEL_PATH", "")  # Path to your fine-tuned model

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
```

**Create `.env.example` file (at `backend/.env.example`):**
```env
# Database
DATABASE_URL=sqlite:///./test.db

# Shopify OAuth
SHOPIFY_API_KEY=your_shopify_app_api_key
SHOPIFY_API_SECRET=your_shopify_app_secret
SHOPIFY_REDIRECT_URI=http://localhost:8000/auth/shopify/callback

# VLM Extraction Backend
# Options: "mock" (free, instant), "gpt4v" (requires OPENAI_API_KEY), "local_vlm" (requires FINE_TUNED_MODEL_PATH)
EXTRACTION_BACKEND=mock

# Only required if EXTRACTION_BACKEND=gpt4v
OPENAI_API_KEY=

# Only required if EXTRACTION_BACKEND=local_vlm
FINE_TUNED_MODEL_PATH=
```

**Update `backend/.env` (your actual environment file):**
```env
DATABASE_URL=sqlite:///./test.db
SHOPIFY_API_KEY=test_key
SHOPIFY_API_SECRET=test_secret
SHOPIFY_REDIRECT_URI=http://localhost:8000/auth/shopify/callback

# Use mock extractor by default (free, no API calls)
EXTRACTION_BACKEND=mock
OPENAI_API_KEY=
FINE_TUNED_MODEL_PATH=
```

**Why This Matters:**
- Config now supports switching between extractors (mock, GPT-4o, your fine-tuned model)
- Makes it easy to test different backends without code changes
- Prepares you to integrate your fine-tuned VLM later

---

## Bonus: Update `backend/app/extraction/processor.py` to Use Settings

**Current Code (lines 38-41):**
```python
extractor = get_extractor(
    backend=settings.extraction_backend,
    api_key=settings.openai_api_key,
)
```

**Fixed Code:**
```python
extractor = get_extractor(
    backend=settings.extraction_backend,
    api_key=settings.openai_api_key,
    model_path=settings.fine_tuned_model_path,  # ← Add this line
)
```

---

## Step-by-Step Execution Plan

### 1. Fix Dashboard (5 minutes)
```bash
# Edit frontend/src/pages/DashboardPage.tsx
# Lines 31-40: Replace mock data with async API call
# Lines 28-29: Update useEffect to await both fetches
```

### 2. Fix CSV Export (10 minutes)
```bash
# Edit backend/app/routes/products.py
# Update the /csv endpoint to include ExtractedAttribute join
# Test with: curl "http://localhost:8000/api/products/csv?seller_id=1"
```

### 3. Fix Config (5 minutes)
```bash
# Edit backend/app/config.py
# Add extraction_backend, openai_api_key, fine_tuned_model_path fields

# Create backend/.env.example
# Update backend/.env with defaults
```

### 4. Update Processor (2 minutes)
```bash
# Edit backend/app/extraction/processor.py
# Line 41: Add model_path=settings.fine_tuned_model_path
```

---

## Validation: Run End-to-End Test

### Terminal 1: Start Backend
```bash
cd backend
python -m app.seed              # Populate DB with 8 test products
python -m app.main              # Start FastAPI server
```

**Expected Output:**
```
[OK] Created demo seller (id=1)
[OK] Added 8 sample products (total: 8)
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Terminal 2: Test Extraction API
```bash
# Start extraction
curl -X POST "http://localhost:8000/api/extract?seller_id=1"
# Response: {"job_id": "abc-123", "status": "pending"}

# Poll status (wait a few seconds)
curl "http://localhost:8000/api/jobs/abc-123"
# Response: {"job_id": "abc-123", "status": "completed", "progress": 100}

# Get extracted data
curl "http://localhost:8000/api/extracted?seller_id=1"
# Response should show extracted attributes like:
# {
#   "extracted": {
#     "seed_001": {"attributes": {"brand": "Nike", "size": "M", ...}, "confidence": 0.87},
#     "seed_002": {"attributes": {"brand": "FabIndia", "size": "Free Size", ...}, "confidence": 0.92},
#     ...
#   }
# }

# Download CSV
curl "http://localhost:8000/api/products/csv?seller_id=1" -o products.csv
cat products.csv  # Should include brand, size, color, material, category, confidence columns
```

### Terminal 3: Start Frontend
```bash
cd frontend
npm run dev
```

**Visit Browser:** `http://localhost:5173`

**Steps:**
1. Login page loads → Click "Demo Mode" (if implemented)
2. Dashboard shows 8 products in table
3. Click "Extract Attributes" button
4. Progress bar fills (should say 0% → 100%)
5. Extracted data appears in table (brand, color, size, etc.)
6. Confidence scores show with color coding (green for >0.85, yellow for 0.7-0.85, red for <0.7)
7. Click "Download CSV" → Check file contains attributes

---

## Success Criteria

- ✅ Dashboard fetches real extracted data from `/api/extracted`
- ✅ CSV export includes brand, color, size, material, category, confidence columns
- ✅ Config supports switching extraction backends (mock → GPT-4o → your VLM)
- ✅ End-to-end flow works: seed data → extract → display → download

---

## After These Fixes

You'll have:
1. ✅ Fully functional MVP (extraction pipeline works end-to-end)
2. ✅ Architecture ready for your fine-tuned VLM (swap in `local_vlm` backend anytime)
3. ✅ Test data to validate with (8 seed products)
4. ✅ A foundation to collect real seller feedback

**Next Phase:**
- Integrate your fine-tuned VLM (follow Part 3 of the implementation report)
- Deploy to production with PostgreSQL
- Start customer validation (the hardest part!)

