# Zero-Trash Code Protocol

**Version:** 1.0  
**Status:** Active  
**Applies to:** All code generation tasks in this workspace

---

## Mission Statement

Every piece of code produced in this workspace passes a rigorous 5-gate pipeline. No exceptions. No "I'll clean it up later". Trash never ships.

This protocol prevents:
- Sloppy code with bugs
- Dead code (written but never called)
- Untested features
- Scope creep
- Security vulnerabilities
- Performance regressions

---

## Trigger Phrases

This skill activates automatically when user requests include:
- "write code"
- "build feature"
- "create function"
- "fix bug"
- "add X to Y"
- "implement"
- "make a script"
- "code this"
- "create a module"
- "develop API endpoint"
- Any task where runnable code or skill/prompt file will be produced

**Note:** Even if user says "just write it quickly" or "skip tests for now" — still run all 5 gates internally. Gates 1-4 are silent (user sees only clean output). Gate 5 output is shown.

---

## The 5-Gate Pipeline

### Gate 1: Scope Lock
**Reference:** `references/01-scope-lock.md`

**Purpose:** Lock feature scope BEFORE any code is written.

**Process:**
1. Extract acceptance criteria (measurable outcomes)
2. Define data contracts (Pydantic models for input/output)
3. List out-of-scope items explicitly
4. Identify edge cases and handling strategies
5. Verify dependencies exist
6. Obtain scope sign-off

**Output:** Locked scope document with clear "done" definition.

**Rule:** If any criterion is vague → STOP and clarify before proceeding.

---

### Gate 2: Test-First Contract
**Reference:** `references/02-test-first.md`

**Purpose:** Write tests BEFORE implementation. Tests define the contract.

**Process:**
1. Translate each acceptance criterion to test case
2. Write edge case tests for each identified edge case
3. Write integration tests for multi-component flows
4. Write performance tests for latency/throughput requirements
5. Obtain test sign-off

**Output:** Complete test suite (initially failing, as code not written yet).

**Rule:** If any criterion lacks a test → STOP and write the test before proceeding.

---

### Gate 3: Bug-Free Code Generation
**Reference:** `references/03-code-generation.md`

**Purpose:** Write code that passes 7 quality gates.

**The 7 Gates:**
1. **Type Safety:** All parameters, returns, variables typed
2. **Error Handling:** Specific exceptions, actionable messages
3. **Resource Management:** Context managers, proper cleanup
4. **Input Validation:** Pydantic at boundaries, no trust
5. **Logging & Observability:** Structured logs, no print()
6. **Idempotency & Retry Safety:** Safe to retry, no side effects
7. **Security Hardening:** OWASP Top 10, no hardcoded secrets

**Output:** Clean, type-safe, secure code.

**Rule:** If any gate fails → FIX before proceeding to Gate 4.

---

### Gate 4: Trash Detector
**Reference:** `references/03-trash-detector.md`

**Purpose:** Detect and remove ALL trash from code.

**Trash Types (Must Remove):**
- Unused imports
- Dead functions
- Orphan variables
- Placeholder comments (TODO, FIXME)
- Duplicate logic
- "Just in case" code
- Magic numbers
- Commented-out code
- Over-engineering
- Print debugging

**Detection Process:**
1. Import audit (`ruff check --select=F401`)
2. Dead code detection (`vulture`)
3. TODO/FIXME hunt (`grep`)
4. Duplicate logic scan (manual review)
5. Magic number extraction
6. Commented code sweep
7. Over-engineering check

**Output:** Lean code where every line contributes to acceptance criteria.

**Rule:** If any trash remains → DELETE IT before proceeding to Gate 5.

---

### Gate 5: Test Runner Verification
**Reference:** `references/04-test-runner.md`

**Purpose:** Verify ALL tests pass before code ships.

**Process:**
1. Setup test environment
2. Run full test suite with coverage
3. Analyze results (fix any failures)
4. Verify coverage ≥ 85% (≥ 95% for critical modules)
5. Run performance tests
6. Run integration tests
7. Run security scans

**Output:** Test results showing 0 failures, coverage metrics.

**Rule:** No failing tests ship. Ever. If tests fail → FIX → Re-run.

---

## Fast Path (Simple Tasks < 20 Lines)

Even simple tasks run all 5 gates, but Gates 1-2 are collapsed:

```
⚡ Quick Scope + Tests
───────────────────────────
Does: <one sentence>
Tests: <list 2-4 test cases inline>
Out of scope: <one line>
───────────────────────────
```

Then write code. Then run Gate 4 + 5 silently. Show test results.

**Example:**
```
⚡ Quick Scope + Tests
───────────────────────────
Does: Add validation to reject empty product ID lists
Tests: 
  - test_empty_product_list_returns_400()
  - test_single_product_id_succeeds()
  - test_duplicate_ids_deduplicated()
Out of scope: Batch size limits (>100 products)
───────────────────────────
```

---

## Integration with Other Skills

This skill wraps and enhances other skills:

