# SPRINT 1 EXECUTION PLAN (May 14-28)

**Goal:** Working MVP by May 28 ready for 5 customer tests.  
**Constraint:** Full-time (~40 hrs/week), before internship starts May 25.

---

## 📁 PROJECT STRUCTURE (Create This Now)

```
catalog-sync/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app entry point
│   │   ├── config.py                  # Env variables (DB_URL, SHOPIFY_API_KEY, etc.)
│   │   ├── models.py                  # SQLAlchemy models (Seller, Product, ExtractedAttribute)
│   │   ├── database.py                # DB connection + session
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   └── shopify_oauth.py       # OAuth flow (authorize, callback, token refresh)
│   │   ├── shopify/
│   │   │   ├── __init__.py
│   │   │   ├── client.py              # Shopify API wrapper (fetch products)
│   │   │   └── models.py              # Shopify data models
│   │   ├── extraction/
│   │   │   ├── __init__.py
│   │   │   ├── vlm.py                 # VLM inference logic
│   │   │   ├── jobs.py                # Async job management (Celery or FastAPI background)
│   │   │   └── processor.py           # VLM processor (image + description → attributes)
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── auth.py                # POST /auth/shopify/authorize, /callback
│   │       ├── products.py            # GET /api/products, POST /api/extract, GET /api/jobs
│   │       └── export.py              # GET /api/products/csv
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_auth.py               # OAuth tests
│   │   ├── test_shopify_client.py     # Shopify API tests
│   │   ├── test_vlm.py                # VLM extraction tests
│   │   └── test_api.py                # Route tests
│   ├── .env.example
│   ├── requirements.txt
│   ├── Dockerfile
│   └── pytest.ini
│
├── frontend/
│   ├── src/
│   │   ├── index.tsx
│   │   ├── App.tsx                    # Main app (router, auth context)
│   │   ├── pages/
│   │   │   ├── LoginPage.tsx          # OAuth login button
│   │   │   └── DashboardPage.tsx      # Products table, extract button, CSV download
│   │   ├── components/
│   │   │   ├── ProductTable.tsx       # Displays products + attributes
│   │   │   ├── ExtractButton.tsx      # Triggers extraction + polls job status
│   │   │   └── CSVDownload.tsx        # Download CSV button
│   │   ├── api.ts                     # API client (fetch, POST, etc.)
│   │   ├── types.ts                   # TypeScript interfaces (Seller, Product, Attribute)
│   │   └── styles/
│   │       └── globals.css            # TailwindCSS
│   ├── tests/
│   │   ├── App.test.tsx
│   │   └── components/
│   │       └── ProductTable.test.tsx
│   ├── package.json
│   ├── tsconfig.json
│   ├── vercel.json
│   └── .env.example
│
└── README.md
```

---

## 📅 WEEK 1 (May 14-20) — AUTH + PRODUCT FETCH

### Task 1.1: Backend Setup (Mon-Tue, 1 day)
**Goal:** FastAPI running, DB connected, OAuth skeleton in place.

**Checklist:**
- [ ] Create `backend/` with FastAPI app
- [ ] Set up PostgreSQL on Render (create account if needed)
- [ ] Create `.env` with: `DATABASE_URL`, `SHOPIFY_API_KEY`, `SHOPIFY_API_SECRET`, `SHOPIFY_REDIRECT_URI`
- [ ] Set up SQLAlchemy models: `Seller`, `Product`, `ExtractedAttribute`
- [ ] Run migrations (Alembic)
- [ ] Test DB connection: `python -c "from app.database import SessionLocal; db = SessionLocal(); print('OK')"`

**Test:**
```python
def test_db_connection():
    db = SessionLocal()
    assert db is not None
    db.close()
```

---

### Task 1.2: Shopify OAuth (Tue-Wed, 1.5 days)
**Goal:** Seller can log in with Shopify, token stored in DB.

**Routes:**
- `GET /auth/shopify/authorize` → redirects to Shopify OAuth
- `GET /auth/shopify/callback` → handles OAuth response, stores token

