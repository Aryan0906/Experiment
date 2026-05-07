# ZERO-TRASH-CODE PROMPT (For Every Feature)

**Use this prompt template for every coding task. Fill in the blanks, then give it to Claude.**

---

## 🔒 FEATURE SCOPE LOCK (Gate 1)

**Feature Name:** [e.g., "Shopify OAuth Login"]  
**User Story:** [Paste from MVP brief]  
**Acceptance Criteria:** [Copy from MVP brief]  
**NOT IN SCOPE:** [Explicitly list what's NOT being built]

**Question:** Is the scope clear and locked? (If not, ask clarifying questions before coding.)

---

## 🧪 TEST-FIRST CONTRACT (Gate 2)

**Before you write ANY code, write the test that MUST pass.**

### Example for Shopify OAuth:
```python
def test_shopify_oauth_flow():
    """
    GIVEN: User at login page
    WHEN: User clicks "Connect Shopify"
    THEN: Redirected to Shopify OAuth consent screen
    AND: After consent, seller_id + refresh_token stored in DB (encrypted)
    AND: User returned to dashboard with "Connected: myshop.myshopify.com"
    """
    # Arrange
    client = TestClient(app)
    
    # Act
    response = client.get("/auth/shopify/authorize")
    
    # Assert
    assert response.status_code == 302
    assert "myshopify.com" in response.location
    
    # Simulate OAuth callback
    callback_response = client.get(
        "/auth/shopify/callback",
        params={"code": "test_code", "shop": "myshop.myshopify.com"}
    )
    
    assert callback_response.status_code == 200
    seller = db.query(Seller).filter_by(shop="myshop.myshopify.com").first()
    assert seller is not None
    assert seller.refresh_token is not None  # Encrypted
```

**Your Test Contract:**
```
[PASTE OR WRITE THE TEST THAT MUST PASS]
```

---

## 💻 BUG-FREE CODE (Gate 3)

**When writing code, follow these rules:**

### Rule 1: No Dead Code
- Every function must be called.
- Every imported module must be used.
- No commented-out code.
- If you write it, it runs.

### Rule 2: No Scope Creep
- Stick to the feature. Nothing more.
- If you find yourself writing "it would be nice if...", STOP. Add to backlog, don't build it.

### Rule 3: Error Handling
- Every external call (Shopify API, DB, VLM) must have try-except.
- Every except block must log the error and return a user-facing message.
- Test what happens when it fails.

### Rule 4: Type Safety
- Use TypeScript (frontend) and type hints (FastAPI).
- No `any`, no implicit types.
- Mypy should pass: `mypy --strict`

### Rule 5: No Magic Strings
- Hardcoded strings belong in `.env` or a config file.
- Example: `SHOPIFY_API_VERSION = "2024-01"` not `"2024-01"` scattered in code.

---

## 🗑️ TRASH DETECTOR (Gate 4)

**Before committing, scan your code for trash:**

| Trash Type | Example | Fix |
|-----------|---------|-----|
| Dead code | `old_fetch_products()` never called | Delete it |
| Unused imports | `import pandas as pd` but never used | Delete import |
| Magic strings | `"https://myshop.myshopify.com"` hardcoded | Move to .env |
| Overfitting | Function handles 5 edge cases but feature only needs 1 | Simplify |
| Over-engineering | Built a plugin system for one feature | Just do the feature |
| Commented code | `# old_way = fetch_from_api()` | Delete |
| Premature optimization | "I'll cache this for performance" (untested) | Build simple first |
| Scope creep | You built multi-marketplace support when MVP is Shopify only | Delete |

**Trash Checklist:**
- [ ] No commented-out code
- [ ] No unused imports
- [ ] No unused functions
- [ ] No hardcoded config (moved to .env)
- [ ] No "TODO" or "FIXME" comments without a corresponding ticket
- [ ] No edge cases beyond acceptance criteria
- [ ] No premature optimization

---

## ✅ TEST RUNNER VERIFICATION (Gate 5)

**Before you say "done," run this:**

```bash
# Backend (FastAPI)
pytest tests/ -v --tb=short
mypy --strict app/
black --check app/
flake8 app/ --max-line-length=100

# Frontend (React)
npm test -- --coverage --watchAll=false
npm run build
npm run lint
```

**For THIS feature, the tests that MUST PASS:**
```
[COPY YOUR TEST-FIRST CONTRACT HERE]
```

**Exit criteria:**
- [ ] All tests pass (green)
- [ ] Type checker passes (mypy strict)
- [ ] Linter passes (no style warnings)
- [ ] Manual test in browser/CLI works
- [ ] No console errors or warnings

---

## 🎯 FINAL CHECKLIST BEFORE "DONE"

- [ ] **Feature is in scope** — Does it match the acceptance criteria exactly?
- [ ] **Test written first** — Did you write the test before the code?
- [ ] **Code is bug-free** — Handles errors, no magic strings, no dead code?
- [ ] **Trash is removed** — No commented code, unused imports, overfitting?
- [ ] **Tests pass** — Green checkmarks on all unit + integration tests?
- [ ] **Code review** — You reviewed your own code, explained why it's written this way?
- [ ] **Manual test** — You used the feature in the browser/CLI and it works?
- [ ] **Deployed** — Pushed to staging branch on Render/Vercel?
- [ ] **No regressions** — Did you break anything else?

---

## 🚫 IF YOU GET STUCK

**Question 1:** Is the test passing?
- If no → Debug the code, not the test.

**Question 2:** Does the code handle errors?
- If no → Add try-except + logging.

**Question 3:** Is the feature in scope?
- If no → Remove it, add to backlog.

**Question 4:** Is there dead code?
- If yes → Delete it.

**If still stuck:** Throw away the code and start over. You'll be faster the second time.

---

## TEMPLATE FOR EACH CODING SESSION

**Copy this, fill it in, give it to Claude with the code files:**

```
ZERO-TRASH-CODE REQUEST

FEATURE: [Name]
STORY: [User story from MVP brief]
SCOPE: [What's included]
NOT IN SCOPE: [What's explicitly NOT included]

TEST CONTRACT:
[Your test, copy-pasted from MVP brief or written fresh]

TECH STACK:
- Backend: [FastAPI, SQLAlchemy, PostgreSQL, etc.]
- Frontend: [React, TypeScript, TailwindCSS]
- VLM: [Your model]

DELIVERABLE:
- Code (fully typed, tested, no dead code)
- Test file (red-green-refactor cycle visible)
- Deployment ready (can run on Render/Vercel)

CONSTRAINTS:
- No scope creep
- No premature optimization
- No hardcoded config
- Test must pass before code is "done"
```

---

## WHY THIS WORKS

1. **Scope lock** prevents "just one more feature" bloat.
2. **Test-first** forces you to think before you code.
3. **Bug-free rules** catch errors before they ship.
4. **Trash detection** keeps code clean and maintainable.
5. **Test runner** is your confidence signal — green = ship.

**Result:** Every feature ships working, tested, and clean. No regressions. No tech debt.

---