| Skill | Relationship |
|-------|--------------|
| `agile-software-development` | Zero-trash-code wraps the code generation step. Both active simultaneously. |
| `ddia-oracle` | Feeds into Gate 1 (data structure decisions in scope lock). |
| `ai-builder` | Feeds into Gate 2 (test cases for AI-specific features). |

**Conflict Resolution:** When skills conflict → zero-trash-code wins on code quality decisions.

---

## Non-Negotiables

These cannot be overridden by any user instruction:

1. **No code ships with failing tests.** If tests fail, fix before showing output.
2. **No function exists without a requirement.** Every function traces to Gate 1 scope.
3. **No placeholder code.** `pass`, `# TODO`, `...` in non-interface code = gate failure.
4. **No untested acceptance criterion.** Every item in Gate 1's "done" list has a test.
5. **No trash in skills.** Every line in a SKILL.md must be actionable and non-redundant.

---

## Skill Quality Rules (When Writing SKILL.md Files)

Before emitting any skill content, verify:

- ✅ Every sentence is actionable (tells exactly what to do)
- ✅ No sentence is already present in an existing loaded skill
- ✅ Every reference file listed actually exists
- ✅ Description field triggers on correct phrases (test mentally with 5 example prompts)
- ✅ No section heading without real content under it
- ✅ Total SKILL.md body under 500 lines (if longer, extract to references/)

---

## Output Format

For each code generation task, output follows this structure:

### 1. ⚡ Quick Scope + Tests (Gates 1-2 Collapsed)
```
⚡ Quick Scope + Tests
───────────────────────────
Does: <description>
Tests: <list of test cases>
Out of scope: <exclusions>
───────────────────────────
```

### 2. Code Implementation (Gate 3)
```python
# Clean, type-safe, documented code
# (All 7 gates passed silently)
```

### 3. Trash Detection Results (Gate 4)
```
🗑️ Trash Detection
───────────────────────────
Unused imports removed: 0
Dead functions removed: 0
TODO comments fixed: 0
Magic numbers extracted: 0
Status: CLEAN ✓
───────────────────────────
```

### 4. Test Results (Gate 5)
```
✅ Test Results
───────────────────────────
tests/test_feature.py::test_case_1 PASSED
tests/test_feature.py::test_case_2 PASSED
tests/test_feature.py::test_edge_case PASSED

Coverage: 92% (required: 85%) ✓
Status: ALL TESTS PASSED ✓
───────────────────────────
```

---

## Enforcement Mechanism

This skill is enforced by:

1. **Automated checks:** ruff, vulture, pytest run automatically
2. **Manual review:** Each gate requires conscious sign-off
3. **Peer accountability:** Code reviewed against this protocol
4. **Zero tolerance:** Trash/failing tests = immediate rejection

---

## Examples

### Example 1: User says "Write a function to extract product attributes"

**Response:**
```
⚡ Quick Scope + Tests
───────────────────────────
Does: Extract brand, color, material from product image using Qwen2-VL model
Tests:
  - test_extraction_returns_required_attributes()
  - test_extraction_completes_within_3s()
  - test_invalid_image_url_returns_error()
  - test_extraction_saved_to_database()
Out of scope: Batch processing >100 images, automatic retries
───────────────────────────

[Code implementation with full type safety, error handling, etc.]

🗑️ Trash Detection
───────────────────────────
Status: CLEAN ✓
───────────────────────────

✅ Test Results
───────────────────────────
tests/test_extractions.py::test_extraction_returns_required_attributes PASSED
tests/test_extractions.py::test_extraction_completes_within_3s PASSED
tests/test_extractions.py::test_invalid_image_url_returns_error PASSED
tests/test_extractions.py::test_extraction_saved_to_database PASSED

Coverage: 94% ✓
Status: ALL TESTS PASSED ✓
───────────────────────────
```

### Example 2: User says "Fix the bug in extraction endpoint"

**Response:**
```
⚡ Quick Scope + Tests
───────────────────────────
Does: Fix 500 error when model returns non-JSON response
Tests:
  - test_non_json_response_retries_then_fails_gracefully()
  - test_max_retries_not_exceeded()
Out of scope: Changing model behavior, updating prompt templates
───────────────────────────

[Fix implementation]

✅ Test Results
───────────────────────────
tests/test_extractions.py::test_non_json_response_retries_then_fails_gracefully PASSED
tests/test_extractions.py::test_max_retries_not_exceeded PASSED

Status: ALL TESTS PASSED ✓
───────────────────────────
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-06-01 | Initial release |

---

## References

- `references/01-scope-lock.md` - Gate 1 detailed process
- `references/02-test-first.md` - Gate 2 detailed process
- `references/03-code-generation.md` - Gate 3 (7 quality gates)
- `references/03-trash-detector.md` - Gate 4 trash detection
- `references/04-test-runner.md` - Gate 5 test verification

---

**Remember:** Zero trash. Zero bugs. Zero exceptions.