**Models:**
```python
class Seller(Base):
    __tablename__ = "sellers"
    id = Column(Integer, primary_key=True)
    shop = Column(String, unique=True)  # e.g., "myshop.myshopify.com"
    access_token = Column(String)  # Encrypted
    refresh_token = Column(String)  # Encrypted
    created_at = Column(DateTime, default=datetime.utcnow)
```

**Test:**
```python
def test_shopify_oauth_callback():
    # Simulate OAuth callback
    response = client.get(
        "/auth/shopify/callback",
        params={"code": "test_code", "shop": "myshop.myshopify.com"}
    )
    assert response.status_code == 200
    seller = db.query(Seller).filter_by(shop="myshop.myshopify.com").first()
    assert seller.access_token is not None
```

---

### Task 1.3: Fetch Shopify Products (Wed-Thu, 1.5 days)
**Goal:** API endpoint that pulls seller's products from Shopify.

**Route:** `GET /api/products?limit=50&offset=0`  
**Response:**
```json
{
  "products": [
    {
      "id": "123",
      "title": "Blue T-Shirt",
      "image_url": "https://...",
      "description": "100% cotton...",
      "price": "₹500",
      "sku": "SKU-123"
    }
  ],
  "total": 200
}
```

**Test:**
```python
def test_fetch_products():
    response = client.get("/api/products?limit=50")
    assert response.status_code == 200
    data = response.json()
    assert "products" in data
    assert len(data["products"]) <= 50
    assert all(p["id"] and p["title"] for p in data["products"])
```

---

### Task 1.4: Frontend Login + Product List (Thu-Fri, 1.5 days)
**Goal:** React app with OAuth button and product table.

**Pages:**
1. `LoginPage.tsx` → "Connect Shopify" button → redirects to backend OAuth
2. `DashboardPage.tsx` → After auth, shows product table

**Components:**
```typescript
// LoginPage.tsx
export const LoginPage = () => {
  const handleAuth = () => {
    window.location.href = `${API_URL}/auth/shopify/authorize`;
  };
  return <button onClick={handleAuth}>Connect Shopify</button>;
};

// DashboardPage.tsx
export const DashboardPage = () => {
  const [products, setProducts] = useState([]);
  
  useEffect(() => {
    fetch(`${API_URL}/api/products`)
      .then(r => r.json())
      .then(d => setProducts(d.products));
  }, []);
  
  return <ProductTable products={products} />;
};
```

**Test:**
```typescript
test('LoginPage renders connect button', () => {
  render(<LoginPage />);
  expect(screen.getByText('Connect Shopify')).toBeInTheDocument();
});

test('DashboardPage fetches products', async () => {
  render(<DashboardPage />);
  await waitFor(() => {
    expect(screen.getByText('Blue T-Shirt')).toBeInTheDocument();
  });
});
```

---

## 📅 WEEK 2 (May 21-28) — VLM INTEGRATION + CSV EXPORT

### Task 2.1: VLM Inference Setup (Mon-Tue, 1.5 days)
**Goal:** VLM can extract attributes from a Shopify product image.

**File:** `backend/app/extraction/vlm.py`

```python
# Pseudo-code
class AttributeExtractor:
    def __init__(self, model_path):
        self.model = load_model(model_path)  # Your fine-tuned VLM
    
    def extract(self, image_url: str, description: str) -> dict:
        """
        Input: Shopify product image + description
        Output: {
          "brand": "Nike",
          "size": "M",
          "color": "Blue",
          "material": "Cotton",
          "category": "T-Shirt",
          "confidence": 0.92
        }
        """
        image = fetch_image(image_url)
        prompt = f"Extract attributes from this product: {description}"
        output = self.model.generate(image, prompt)
        return parse_output(output)
```

**Test:**
```python
def test_vlm_extraction():
    extractor = AttributeExtractor("path/to/model")
    result = extractor.extract(
        image_url="https://example.com/image.jpg",
        description="Blue cotton t-shirt"
    )
    assert result["brand"]
    assert 0 < result["confidence"] <= 1
    assert result["color"] == "Blue"
```

