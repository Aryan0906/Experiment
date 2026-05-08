# Quick Reference: 45-Minute Path to Working MVP

Print this. Use it as a checklist.

---

## ⏱️ Timeline: 45 minutes to working end-to-end

```
0:00-0:05   Fix Dashboard (DashboardPage.tsx)
0:05-0:15   Fix CSV Export (products.py)
0:15-0:20   Fix Config (config.py + .env)
0:20-0:30   Run Backend & Seed Data
0:30-0:40   Start Frontend & Extract
0:40-0:45   Verify All Working
```

---

## Fix 1: Dashboard API Connection

**File:** `frontend/src/pages/DashboardPage.tsx`

**Find:** Lines 31-40 (the `fetchExtractedAttributes` function)

**Replace:**
```typescript
// OLD (mock data):
const fetchExtractedAttributes = () => {
    const mockExtracted: Record<string, ...> = {};
    products.forEach(p => {
        mockExtracted[p.id] = { ... }; // hardcoded mock
    });
    setExtracted(mockExtracted);
};

// NEW (real API):
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

**Also update useEffect (line 29):**
```typescript
// OLD:
useEffect(() => { Promise.resolve().then(() => fetchProducts()); }, []);

// NEW:
useEffect(() => { 
    Promise.resolve()
        .then(() => fetchProducts())
        .then(() => fetchExtractedAttributes()); 
}, []);
```

✅ **Time: 5 minutes**

---

## Fix 2: CSV Export with Attributes

**File:** `backend/app/routes/products.py`

**Find:** The `@router.get("/products/csv")` endpoint (around line 100+)

**Replace the entire function with:**

```python
@router.get("/products/csv")
def export_csv(seller_id: int, db: Session = Depends(get_db)):
    from app.models import ExtractedAttribute
    import io
    import csv
    
    products = db.query(Product).filter_by(seller_id=seller_id).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Headers with extracted attributes
    writer.writerow([
        "id", "title", "price", "sku", 
        "brand", "size", "color", "material", "category", "confidence"
    ])
    
    # Rows
    for product in products:
        # Get most recent extraction
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
            ])
        else:
            # No extraction yet
            writer.writerow([
                product.id, 
                product.title, 
                product.price, 
                product.sku,
                "", "", "", "", "", "",
            ])
    
    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment;filename=products.csv"}
    )
```

✅ **Time: 10 minutes**

---

## Fix 3: Configuration

**File:** `backend/app/config.py`

**Find:** The `Settings` class

**Replace with:**
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
    
    # VLM Extraction Settings ← NEW
    extraction_backend: str = os.getenv("EXTRACTION_BACKEND", "mock")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    fine_tuned_model_path: str = os.getenv("FINE_TUNED_MODEL_PATH", "")

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
```

**File:** `backend/.env`

**Add these lines:**
```env
# VLM Extraction Backend
EXTRACTION_BACKEND=mock
OPENAI_API_KEY=
FINE_TUNED_MODEL_PATH=
```

✅ **Time: 5 minutes**

---

## Bonus: Update Processor

**File:** `backend/app/extraction/processor.py`

**Find:** Lines 38-41

**Change from:**
```python
extractor = get_extractor(
    backend=settings.extraction_backend,
    api_key=settings.openai_api_key,
)
```

**Change to:**
```python
extractor = get_extractor(
    backend=settings.extraction_backend,
    api_key=settings.openai_api_key,
    model_path=settings.fine_tuned_model_path,  # ← Add this
)
```

✅ **Time: 2 minutes (optional, but recommended)**

---

## Testing: 25 minutes

### Terminal 1: Start Backend
```bash
cd backend

# Seed the database with 8 test products
python -m app.seed

# Expected:
# [OK] Created demo seller (id=1)
# [OK] Added 8 sample products (total: 8)

# Start the server
python -m app.main

# Expected:
# INFO:     Application startup complete
# Uvicorn running on http://0.0.0.0:8000
```

