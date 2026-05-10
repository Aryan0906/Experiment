# Zero-Trash Code Protocol - Active

## ✅ Reference Files Created

All 5 gates of the Zero-Trash Code Protocol are now active in this workspace:

| Gate | Reference File | Status |
|------|----------------|--------|
| **Gate 1: Scope Lock** | `references/01-scope-lock.md` | ✅ Active |
| **Gate 2: Test-First** | `references/02-test-first.md` | ✅ Active |
| **Gate 3: Code Generation** | `references/03-code-generation.md` | ✅ Active |
| **Gate 4: Trash Detector** | `references/03-trash-detector.md` | ✅ Active |
| **Gate 5: Test Runner** | `references/04-test-runner.md` | ✅ Active |

## 📋 Skill File Created

- **`SKILL-zero-trash-code.md`** - Master protocol document (361 lines)

## 🎯 How It Works

### Automatic Activation
The protocol activates when you use phrases like:
- "write code"
- "build feature"
- "create function"
- "fix bug"
- "implement X"
- "make a script"
- "code this"

### The 5-Gate Pipeline

Every piece of code passes through:

1. **Scope Lock** → Defines exactly what "done" means
2. **Test-First** → Writes tests before implementation
3. **Bug-Free Code** → 7 quality gates (types, errors, resources, validation, logging, idempotency, security)
4. **Trash Detector** → Removes unused imports, dead code, TODOs, magic numbers
5. **Test Runner** → Verifies all tests pass with ≥85% coverage

### Output Format

```
⚡ Quick Scope + Tests
───────────────────────────
Does: <description>
Tests: <test cases>
Out of scope: <exclusions>
───────────────────────────

[Clean, type-safe code]

🗑️ Trash Detection
───────────────────────────
Status: CLEAN ✓
───────────────────────────

✅ Test Results
───────────────────────────
tests/test_file.py::test_case_1 PASSED
tests/test_file.py::test_case_2 PASSED

Coverage: 92% ✓
Status: ALL TESTS PASSED ✓
───────────────────────────
```

## 🛡️ Non-Negotiables

These rules cannot be overridden:

1. ❌ No code ships with failing tests
2. ❌ No function exists without a requirement
3. ❌ No placeholder code (`# TODO`, `pass`)
4. ❌ No untested acceptance criteria
5. ❌ No trash in skills

## 🚀 Next Steps

To start using the protocol, simply request:

**Example:**
> "Write a function to validate product image URLs"

The system will automatically:
1. Lock scope (what "validate" means, edge cases)
2. Write tests first (valid URLs, invalid URLs, edge cases)
3. Generate bug-free code (type-safe, error-handled, secure)
4. Detect and remove any trash
5. Run tests and show results

## 📁 Directory Structure

```
/workspace/
├── SKILL-zero-trash-code.md      # Master protocol
├── references/
│   ├── 01-scope-lock.md          # Gate 1
│   ├── 02-test-first.md          # Gate 2
│   ├── 03-code-generation.md     # Gate 3
│   ├── 03-trash-detector.md      # Gate 4
│   └── 04-test-runner.md         # Gate 5
└── tests/                        # Test directory
    └── __init__.py
```

---

**Status:** ✅ Zero-Trash Code Protocol is now ACTIVE

**Remember:** Zero trash. Zero bugs. Zero exceptions.
