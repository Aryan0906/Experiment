# Gate 4: Trash Detector

## Purpose
Detect and remove ALL trash from code before it ships. Trash never leaves this workspace.

## Trigger
Runs automatically after Gate 3 (Code Generation) completes, BEFORE tests are run.

## What is "Trash"?

### Code Trash (Must Remove)
| Type | Example | Action |
|------|---------|--------|
| **Unused imports** | `import os` (never used) | DELETE |
| **Dead functions** | `def helper(): ...` (never called) | DELETE |
| **Orphan variables** | `result = compute(); # result never read` | DELETE variable or USE it |
| **Placeholder comments** | `# TODO: implement this`, `# fix later` | IMPLEMENT or DELETE |
| **Duplicate logic** | Same computation done twice in different functions | EXTRACT to shared function |
| **"Just in case" code** | Functions/branches not required by any acceptance criterion | DELETE |
| **Wrong feature code** | Code copied from different feature that doesn't apply here | DELETE |
| **Magic numbers** | `if retries > 3:` (no named constant) | REPLACE with `MAX_RETRIES = 3` |
| **Commented-out code** | `# old_code = do_something()` | DELETE (git history exists) |
| **Over-engineering** | Abstract base class for single implementation | SIMPLIFY to concrete class |
| **Defensive over-validation** | Validating same input 3 times in different layers | KEEP only at boundary |
| **Print debugging** | `print(f"DEBUG: {value}")` | REPLACE with proper logging or DELETE |
| **Redundant type hints** | `x: int = 5` where type is obvious AND no interface benefit | KEEP if Pydantic/interface, else simplify |

### Skill Trash (Must Remove from SKILL.md files)
| Type | Example | Action |
|------|---------|--------|
| **Generic boilerplate** | "Always write clean code", "Follow best practices" | DELETE (too vague) |
| **Repeated instructions** | Same rule already in another skill | DELETE or MERGE |
| **Padding text** | "Make sure to", "Always remember to", "It's important that" | DELETE, keep only actionable |
| **Contradictions** | Section A says X, Section B says not X | RESOLVE contradiction |
| **Phantom references** | `See references/file.md` (file doesn't exist) | CREATE file or DELETE reference |
| **Empty sections** | `## Examples` (with no examples) | FILL with real examples or DELETE section |

## Detection Process

### Step 1: Import Audit
```bash
# Run automatically
ruff check --select=F401,F403,F405 /workspace
```
- F401: Unused imports
- F403: Wildcard imports (`from x import *`)
- F405: Undefined names (often from unused wildcard imports)

**Action:** Delete all unused imports immediately.

### Step 2: Dead Code Detection
```bash
# Run automatically
vulture /workspace --min-confidence 80
```
**Action:** Review each reported item:
- If truly unused → DELETE
- If false positive (used dynamically) → Add `# noqa: V001` comment with explanation

### Step 3: TODO/FIXME Hunt
```bash
# Run automatically
grep -rn "TODO\|FIXME\|XXX\|HACK\|BUG" /workspace --include="*.py" | grep -v "__pycache__"
```
**Action:** For each match:
- If it's a real task → IMPLEMENT it now
- If it's obsolete → DELETE the comment
- If it's future work → Move to GitHub Issues, DELETE comment

**Rule:** No placeholder comments ship. Period.

### Step 4: Duplicate Logic Scan
Manual review: Look for:
- Same function body in multiple files
- Same regex pattern defined twice
- Same validation logic in multiple places
- Same SQL query repeated

**Action:** Extract to shared utility module.

### Step 5: Magic Number Extraction
Scan for numeric literals:
```python
# ❌ Trash
if len(product_ids) > 100:
    raise ValueError("Too many")
    
timeout = 30
max_retries = 3

# ✅ Clean
MAX_BATCH_SIZE = 100
HTTP_TIMEOUT_SECONDS = 30
MAX_RETRY_ATTEMPTS = 3

if len(product_ids) > MAX_BATCH_SIZE:
    raise ValueError(f"Maximum {MAX_BATCH_SIZE} products per batch")
```

**Action:** Replace all magic numbers with named constants at module top.

### Step 6: Commented Code Sweep
```bash
# Run automatically
grep -rn "^#.*=\|^[[:space:]]*#" /workspace --include="*.py" | grep -v "^[^:]*:# [A-Z]" | head -20
```
**Action:** Delete all commented-out code blocks. Git has the history.

### Step 7: Over-Engineering Check
Ask for each abstraction:
- Is this interface implemented by more than one class? → If NO, consider concrete class
- Is this generic parameter actually used with multiple types? → If NO, simplify
- Does this design pattern solve a problem we actually have? → If NO, remove

**Action:** Simplify to YAGNI (You Ain't Gonna Need It).

## Trash Detection Checklist

Before marking Gate 4 as complete, verify:

- [ ] **Zero unused imports** (ruff F401 clean)
- [ ] **Zero dead functions** (vulture clean or documented false positives)
- [ ] **Zero TODO/FIXME comments** (all implemented or deleted)
- [ ] **Zero duplicate logic** (DRY verified)
- [ ] **Zero magic numbers** (all extracted to named constants)
- [ ] **Zero commented-out code** (deleted)
- [ ] **Zero print statements** (replaced with logging or deleted)
- [ ] **Zero "just in case" features** (all code traces to Gate 1 acceptance criteria)
- [ ] **Zero over-engineering** (simplest solution that works)
- [ ] **Zero orphan variables** (all assigned variables are read)

## Sign-Off

**Gate 4 PASSES when:**
- All trash types above are eliminated
- Code does exactly what Gate 1 requires, nothing more, nothing less
- Every line of code contributes to a stated acceptance criterion

**If any trash remains → DELETE IT before proceeding to Gate 5.**

## Post-Cleanup Verification

After trash removal, run:
```bash
# Verify tests still pass (trash deletion shouldn't break anything)
pytest tests/ -v

# Verify no new linting errors
ruff check /workspace
mypy /workspace
```

If tests fail after trash removal → you deleted something actually needed → restore it and re-categorize as "not trash".
