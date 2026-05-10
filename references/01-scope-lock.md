# Gate 1: Scope Lock

## Purpose
Lock feature scope BEFORE any code is written. Prevents scope creep, ensures every line of code has a purpose.

## Trigger
Automatically runs when user requests: "write code", "build feature", "create function", "fix bug", "add X to Y", "implement", "make a script", "code this"

## Process

### 1. Extract Acceptance Criteria
From user request, list EXACTLY what "done" looks like:
- [ ] Criterion 1: Measurable outcome (e.g., "Function returns JSON with keys: brand, color, material")
- [ ] Criterion 2: Performance constraint (e.g., "< 3 seconds per image")
- [ ] Criterion 3: Error handling (e.g., "Returns 400 if image URL invalid")
- [ ] Criterion 4: Integration point (e.g., "Saves result to PostgreSQL `extractions` table")

### 2. Define Data Contracts
Specify exact input/output types using Pydantic models:

```python
# Input Contract
class ExtractionRequest(BaseModel):
    product_ids: List[UUID]
    model_version: str = "qwen2-vl-ft-v1"

# Output Contract
class ExtractionResult(BaseModel):
    product_id: UUID
    attributes: Dict[str, str]  # Keys: brand, color, material, category
    confidence_score: float     # Range: 0.0 - 1.0
    processing_time_ms: int
    status: Literal["success", "failed", "retry"]
    error_message: Optional[str] = None
```

### 3. List Out-of-Scope Items
Explicitly state what this feature does NOT do:
- ❌ Does NOT handle batch uploads > 100 images (separate feature)
- ❌ Does NOT retry failed extractions automatically (handled by Celery beat)
- ❌ Does NOT validate image content (handled by Anomaly Detection module)
- ❌ Does NOT update Shopify product (read-only operation)

### 4. Identify Edge Cases
List all known edge cases that must be handled:
| Edge Case | Handling Strategy |
|-----------|-------------------|
| Image URL returns 404 | Catch HTTPError, return status="failed", error_message="Image not found" |
| Model returns non-JSON | Retry max 2 times with "Output JSON only" prompt, then fail gracefully |
| VRAM OOM (>4GB) | Clear cache after each inference, batch size = 1 for extraction |
| Empty product list | Return 400 Bad Request with message "No product IDs provided" |
| Shopify token expired | Catch AuthError, return status="failed", error_message="Re-authenticate required" |
| Duplicate product IDs | Deduplicate input list silently, log warning |

### 5. Dependency Check
Verify all required components exist:
- [ ] Database tables created (`products`, `extractions`)
- [ ] Redis queue running (`queue:extract`)
- [ ] Model weights available (`models/qwen2-vl-ft-v1.safetensors`)
- [ ] Shopify API credentials configured

### 6. Scope Sign-Off
**Scope is LOCKED when:**
- All acceptance criteria are measurable (no vague terms like "fast", "accurate")
- All edge cases have explicit handling strategies
- All dependencies are confirmed available
- Out-of-scope items are explicitly listed

**If any criterion is vague → STOP and clarify with user before proceeding.**
