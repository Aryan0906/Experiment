# Gate 5: Test Runner Verification

## Purpose
Verify ALL tests pass before code is considered complete. No failing tests ship. Ever.

## Trigger
Runs automatically after Gate 4 (Trash Detector) completes. Final gate before code ships.

## Test Execution Protocol

### Step 1: Environment Setup
```bash
# Ensure test dependencies installed
pip install pytest pytest-cov pytest-asyncio pytest-mock factory-boy faker

# Set test environment variables
export TEST_DATABASE_URL="postgresql://test:test@localhost:5432/test_db"
export REDIS_URL="redis://localhost:6379/1"
export ENVIRONMENT="test"
export LOG_LEVEL="DEBUG"
```

### Step 2: Run Full Test Suite
```bash
# Run all tests with coverage
pytest tests/ \
    --verbose \
    --cov=app \
    --cov-report=term-missing \
    --cov-report=html \
    --cov-fail-under=85 \
    --maxfail=5 \
    --dist=no \
    -n auto
```

**Flags explained:**
- `--verbose`: Show each test name and result
- `--cov=app`: Measure coverage for `app` directory
- `--cov-report=term-missing`: Show uncovered lines in terminal
- `--cov-fail-under=85`: Fail if coverage < 85%
- `--maxfail=5`: Stop after 5 failures (prevents flood of errors)
- `-n auto`: Parallelize tests across CPU cores

### Step 3: Analyze Results

#### If ALL TESTS PASS ✅
```
======================== 47 passed, 3 warnings in 12.34s ========================
Name                           Stmts   Miss  Cover   Missing
------------------------------------------------------------
app/api/extractions.py            45      2    96%   78-79
app/services/model_loader.py      32      1    97%   45
------------------------------------------------------------
TOTAL                            780     98    87%

Required coverage: 85%
Achieved coverage: 87% ✓
```

**Action:** Proceed to code review → Merge → Deploy

#### If ANY TEST FAILS ❌
```
=================================== FAILURES ===================================
______________________ test_extraction_returns_attributes ______________________

    def test_extraction_returns_attributes():
>       assert "brand" in result.attributes
E       AssertionError: assert 'brand' in {}
E        +  where {} = ExtractionResult(attributes={}, ...).attributes

tests/test_extractions.py:23: AssertionError
===================== 1 failed, 46 passed in 11.89s =====================
```

**Action:**
1. **DO NOT PROCEED** until fixed
2. Read failure message carefully
3. Identify root cause:
   - Bug in implementation? → Fix code
   - Bug in test? → Fix test
   - Missing dependency? → Install/configure
4. Fix the issue
5. Re-run ONLY the failed test: `pytest tests/test_extractions.py::test_extraction_returns_attributes -v`
6. Once it passes, re-run full suite
7. Repeat until ALL tests pass

### Step 4: Coverage Analysis

**Rule:** Minimum 85% coverage required. Critical modules (API, services) require 95%+.

If coverage < 85%:
```bash
# Generate HTML report for detailed analysis
pytest --cov=app --cov-report=html

# Open in browser
open htmlcov/index.html
```

**Identify uncovered lines:**
- Are they edge cases? → Write tests for them
- Are they dead code? → Delete (Gate 4 should have caught this)
- Are they impossible to test? → Refactor to make testable

**Common coverage gaps and fixes:**

| Gap | Why It Happens | Fix |
|-----|----------------|-----|
| Error handlers not covered | Tests only check happy path | Add tests for failure scenarios |
| Utility functions not covered | Assumed "too simple to fail" | Write unit tests anyway |
| Integration points not covered | Requires external setup | Use mocks/fixtures |
| Async functions not covered | Test runner config issue | Add `@pytest.mark.asyncio` |

### Step 5: Performance Test Verification

Run performance tests separately (they're slow):
```bash
pytest tests/performance/ -v --tb=short
```

**Expected results:**
```
tests/performance/test_extraction_speed.py::test_extraction_under_3s PASSED
tests/performance/test_concurrent_load.py::test_10_concurrent_extractions PASSED
tests/performance/test_vram_usage.py::test_vram_stays_under_4gb PASSED
```

**If performance test fails:**
- Profile the bottleneck: `pytest --profile-svg`
- Optimize hot path
- Re-test

### Step 6: Integration Test Verification

Run integration tests (requires test database + Redis):
```bash
# Start test services
docker-compose -f docker-compose.test.yml up -d

# Run integration tests
pytest tests/integration/ -v --tb=long

# Cleanup
docker-compose -f docker-compose.test.yml down
```

**Critical integration tests:**
- [ ] End-to-end extraction flow (API → Celery → Model → DB → API)
- [ ] Shopify OAuth flow (mocked)
- [ ] Database migrations (upgrade + downgrade)
- [ ] Redis queue processing

### Step 7: Security Scan

Run security checks before shipping:
```bash
# Check for hardcoded secrets
detect-secrets scan --baseline .secrets.baseline

# Check dependencies for vulnerabilities
pip-audit

# Static security analysis
bandit -r app/ -f json -o bandit-report.json
```

**Action:** Fix ALL high/critical severity issues before proceeding.

## Test Quality Checklist

Before marking Gate 5 as complete, verify:

- [ ] **All unit tests pass** (0 failures)
- [ ] **All integration tests pass** (0 failures)
- [ ] **All performance tests pass** (within thresholds)
- [ ] **Code coverage ≥ 85%** (≥ 95% for critical modules)
- [ ] **No flaky tests** (tests that pass/fail randomly)
- [ ] **No skipped tests** (unless documented with good reason)
- [ ] **Security scans clean** (no high/critical vulnerabilities)
- [ ] **Test output is readable** (clear assertions, helpful error messages)

## Flaky Test Protocol

If a test is flaky (passes sometimes, fails other times):

**DO NOT:**
- ❌ Ignore it ("it's probably fine")
- ❌ Add `@pytest.mark.skip` to hide it
- ❌ Increase timeouts indefinitely

**DO:**
- ✅ Identify root cause (race condition? shared state? timing?)
- ✅ Fix the underlying issue
- ✅ Add proper synchronization (locks, waits, fixtures)
- ✅ Verify it passes 10 times in a row: `for i in {1..10}; do pytest tests/test_x.py; done`

## Sign-Off

**Gate 5 PASSES when:**
- ✅ All tests pass (0 failures)
- ✅ Coverage requirements met
- ✅ Performance thresholds met
- ✅ Security scans clean
- ✅ No flaky tests

**Final command before sign-off:**
```bash
# One final full run to confirm everything works
pytest tests/ -v --cov=app --cov-fail-under=85
```

**If this command succeeds → CODE IS READY TO SHIP**

**If this command fails → FIX ISSUES → Re-run from Step 2**

---

## Post-Merge Verification

After code is merged and deployed:

1. **Smoke test production:**
   ```bash
   # Run minimal test against production (read-only)
   curl https://api.yoursaas.com/health
   ```

2. **Monitor for regressions:**
   - Watch error rates in Sentry
   - Monitor response times in Grafana
   - Check for new exceptions in logs

3. **Rollback plan ready:**
   - If critical bug found in production → Rollback to previous version immediately
   - Fix bug in development → Re-run all 5 gates → Redeploy

---

## Remember

> **"Tests are the contract. Code is the implementation. If they don't match, fix the code."**

Never skip Gate 5. Never merge with failing tests. Never deploy without verification.

**Zero trash. Zero bugs. Zero exceptions.**