**Kill Switch:** If inference takes >10 sec per product, optimize model or switch to GPT-4o Vision.

---

### Task 2.2: Async Extraction Jobs (Tue-Wed, 1.5 days)
**Goal:** User clicks "Extract" → backend processes all products asynchronously.

**Route:** `POST /api/extract` → creates job, returns job_id

**Job Management:**
```python
class ExtractionJob(Base):
    __tablename__ = "extraction_jobs"
    id = Column(String, primary_key=True)  # UUID
    seller_id = Column(Integer, ForeignKey("sellers.id"))
    status = Column(String)  # "pending", "processing", "completed", "failed"
    progress = Column(Integer)  # 0-100
    created_at = Column(DateTime)

# API
@app.post("/api/extract")
def start_extraction(seller_id: int):
    job = ExtractionJob(seller_id=seller_id, status="pending")
    db.add(job)
    db.commit()
    
    # Queue job (Celery or FastAPI background)
    process_extraction.delay(job.id)  # Celery
    
    return {"job_id": job.id, "status": "pending"}

@app.get("/api/jobs/{job_id}")
def get_job_status(job_id: str):
    job = db.query(ExtractionJob).filter_by(id=job_id).first()
    return {
        "id": job.id,
        "status": job.status,
        "progress": job.progress,
        "message": "Extracting attributes..."
    }
```

**Test:**
```python
def test_extract_job_creation():
    response = client.post("/api/extract", json={"seller_id": 1})
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    
    # Poll job
    status = client.get(f"/api/jobs/{data['job_id']}")
    assert status.json()["status"] in ["pending", "processing", "completed"]
```

---

### Task 2.3: Store Extracted Attributes (Wed, 0.5 days)
**Goal:** Save extracted attributes to PostgreSQL.

**Model:**
```python
class ExtractedAttribute(Base):
    __tablename__ = "extracted_attributes"
    id = Column(Integer, primary_key=True)
    product_id = Column(String, ForeignKey("products.id"))
    job_id = Column(String, ForeignKey("extraction_jobs.id"))
    attributes = Column(JSON)  # {"brand": "Nike", "size": "M", ...}
    confidence = Column(Float)
    created_at = Column(DateTime)
```

**In `process_extraction` job:**
```python
def process_extraction(job_id: str):
    job = db.query(ExtractionJob).filter_by(id=job_id).first()
    job.status = "processing"
    db.commit()
    
    seller = job.seller
    products = db.query(Product).filter_by(seller_id=seller.id).all()
    
    for i, product in enumerate(products):
        attrs = extractor.extract(product.image_url, product.description)
        
        extracted = ExtractedAttribute(
            product_id=product.id,
            job_id=job_id,
            attributes=attrs,
            confidence=attrs["confidence"]
        )
        db.add(extracted)
        
        job.progress = int((i / len(products)) * 100)
        db.commit()
    
    job.status = "completed"
    db.commit()
```

---

### Task 2.4: React Dashboard + Extract Button (Thu, 1 day)
**Goal:** Product table with "Extract" button, status polling, attribute display.

