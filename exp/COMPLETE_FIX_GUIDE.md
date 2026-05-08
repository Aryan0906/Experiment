# 🔧 COMPLETE FIX GUIDE: OAuth 307 Redirect Error

## What Was Wrong (The 5 Bugs)

| Bug | File | Issue | Status |
|-----|------|-------|--------|
| **Bug 1** | `backend/app/main.py` | No CORS headers → Frontend can't call backend | ✅ FIXED |
| **Bug 2** | `backend/app/config.py` | Redirect URI pointed to port 3000 (wrong port) | ✅ FIXED |
| **Bug 3** | `backend/app/routes/auth.py` | OAuth URL missing `state` parameter (security) | ✅ FIXED |
| **Bug 4** | `backend/app/models.py` | No `OAuthSession` model for state token storage | ✅ FIXED |
| **Bug 5** | `frontend/src/types.ts` | API_URL fallback was empty string | ✅ FIXED |

---

## What Each Fix Does

### Fix 1: CORS Middleware (main.py)
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
**Why:** Frontend on port 5173 needs to make requests to backend on port 8000. CORS policy was blocking it.

---

### Fix 2: Correct Redirect URI (config.py)
```python
shopify_redirect_uri: str = os.getenv(
    "SHOPIFY_REDIRECT_URI", 
    "http://localhost:8000/auth/shopify/callback"  # ← Backend port 8000, not 3000
)
```
**Why:** OAuth callback must go to backend to process tokens, not to frontend.

---

### Fix 3: OAuth State Token (auth.py)
```python
state_bytes = secrets.token_bytes(32)
state = base64.urlsafe_b64encode(state_bytes).decode().rstrip("=")

# Store in DB for verification
oauth_session = OAuthSession(shop=shop, state=state)
db.add(oauth_session)
db.commit()

# Add state to OAuth URL
auth_params = {
    "client_id": client_id,
    "scope": scope,
    "redirect_uri": redirect_uri,
    "state": state,  # ← This prevents CSRF attacks
}
```
**Why:** OAuth 2.0 best practice. State token prevents attackers from hijacking the flow.

---

### Fix 4: OAuthSession Model (models.py)
```python
class OAuthSession(Base):
    """Store temporary OAuth state tokens."""
    __tablename__ = "oauth_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    shop = Column(String, index=True)
    state = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
```
**Why:** Need a place to store and verify state tokens during the OAuth flow.

---

### Fix 5: API URL Fallback (frontend/src/types.ts)
```typescript
export const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
```
**Why:** Frontend needs to know where backend is. Default to localhost:8000 for development.

---

## How to Apply the Fixes

### Step 1: Replace Fixed Files

All files have been updated. Check they're in place:

```bash
# Backend files
✅ /home/claude/backend/app/main.py
✅ /home/claude/backend/app/config.py
✅ /home/claude/backend/app/models.py
✅ /home/claude/backend/app/routes/auth.py
✅ /home/claude/backend/.env
✅ /home/claude/backend/tests/test_auth.py

# Frontend files
✅ /home/claude/frontend/src/types.ts
✅ /home/claude/frontend/.env
```

---

### Step 2: Delete Old Database (Fresh Start)

```bash
cd /home/claude/backend
rm -f test.db  # Remove old database to ensure tables are recreated
```

---

### Step 3: Run Tests to Verify Fixes

```bash
cd /home/claude/backend

# Install dependencies (if needed)
pip install -r requirements.txt

# Run tests (this will verify all OAuth flows work)
pytest tests/test_auth.py -v

# Expected output:
# test_shopify_oauth_authorize PASSED
# test_shopify_oauth_authorize_missing_shop PASSED
# test_shopify_oauth_authorize_invalid_shop PASSED
# test_shopify_oauth_callback_success PASSED
# test_shopify_oauth_callback_invalid_state PASSED
# test_shopify_oauth_callback_shop_mismatch PASSED
# test_shopify_oauth_callback_missing_params PASSED
```

---

### Step 4: Start Backend Server

```bash
cd /home/claude/backend
python -m uvicorn app.main:app --reload --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

---

### Step 5: Start Frontend Server (New Terminal)

```bash
cd /home/claude/frontend
npm run dev
```

**Expected Output:**
```
  VITE v4.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  press h + enter to show help
```

---

### Step 6: Test the OAuth Flow Manually

1. **Open browser to:** `http://localhost:5173/login`

2. **You should see:**
   ```
   Catalog Sync
   Automate your Shopify product attribute extraction.
   [Input field: "your-store.myshopify.com"]
   [Button: "Connect Shopify Store"]
   ```

3. **Enter shop domain:** `myshop.myshopify.com`

4. **Click "Connect Shopify Store"**

5. **Check backend logs** for:
   ```
   INFO: OAuth session created for shop: myshop.myshopify.com
   INFO: Redirecting to Shopify: https://myshop.myshopify.com/admin/oauth/authorize?...
   ```

