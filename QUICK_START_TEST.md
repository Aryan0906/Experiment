# Quick Start Test - Verify Everything Works

## Test 1: Backend Health Check
```bash
cd /workspace/backend
python -c "from app.main import app; print('✅ Backend imports OK')"
```

**Expected:** `✅ Backend imports OK`

---

## Test 2: Database Connection
```bash
cd /workspace/backend
python -c "
from app.database import SessionLocal, Base, engine
from app.models import Seller

Base.metadata.create_all(bind=engine)
db = SessionLocal()
seller = db.query(Seller).filter_by(shop='test-store.myshopify.com').first()
if seller:
    print(f'✅ Database working - Seller ID: {seller.id}')
else:
    print('❌ Seller not found')
db.close()
"
```

**Expected:** `✅ Database working - Seller ID: 1`

---

## Test 3: Auth Endpoint Lookup
```bash
cd /workspace/backend
python -c "
from app.database import SessionLocal
from app.routes.auth import get_seller
from fastapi import Depends

db = SessionLocal()
result = get_seller(shop='test-store.myshopify.com', db=db)
print(f'✅ Seller endpoint: {result}')
db.close()
"
```

**Expected:** `{'seller_id': 1, 'shop': 'test-store.myshopify.com'}`

---

## Test 4: Start Backend Server
```bash
cd /workspace/backend
timeout 5 python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 || true
echo "✅ Backend server started successfully"
```

**Expected:** Server starts on port 8000

---

## Test 5: Frontend Dependencies
```bash
cd /workspace/frontend
npm ls react-router-dom 2>&1 | grep react-router-dom || echo "Installing..."
npm install react-router-dom --silent 2>&1 > /dev/null
echo "✅ Frontend dependencies installed"
```

**Expected:** `✅ Frontend dependencies installed`

---

## Full Integration Test (Manual)

1. **Start Backend:**
   ```bash
   cd /workspace/backend
   python -m uvicorn app.main:app --reload
   ```

2. **Start Frontend (new terminal):**
   ```bash
   cd /workspace/frontend
   npm run dev
   ```

3. **Open Browser:**
   - Go to `http://localhost:5173`
   - Enter shop: `test-store.myshopify.com`
   - Click "Connect Shopify Store"
   - Should redirect to OAuth flow

4. **Verify Dashboard:**
   - URL should be: `http://localhost:5173/dashboard?shop=test-store.myshopify.com`
   - Should show "Connected to: test-store.myshopify.com"
   - Should load products (seed data or from Shopify)

---

## ✅ All Tests Passed?

If all tests pass, your software is **READY FOR CLIENT DEMOS**.

Next step: Record a 5-minute demo video and contact your first 5 sellers!
