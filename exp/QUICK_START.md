# 🚀 QUICK START: Fix & Run Your OAuth Flow

## What's Been Fixed (5 Bugs) ✅

| # | Problem | Solution | File |
|----|---------|----------|------|
| 1 | No CORS headers | Added `CORSMiddleware` | `backend/app/main.py` |
| 2 | Wrong redirect URI | Changed to `localhost:8000/auth/shopify/callback` | `backend/app/config.py` |
| 3 | Missing OAuth state | Added secure `state` token generation | `backend/app/routes/auth.py` |
| 4 | No token storage | Added `OAuthSession` model | `backend/app/models.py` |
| 5 | Empty API URL | Set default to `localhost:8000` | `frontend/src/types.ts` |

---

## You Only Need to Do 2 Things

### STEP 1: Delete Old Database
```bash
cd /home/claude/backend
rm -f test.db
```

### STEP 2: Start Servers

**Terminal 1 - Backend:**
```bash
cd /home/claude/backend
python -m uvicorn app.main:app --reload --port 8000
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

**Terminal 2 - Frontend:**
```bash
cd /home/claude/frontend
npm run dev
```

Expected output:
```
  ➜  Local:   http://localhost:5173/
```

---

## Test It (2 Easy Tests)

### Test 1: Health Check
```bash
curl http://localhost:8000/health
```
Expected: `{"status":"healthy"}`

### Test 2: OAuth Flow (Manual)
1. Open `http://localhost:5173/login` in browser
2. Enter shop: `3tj1az-h6.myshopify.com`
3. Click "Connect Shopify Store"
4. **Backend logs should show:**
   ```
   INFO: OAuth session created for shop: 3tj1az-h6.myshopify.com
   INFO: Redirecting to Shopify: https://3tj1az-h6.myshopify.com/admin/oauth/authorize?...
   ```

---

## Why the 307 Error is Fixed

### Before (Broken)
- Frontend sent request to `/auth/shopify/authorize?shop=...`
- Backend responded with `307 Temporary Redirect` to Shopify
- Frontend couldn't see the redirect (CORS blocked it)
- Default shop parameter was wrong

### After (Fixed)
1. ✅ CORS enabled → Frontend can see redirects
2. ✅ OAuth URL properly formed → Has `state`, `client_id`, `scope`
3. ✅ State token generated & stored → Prevents CSRF attacks
4. ✅ Redirect URI points to backend → Can process OAuth callback
5. ✅ Returns 302 (not 307) → Standard HTTP redirect

---

## Files Changed (All in /home/claude/)

```
backend/
├── app/
│   ├── main.py          (✅ CORS added)
│   ├── config.py        (✅ Port fixed)
│   ├── models.py        (✅ OAuthSession added)
│   ├── routes/
│   │   └── auth.py      (✅ OAuth flow rewritten)
│   └── ...
├── .env                 (✅ Already correct)
├── tests/
│   └── test_auth.py     (✅ Tests updated)
└── requirements.txt

frontend/
├── src/
│   ├── types.ts         (✅ API_URL fixed)
│   └── ...
├── .env                 (✅ NEW - API_URL set)
└── ...
```

---

## What You DON'T Need to Do

- ❌ Don't update `.env` files (they're already fixed)
- ❌ Don't install new packages (same requirements.txt)
- ❌ Don't rewrite database (will auto-create on startup)
- ❌ Don't change frontend LoginPage component (already correct)

---

## Architecture Diagram (Now Working)

```
Browser (port 5173)
    ↓
[LoginPage]
    ↓ Click "Connect Shopify"
    ↓
GET /auth/shopify/authorize?shop=...
    ↓
FastAPI Backend (port 8000)  ← WITH CORS ✅
    ↓
[Generate state token]
[Store in DB]
[Build OAuth URL with state]
    ↓
302 Redirect
    ↓
Browser → Shopify OAuth Screen
    ↓
[User consents]
    ↓
GET /auth/shopify/callback?code=...&state=...&shop=...
    ↓
FastAPI Backend
    ↓
[Verify state token]
[Save seller to DB]
[Create mock tokens]
    ↓
302 Redirect → /dashboard
    ↓
Browser → http://localhost:5173/dashboard ✅
```

---

## Key Insight: Why 307 → 302

The 307 status code wasn't wrong—it was the **destination** that was wrong:

- **307 Temporary Redirect** = "Redirect here, but use same HTTP method"
- **302 Found** = "Redirect here, may change HTTP method"

For OAuth, we want 302 because the browser will follow the redirect automatically.

Our fixed code returns `RedirectResponse(url=auth_url, status_code=302)` which is correct.

---

## Debug Commands (If Something Goes Wrong)

```bash
# 1. Check CORS headers
curl -i http://localhost:8000/health

# 2. Check OAuth endpoint
curl -i "http://localhost:8000/auth/shopify/authorize?shop=test.myshopify.com"

# 3. View database
cd backend
python3 << 'EOF'
from app.database import SessionLocal
from app.models import OAuthSession, Seller
db = SessionLocal()
print(f"OAuth sessions: {db.query(OAuthSession).count()}")
print(f"Sellers: {db.query(Seller).count()}")
EOF

# 4. Check frontend .env
cat frontend/.env

# 5. Check backend .env
cat backend/.env
```

---

## Next Steps (After Verification)

Once you confirm OAuth works:

1. **Get real Shopify API credentials** (replace `test_key` in `.env`)
2. **Implement real token exchange** (currently mocked)
3. **Build product fetching** (Task 1.3)
4. **Build VLM integration** (Task 2.1)

---

## Common Issues & Fixes

| Issue | Symptom | Fix |
|-------|---------|-----|
| CORS error in console | "Access-Control-Allow-Origin" | Restart backend (CORS middleware must load) |
| Database locked | "database is locked" | `rm -f backend/test.db` then restart |
| API_URL empty | Frontend can't reach backend | Check `frontend/.env` exists with `VITE_API_URL=http://localhost:8000` |
| 400 Bad Request | Missing shop parameter | Pass `?shop=something.myshopify.com` |
| 404 Not Found | Wrong endpoint path | Check path is `/auth/shopify/authorize` |
| State mismatch error | OAuth callback fails | Database wasn't reset (delete `test.db`) |

---

## One Last Thing

The error you saw:
```
307 Temporary Redirect
GET /auth/shopify/authorize?shop=3tj1az-h6.myshopify.com HTTP/1.1
```

This was **correct behavior**—the endpoint WAS redirecting. The problem was:
1. Frontend couldn't see the redirect (CORS)
2. The redirect destination might be wrong
3. Missing security parameters

**All 5 issues are now fixed.** You should see a clean 302 redirect to Shopify's OAuth screen.

---