**Components:**
```typescript
// ExtractButton.tsx
const ExtractButton = ({ sellerId, onComplete }) => {
  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState("idle");
  const [progress, setProgress] = useState(0);
  
  const handleExtract = async () => {
    const res = await fetch(`${API_URL}/api/extract`, {
      method: "POST",
      body: JSON.stringify({ seller_id: sellerId })
    });
    const data = await res.json();
    setJobId(data.job_id);
    
    // Poll job status
    const interval = setInterval(async () => {
      const statusRes = await fetch(`${API_URL}/api/jobs/${data.job_id}`);
      const statusData = await statusRes.json();
      setStatus(statusData.status);
      setProgress(statusData.progress);
      
      if (statusData.status === "completed") {
        clearInterval(interval);
        onComplete();
      }
    }, 2000);
  };
  
  return (
    <>
      <button onClick={handleExtract} disabled={status === "processing"}>
        {status === "processing" ? `Extracting... ${progress}%` : "Extract Attributes"}
      </button>
    </>
  );
};

// ProductTable.tsx (updated)
const ProductTable = ({ products, extracted }) => {
  return (
    <table>
      <thead>
        <tr>
          <th>Image</th>
          <th>Title</th>
          <th>Extracted Attributes</th>
          <th>Confidence</th>
        </tr>
      </thead>
      <tbody>
        {products.map(p => (
          <tr key={p.id}>
            <td><img src={p.image_url} width={50} /></td>
            <td>{p.title}</td>
            <td>
              {extracted[p.id] ? (
                <pre>{JSON.stringify(extracted[p.id].attributes, null, 2)}</pre>
              ) : (
                "Not extracted yet"
              )}
            </td>
            <td>
              {extracted[p.id]?.confidence ? 
                (extracted[p.id].confidence * 100).toFixed(0) + "%" : 
                "-"
              }
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};
```

**Test:**
```typescript
test('Extract button starts extraction job', async () => {
  const mockOnComplete = jest.fn();
  render(<ExtractButton sellerId={1} onComplete={mockOnComplete} />);
  
  fireEvent.click(screen.getByText('Extract Attributes'));
  
  await waitFor(() => {
    expect(screen.getByText(/Extracting/)).toBeInTheDocument();
  });
});
```

---

### Task 2.5: CSV Export (Fri, 0.5 days)
**Goal:** Download extracted attributes as CSV.

**Route:** `GET /api/products/csv`

```python
@app.get("/api/products/csv")
def export_csv(seller_id: int):
    products = db.query(Product).filter_by(seller_id=seller_id).all()
    extracted = db.query(ExtractedAttribute).filter(
        ExtractedAttribute.product_id.in_([p.id for p in products])
    ).all()
    
    # Build CSV
    import csv
    import io
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["product_id", "title", "brand", "color", "size", "material", "category", "price"]
    )
    writer.writeheader()
    
    for product in products:
        attr = next((a for a in extracted if a.product_id == product.id), None)
        if attr:
            writer.writerow({
                "product_id": product.id,
                "title": product.title,
                "brand": attr.attributes.get("brand", ""),
                "color": attr.attributes.get("color", ""),
                "size": attr.attributes.get("size", ""),
                "material": attr.attributes.get("material", ""),
                "category": attr.attributes.get("category", ""),
                "price": product.price
            })
    
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=catalog.csv"}
    )
```

**React:**
```typescript
// CSVDownload.tsx
const CSVDownload = ({ sellerId }) => {
  const handleDownload = async () => {
    const res = await fetch(`${API_URL}/api/products/csv?seller_id=${sellerId}`);
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `catalog_${Date.now()}.csv`;
    a.click();
  };
  
  return <button onClick={handleDownload}>Download CSV</button>;
};
```

---

## ✅ DEFINITION OF DONE (By May 28)

- [ ] OAuth login works (tested with real Shopify store)
- [ ] Can fetch 50+ products from Shopify
- [ ] VLM extracts attributes on real product data
- [ ] Extraction job completes in <2 min for 50 products
- [ ] React dashboard shows products + extracted attributes
- [ ] CSV downloads correctly
- [ ] All tests pass (pytest + npm test)
- [ ] No dead code, no console errors
- [ ] Deployed to Render (backend) + Vercel (frontend)
- [ ] Can show this to 5 sellers and ask "Would you pay $200/month?"

---

## 🎯 SUCCESS METRICS (May 28-June 4)

**Phase 1.5 Validation:**
- [ ] 5 Shopify sellers can log in and test it
- [ ] ≥3/5 say "This extracted my attributes correctly"
- [ ] ≥3/5 say "I would use this"
- [ ] ≥50% would pay $200/month
- [ ] Average extraction accuracy ≥80%

**If any metric fails:** Pivot or kill per kill switches in MVP brief.

---

