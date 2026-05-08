# 🐛 BUG FIX: 307 Temporary Redirect Error

## Root Cause Analysis

### The Problem
```
INFO: GET /auth/shopify/authorize?shop=3tj1az-h6.myshopify.com HTTP/1.1" 307 Temporary Redirect
```

A **307 Temporary Redirect** means the backend IS responding but sending the response to the wrong place.

### Why It's Happening (5 Issues Found)

| Issue | Location | Problem | Impact |
|-------|----------|---------|--------|
| **Issue 1** | `auth.py` line 11 | Default shop parameter is wrong | OAuth URL has `myshop.myshopify.com` hardcoded as default |
| **Issue 2** | `auth.py` line 20-23 | OAuth URL format is incomplete | Missing `state` parameter (OAuth security requirement) |
| **Issue 3** | `config.py` line 10-12 | `SHOPIFY_REDIRECT_URI` points to port 3000 | Should point to localhost:8000 (backend), not frontend |
| **Issue 4** | `main.py` line 14 | No CORS enabled | Frontend (5173) can't call backend (8000) cross-origin |
| **Issue 5** | Frontend `.env` | `VITE_API_URL` not set | Frontend doesn't know backend URL |

---

## Fix Strategy (In Priority Order)

### Priority 1: Fix CORS (Blocks Frontend ↔ Backend Communication)
**File:** `backend/app/main.py`

**Problem:** Frontend runs on `http://localhost:5173`, backend on `http://localhost:8000`. Cross-origin requests blocked.

**Solution:** Add CORS middleware.

```python
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(...)

# Add CORS middleware BEFORE other routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### Priority 2: Fix OAuth Redirect URI
**File:** `backend/app/config.py`

**Problem:** `SHOPIFY_REDIRECT_URI` points to port 3000 (old config). OAuth callback should go to backend port 8000.

**Solution:** Change to backend callback endpoint.

```python
shopify_redirect_uri: str = os.getenv(
    "SHOPIFY_REDIRECT_URI", 
    "http://localhost:8000/auth/shopify/callback"  # ← Fixed
)
```

---

### Priority 3: Fix Auth Route (Remove Default Parameter)
**File:** `backend/app/routes/auth.py`

**Problem:** `authorize_shopify(shop: str = "myshop.myshopify.com")` has a hardcoded default.

**Solution:** Make `shop` required, not optional with a default.

```python
@router.get("/authorize")
async def authorize_shopify(shop: str) -> RedirectResponse:
    # shop must be provided by client
    if not shop:
        return {"error": "shop parameter is required"}
    ...
```

---

### Priority 4: Add OAuth Security Parameters
**File:** `backend/app/routes/auth.py`

**Problem:** Missing `state` and `nonce` parameters (OAuth 2.0 best practices).

**Solution:** Generate and store state token.

```python
import secrets
import base64

@router.get("/authorize")
async def authorize_shopify(
    shop: str,
    db: Session = Depends(get_db)
) -> RedirectResponse:
    """Generate OAuth state token and redirect to Shopify."""
    if not shop:
        return {"error": "shop parameter is required"}
    
    # Generate secure state token
    state = base64.b64encode(secrets.token_bytes(32)).decode()
    
    # Store in DB for verification during callback
    oauth_session = OAuthSession(shop=shop, state=state)
    db.add(oauth_session)
    db.commit()
    
    redirect_uri = settings.shopify_redirect_uri
    client_id = settings.shopify_api_key
    
    auth_url = (
        f"https://{shop}/admin/oauth/authorize?"
        f"client_id={client_id}"
        f"&scope=read_products,write_products,read_inventory"
        f"&redirect_uri={redirect_uri}"
        f"&state={state}"
    )
    
    return RedirectResponse(url=auth_url, status_code=302)
```

---

### Priority 5: Frontend Environment Setup
**File:** `frontend/.env`

**Problem:** `VITE_API_URL` not defined, so frontend doesn't know backend URL.

**Solution:** Create `.env` file.

```env
VITE_API_URL=http://localhost:8000
```

---

## The Fix (Step by Step)

### Step 1: Create Backend `.env`
```bash
cd backend
cat > .env << 'EOF'
DATABASE_URL=sqlite:///./test.db
SHOPIFY_API_KEY=test_key_do_not_use_in_production
SHOPIFY_API_SECRET=test_secret_do_not_use_in_production
SHOPIFY_REDIRECT_URI=http://localhost:8000/auth/shopify/callback
EOF
```

### Step 2: Create Frontend `.env`
```bash
cd frontend
cat > .env << 'EOF'
VITE_API_URL=http://localhost:8000
EOF
```

### Step 3: Apply Code Fixes (See Below)

### Step 4: Run Tests
```bash
cd backend
pytest tests/test_auth.py -v
```

### Step 5: Start Both Servers
```bash
# Terminal 1: Backend
cd backend
python -m uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

### Step 6: Test OAuth Flow
1. Open `http://localhost:5173/login`
2. Enter shop: `3tj1az-h6.myshopify.com`
3. Click "Connect Shopify Store"
4. Should redirect to Shopify consent screen (or mock in Sprint 1)
5. After consent, should redirect to `http://localhost:5173/dashboard`

---

## Files to Update

1. ✅ `backend/app/main.py` — Add CORS
2. ✅ `backend/app/config.py` — Fix redirect URI
3. ✅ `backend/app/routes/auth.py` — Fix OAuth flow
4. ✅ `backend/app/models.py` — Add OAuthSession model
5. ✅ `backend/.env` — Create with correct values
6. ✅ `frontend/.env` — Create with API URL
7. ✅ `backend/tests/test_auth.py` — Update tests

---

## Key Insight: Why 307 Happened

The 307 status code itself is NOT an error—it's the browser doing what the backend told it to do:

1. Frontend sends: `GET http://localhost:8000/auth/shopify/authorize?shop=...`
2. Backend responds: "307 Redirect to `https://3tj1az-h6.myshopify.com/admin/oauth/authorize?...`"
3. Browser follows: Tries to go to Shopify's OAuth screen
4. **But then fails** because:
   - CORS not enabled → frontend can't see the redirect
   - OR Shopify OAuth URL is malformed (missing `state`, wrong scope)
   - OR the actual Shopify store doesn't exist (test data)

**The fix:** Ensure OAuth URL is correct + CORS is enabled + test with real/mock Shopify data.

---