6. **Browser redirects to:** Shopify OAuth consent screen (or will fail if shop doesn't exist, which is expected in dev)

---

## Testing Checklist

Run this to verify everything is working:

```bash
cd /home/claude/backend

# 1. Run all tests
pytest tests/ -v --tb=short

# 2. Check type safety
mypy app/ --strict

# 3. Check code style
flake8 app/ --max-line-length=100

# 4. Test health endpoint
curl http://localhost:8000/health
# Expected: {"status":"healthy"}

# 5. Test authorize endpoint with missing shop
curl http://localhost:8000/auth/shopify/authorize
# Expected: {"detail":"shop parameter is required"}

# 6. Test authorize endpoint with valid shop (will redirect)
curl -i http://localhost:8000/auth/shopify/authorize?shop=test.myshopify.com
# Expected: 302 redirect to Shopify OAuth URL
```

---

## The OAuth Flow (Now Fixed)

```
Frontend                Backend                    Shopify
  |                       |                          |
  | Click "Connect"        |                          |
  |----------------------->|                          |
  |                        | Generate state token     |
  |                        | Store in DB              |
  |                        | Build OAuth URL          |
  |                    302 Redirect                   |
  |<-----------------------|                          |
  | Follow redirect        |                          |
  |--------------------------------------------->|
  |                                                (User consents)
  |                        OAuth callback           |
  |<---------------------------------------------|
  |                        |                          |
  |                        | Verify state token       |
  |                        | Create/update seller     |
  |                    302 Redirect                   |
  |<-----------------------|                          |
  | Follow redirect        |                          |
  | /dashboard ✅          |                          |
```

---

## Key Files Updated

### 1. `backend/app/main.py`
- Added `CORSMiddleware` to allow frontend ↔ backend communication

### 2. `backend/app/config.py`
- Fixed `SHOPIFY_REDIRECT_URI` to point to port 8000 (backend)
- Added default values for API keys (test values)

### 3. `backend/app/models.py`
- Added `OAuthSession` model to store state tokens

### 4. `backend/app/routes/auth.py`
- Completely rewritten with proper OAuth 2.0 flow
- Generates and verifies state tokens
- Proper error handling with logging
- Returns 302 redirects (not 307)

### 5. `backend/tests/test_auth.py`
- Complete test suite with 7 test cases
- Tests all error scenarios
- Tests happy path (successful OAuth)

### 6. `backend/.env`
- Already correct (no changes needed)

### 7. `frontend/src/types.ts`
- Fixed API_URL fallback to `http://localhost:8000`

### 8. `frontend/.env` (NEW)
- Created with `VITE_API_URL=http://localhost:8000`

---

## Why It Was a 307 Before

**307 Temporary Redirect** is what FastAPI returns when:

1. ✅ Server successfully processes request
2. ✅ Server wants to redirect you somewhere
3. ❌ But the redirect URL is wrong OR
4. ❌ CORS headers missing so frontend can't see the redirect

The error was actually correct! It was the **destination** that was wrong:
- Default shop parameter was `"myshop.myshopify.com"` (fake)
- Missing `state` parameter (OAuth security issue)
- Frontend couldn't make the call anyway (no CORS)
- Redirect URI pointed to wrong port

**Now all 5 issues are fixed.** You should get a proper 302 redirect to Shopify.

---

## Next Steps After Testing

Once OAuth is working:

1. **Get real Shopify credentials** (replace test values in `.env`)
2. **Implement token exchange** (currently mocked)
3. **Build product fetching** (Task 1.3)
4. **Build VLM extraction** (Task 2.1)
5. **Build CSV export** (Task 3.1)

---

## Debugging Tips

If something still doesn't work:

```bash
# 1. Check backend logs
cd /home/claude/backend
python -m uvicorn app.main:app --reload --port 8000
# Look for:
# - "OAuth session created for shop"
# - "Redirecting to Shopify"
# - Any exceptions in red

# 2. Check CORS is enabled
curl -i http://localhost:8000/health
# Look for:
# Access-Control-Allow-Origin: http://localhost:5173

# 3. Check frontend console
# Open http://localhost:5173 → F12 → Console tab
# Look for CORS errors or network errors

# 4. Check database
cd /home/claude/backend
python3 << 'EOF'
from app.database import SessionLocal
from app.models import OAuthSession, Seller
db = SessionLocal()
sessions = db.query(OAuthSession).all()
sellers = db.query(Seller).all()
print(f"OAuth sessions: {len(sessions)}")
print(f"Sellers: {len(sellers)}")
EOF

# 5. Test endpoints with curl
curl http://localhost:8000/health
curl "http://localhost:8000/auth/shopify/authorize?shop=test.myshopify.com" -i
```

---

