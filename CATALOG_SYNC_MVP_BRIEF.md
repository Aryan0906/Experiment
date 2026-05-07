# CATALOG SYNC MVP — COMPACT BRIEF

**Project:** Shopify Product Attribute Extraction Tool  
**Timeline:** Sprint 1 (May 14-28) = Validation MVP  
**Goal:** "Take Shopify store → Extract attributes with VLM → Output CSV"  
**Success:** 5 sellers test it, ≥3 say "this works, I'd pay"

---

## 📚 UBIQUITOUS LANGUAGE (DDD Terms)

| Term | Definition | Example |
|------|-----------|---------|
| **Seller** | A user who owns a Shopify store | "seller@abc.com" |
| **Store** | A Shopify store (accessed via OAuth) | "myshop.myshopify.com" |
| **Product** | A Shopify product with variants, images, descriptions | "Blue Cotton T-Shirt" |
| **Attribute** | Structured metadata extracted from product | brand="Cotton Co", size="M", color="Blue" |
| **Extraction Job** | Async task: "VLM, extract attributes from this product" | Job ID: ex_12345 |
| **Attribute Schema** | The set of allowed attributes for a given marketplace | Amazon schema: {brand, color, size, material, ...} |
| **CSV Output** | Seller's extracted products in downloadable CSV format | seller_12345_products.csv |

---

## 🎯 MVP FEATURE SET (Zero Scope Creep)

### ✅ Phase 1 (May 14-28) — MUST HAVE
1. **Shopify OAuth** → Seller logs in with Shopify account
2. **Fetch products** → Pull seller's products (title, description, image URL) via Shopify API
3. **VLM extraction** → Fine-tuned VLM extracts attributes (brand, size, color, material, category, price, description)
4. **Store results** → Save extracted attributes to PostgreSQL
5. **CSV export** → Download results as CSV (product_id, title, extracted_attributes)
6. **React dashboard** → Simple table showing: Product | Image | Extracted Attrs | Confidence

### ❌ Phase 1 (DO NOT BUILD YET)
- Multi-marketplace schema mapping (Amazon, Flipkart schemas)
- Auto-sync to marketplaces
- Inventory management
- Order management
- Payment/billing system
- Email notifications

### ⚠️ Phase 2 (June onwards) — NICE TO HAVE
- Marketplace schema selection (Amazon, Flipkart, Meesho)
- One-click CSV → Amazon upload
- Recurring sync (daily/weekly inventory updates)
- Accuracy feedback loop (seller corrects attributes, retrains model)

---

## 📋 SPRINT 1 USER STORIES

### Story 1: Shopify OAuth Login
**As a** Shopify seller  
**I want to** authorize my store with one click  
**So that** I don't have to manually enter API keys  

**Acceptance Criteria:**
- [ ] User clicks "Connect Shopify Store"
- [ ] Redirected to Shopify OAuth consent screen
- [ ] After consent, token stored in PostgreSQL (encrypted)
- [ ] User returned to dashboard showing "Connected: myshop.myshopify.com"
- [ ] Token refreshes automatically before expiry

**Test Contract:**
```python
def test_shopify_oauth_flow():
    # Given: User at login page
    # When: User clicks "Connect Shopify"
    # Then: Redirect to Shopify OAuth
    # And: After consent, seller_id + refresh_token in DB
    # And: Cookie set for future requests
    assert response.status_code == 302
    assert "myshopify.com" in response.location
```

---

### Story 2: Fetch Shopify Products
**As a** Shopify seller  
**I want to** see my products loaded from Shopify  
**So that** I can verify the extraction works on real data  

**Acceptance Criteria:**
- [ ] Dashboard fetches all products from Shopify API (paginated)
- [ ] Shows: Product image, title, description, SKU, current price
- [ ] Handles >100 products (pagination)
- [ ] Displays load time (goal: <3 sec for 50 products)
- [ ] Error handling: If API fails, show user-friendly message

**Test Contract:**
```python
def test_fetch_shopify_products():
    # Given: Seller with OAuth token
    # When: GET /api/products
    # Then: Response contains list of products
    # And: Each product has {id, title, image_url, description, price}
    # And: Pagination works (limit=50, offset=0)
    assert len(products) > 0
    assert all(p["id"] and p["title"] and p["image_url"] for p in products)
```

---

### Story 3: VLM Attribute Extraction (Async Job)
**As a** Shopify seller  
**I want to** extract product attributes automatically  
**So that** I don't have to manually enter them for each SKU  

**Acceptance Criteria:**
- [ ] User clicks "Extract Attributes" button
- [ ] Backend creates async job (Celery or FastAPI background task)
- [ ] VLM processes product image + description → outputs JSON attributes
- [ ] Results saved to PostgreSQL (product_id, extracted_attributes, confidence_score, timestamp)
- [ ] Dashboard polls job status, updates table as results arrive
- [ ] Extraction completes for 50 products in <2 min (cached)

**Test Contract:**
```python
def test_vlm_extraction():
    # Given: Product with image + description
    # When: VLM processes it
    # Then: Returns JSON with attributes
    # Sample output: {
    #   "brand": "Nike",
    #   "size": "M",
    #   "color": "Blue",
    #   "material": "Cotton",
    #   "category": "T-Shirt",
    #   "confidence": 0.92
    # }
    assert output["brand"]
    assert 0 < output["confidence"] <= 1
```

---

### Story 4: Display Extracted Attributes (React Dashboard)
**As a** Shopify seller  
**I want to** review extracted attributes in a clean table  
**So that** I can verify accuracy before downloading  