### Terminal 2: Test API
```bash
# Start an extraction job
curl -X POST "http://localhost:8000/api/extract?seller_id=1"

# Expected response:
# {"job_id":"abc-123","status":"pending"}

# Wait 5 seconds, then check status
curl "http://localhost:8000/api/jobs/abc-123"

# Expected:
# {"job_id":"abc-123","status":"completed","progress":100}

# Get extracted attributes
curl "http://localhost:8000/api/extracted?seller_id=1" | python -m json.tool

# Expected: JSON with extracted brand, size, color, etc.

# Download CSV
curl "http://localhost:8000/api/products/csv?seller_id=1" -o products.csv
cat products.csv

# Expected: CSV with columns including brand, size, color, material, category, confidence
```

### Terminal 3: Start Frontend
```bash
cd frontend
npm run dev

# Expected:
# Local:      http://localhost:5173
```

### Browser: Verify Dashboard
1. Go to http://localhost:5173
2. Click "Login" (or "Demo Mode" if you implemented it)
3. Should see 8 products in table
4. Click "Extract Attributes" button
5. Progress bar fills 0% → 100%
6. Table updates with brand, color, size, confidence for each product
7. Click "Download CSV"
8. Open products.csv → should have all attributes

✅ **All working = Success!**

---

## What Each Component Does

| Component | Role | Status |
|-----------|------|--------|
| **MockExtractor** | Returns instant fake but realistic attributes | ✅ Ready |
| **Backend API** | Accepts extraction requests, returns status + results | ✅ Ready |
| **Job Processor** | Runs extraction asynchronously | ✅ Ready |
| **Database** | Stores sellers, products, extraction results | ✅ Ready |
| **Dashboard** | Shows products + extracted attributes | ✅ Almost (was missing API call) |
| **CSV Export** | Downloads products with attributes | ✅ Almost (was missing attributes) |

---

## Switching Backends

### Currently Using Mock (Free, Instant)
```env
EXTRACTION_BACKEND=mock
```

### To Use GPT-4o Vision (Optional)
```env
EXTRACTION_BACKEND=gpt4v
OPENAI_API_KEY=sk-your-key-here
```
Cost: ~$0.01 per image

### To Use Your Fine-Tuned VLM (Future)
```env
EXTRACTION_BACKEND=local_vlm
FINE_TUNED_MODEL_PATH=/path/to/your/model_weights.pth
```
Cost: $0 (runs locally)

---

## If Something Breaks

### Error: "products.py" can't find ExtractedAttribute
**Fix:** Add this import at the top of the CSV function:
```python
from app.models import ExtractedAttribute
```

### Error: Dashboard shows no products
**Fix:** Make sure you ran `python -m app.seed` first

### Error: "DashboardPage.tsx" has syntax errors
**Fix:** Make sure you copied the exact TypeScript code from Fix 1

### Error: "API endpoint /api/extracted not found"
**Fix:** Make sure backend is running and you're using the right seller_id (should be 1 after seeding)

---

## Success Indicators

- ✅ Backend server starts without errors
- ✅ Frontend loads without 404s
- ✅ Seed command creates 8 products
- ✅ Extraction API returns job_id
- ✅ Job completes with status="completed"
- ✅ /api/extracted returns attributes
- ✅ Dashboard table shows brands, colors, sizes
- ✅ CSV includes attribute columns

If all 8 are true, you're done. Ship it.

---

## Next Steps After MVP Works

1. **Deploy Frontend** (Vercel, Netlify, etc.)
2. **Deploy Backend** (Railway, Render, AWS, etc.)
3. **Reach out to 5 sellers** (Uncanny CS network)
4. **Get feedback** (which attributes matter, any missing fields)
5. **Collect examples** (500+ labeled product images)
6. **Train your VLM** (transfer learning, weeks 7-8)
7. **Integrate** (swap backend, same code)
8. **Launch with 10-15 paying customers**

You have 6 months. You're on track.

---

## Final Checklist

- [ ] Fix 1: DashboardPage.tsx (5 min)
- [ ] Fix 2: products.py CSV (10 min)
- [ ] Fix 3: config.py + .env (5 min)
- [ ] Seed database (2 min)
- [ ] Start backend (1 min)
- [ ] Start frontend (1 min)
- [ ] Test extraction API (5 min)
- [ ] Verify dashboard (5 min)
- [ ] Download CSV and check (2 min)

**Total time: 36 minutes**  
**Buffer: 9 minutes for troubleshooting**  
**Total target: 45 minutes**

Go.