**Acceptance Criteria:**
- [ ] Table shows: Product Image | Title | Extracted Attributes | Confidence Score
- [ ] Attributes shown as key-value pairs or editable fields
- [ ] Color-code confidence (green >0.85, yellow 0.7-0.85, red <0.7)
- [ ] Can filter by confidence threshold
- [ ] Can manually edit attributes inline (prep for phase 2 feedback loop)

**Test Contract:**
```javascript
// React component test
test('displays extracted attributes table', () => {
  const mockData = [{
    id: '123',
    image_url: 'https://...',
    title: 'Blue T-Shirt',
    attributes: { brand: 'Nike', color: 'Blue', size: 'M' },
    confidence: 0.92
  }];
  
  render(<AttributeTable data={mockData} />);
  
  expect(screen.getByText('Nike')).toBeInTheDocument();
  expect(screen.getByText('0.92')).toBeInTheDocument();
});
```

---

### Story 5: CSV Export
**As a** Shopify seller  
**I want to** download extracted attributes as CSV  
**So that** I can upload to Amazon/Flipkart manually (Phase 1)  

**Acceptance Criteria:**
- [ ] "Download CSV" button on dashboard
- [ ] CSV includes: product_id, title, brand, size, color, material, category, price, description
- [ ] CSV is properly escaped (handles quotes, newlines)
- [ ] File named: `catalog_extraction_{timestamp}.csv`
- [ ] CSV valid for 5 marketplaces (column order doesn't matter yet)

**Test Contract:**
```python
def test_csv_export():
    # Given: 50 extracted products
    # When: User clicks "Download CSV"
    # Then: Returns CSV with all attributes
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'text/csv'
    assert 'product_id' in csv_content
    assert len(csv_lines) == 51  # 50 products + header
```

---

## 🏗️ ARCHITECTURE (High Level)

```
┌─────────────────────────────────────────────────────────────┐
│                    REACT FRONTEND (Vercel)                   │
│  Dashboard → OAuth → Product List → Extract Button → CSV DL  │
└────────────────────┬────────────────────────────────────────┘
                     │ (API calls)
┌────────────────────▼────────────────────────────────────────┐
│                  FASTAPI (Render)                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ POST /auth/shopify/callback → OAuth token handling   │   │
│  │ GET /api/products → Fetch from Shopify API           │   │
│  │ POST /api/extract → Create async extraction job      │   │
│  │ GET /api/jobs/{id} → Poll job status                 │   │
│  │ GET /api/products/csv → Download CSV                 │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
    ┌───▼───┐   ┌───▼───┐   ┌───▼───┐
    │ PG    │   │ VLM   │   │Shopify│
    │ DB    │   │Model  │   │ API   │
    │Render │   │Render │   │       │
    └───────┘   └───────┘   └───────┘
```

---

## 🔧 TECH STACK (Locked)

| Layer | Tech | Rationale |
|-------|------|-----------|
| Frontend | React 19 + TypeScript + TailwindCSS | Fast, simple, works on Vercel |
| Backend | FastAPI | Async-first, perfect for long-running VLM inference |
| ORM | SQLAlchemy (Django ORM not needed yet) | Type-safe, async-compatible |
| Database | PostgreSQL on Render | Managed, reliable, scales easily |
| VLM | Fine-tuned lightweight model (local weights) | Your research, inference on Render |
| Auth | Shopify OAuth2 | Industry standard, no API keys exposed |
| Async Tasks | Celery + Redis OR FastAPI background tasks | Queue extraction jobs |
| Hosting | Render (backend) + Vercel (frontend) | Free tier works, easy deployment |

---

## 📅 SPRINT 1 TIMELINE (May 14-28, 2 weeks)

| Week | Goal | Deliverable |
|------|------|-----------|
| **May 14-20** | Auth + Product Fetch | OAuth working, can pull Shopify products |
| **May 21-24** | VLM Integration | Extraction runs, saves to DB |
| **May 25-28** | UI + CSV Export + Testing | Dashboard works, CSV downloads, ready to test with 5 sellers |

---

## ✅ DEFINITION OF DONE (Per User Story)

For EVERY story:
- [ ] Unit tests written BEFORE code (TDD red-green-refactor)
- [ ] Code reviewed (self-review counts, explain why)
- [ ] Deployed to Render/Vercel staging
- [ ] Manually tested with real Shopify store (if applicable)
- [ ] No dead code, no commented-out blocks
- [ ] Error handling: what happens if Shopify API fails? VLM times out?
- [ ] Logging: can you debug issues in production?

---

## 🚨 KILL SWITCHES (Sprint 1)

| Signal | Action |
|--------|--------|
| OAuth integration doesn't work by May 17 | Stop. Rethink auth approach (API key backup?) |
| VLM inference takes >10 sec per product | Optimize model or switch to GPT-4o Vision |
| Can't run extraction on Render (memory/timeout) | Run inference locally, save results async |
| React dashboard too slow to load 50 products | Virtualize table, lazy-load images |

---

## 📤 DELIVERABLE (May 28)

A working MVP where:
1. ✅ Seller logs in with Shopify OAuth
2. ✅ Sees 50 of their products in a table
3. ✅ Clicks "Extract" → attributes appear in 2 minutes
4. ✅ Downloads CSV
5. ✅ Can show this to real sellers and ask "Would you pay $200/month?"

---

## 📌 DO NOT BUILD (Explicit Scope Boundaries)

- ❌ Multi-marketplace schema mapping (Phase 2)
- ❌ Auto-sync to Amazon/Flipkart (Phase 2)
- ❌ Payment/billing (post-MVP)
- ❌ Email notifications (post-MVP)
- ❌ User profiles, teams, workspaces (post-MVP)
- ❌ Mobile app (post-MVP)
- ❌ Inventory sync (Phase 2)

**If you find yourself building anything above, STOP. Ask first.**

