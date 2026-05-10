# Gate 2: Test-First Contract

## Purpose
Write tests BEFORE implementation. Tests define the contract that code must fulfill. No code is written until tests are defined.

## Trigger
Runs immediately after Gate 1 (Scope Lock) completes.

## Process

### 1. Translate Acceptance Criteria to Tests
For EACH acceptance criterion in Gate 1, write a corresponding test:

```python
# Criterion: "Function returns JSON with keys: brand, color, material"
def test_extraction_returns_required_attributes():
    result = extract_attributes(product_id=test_uuid, image_url=test_image_url)
    assert "brand" in result.attributes
    assert "color" in result.attributes
    assert "material" in result.attributes
    assert result.status == "success"

# Criterion: "< 3 seconds per image"
def test_extraction_completes_within_time_limit():
    start_time = time.time()
    result = extract_attributes(product_id=test_uuid, image_url=test_image_url)
    elapsed_ms = (time.time() - start_time) * 1000
    assert elapsed_ms < 3000, f"Extraction took {elapsed_ms}ms, expected < 3000ms"
    assert result.processing_time_ms < 3000

# Criterion: "Returns 400 if image URL invalid"
def test_invalid_image_url_returns_error():
    result = extract_attributes(product_id=test_uuid, image_url="https://invalid-url-404.com/image.jpg")
    assert result.status == "failed"
    assert result.error_message is not None
    assert "not found" in result.error_message.lower() or "invalid" in result.error_message.lower()

# Criterion: "Saves result to PostgreSQL extractions table"
def test_extraction_saved_to_database():
    # Arrange
    test_product = create_test_product()
    
    # Act
    result = extract_attributes(product_id=test_product.id, image_url=test_product.image_url)
    
    # Assert
    db_result = db.query(Extraction).filter_by(product_id=test_product.id).first()
    assert db_result is not None
    assert db_result.attributes["brand"] == result.attributes["brand"]
    assert db_result.confidence_score == result.confidence_score
```

### 2. Define Edge Case Tests
For EACH edge case in Gate 1, write a test:

```python
# Edge Case: Model returns non-JSON
def test_non_json_model_output_retries_then_fails():
    # Mock model to return invalid JSON twice, then valid on third try
    mock_model_response.side_effect = ["{invalid", "{also invalid", '{"brand": "Test"}']
    
    result = extract_attributes(product_id=test_uuid, image_url=test_image_url)
    
    # Should retry twice, then succeed on third attempt
    assert mock_model_response.call_count == 3
    assert result.status == "success"

# Edge Case: VRAM OOM
def test_vram_oom_clears_cache_and_continues():
    # Mock torch.cuda.memory_allocated to simulate OOM
    mock_memory_allocated.return_value = 5_000_000_000  # 5GB > 4GB limit
    
    result = extract_attributes(product_id=test_uuid, image_url=test_image_url)
    
    # Should call empty_cache() after inference
    mock_empty_cache.assert_called_once()
    assert result.status == "success"  # Should recover gracefully

# Edge Case: Empty product list
def test_empty_product_list_returns_bad_request():
    with pytest.raises(HTTPException) as exc_info:
        extraction_batch(product_ids=[])
    
    assert exc_info.value.status_code == 400
    assert "No product IDs provided" in str(exc_info.value.detail)

# Edge Case: Duplicate product IDs
def test_duplicate_product_ids_deduplicated():
    duplicate_ids = [test_uuid, test_uuid, test_uuid]
    
    result = extraction_batch(product_ids=duplicate_ids)
    
    # Should only process once
    assert mock_extract_single.call_count == 1
```

### 3. Define Integration Tests
Tests that verify multiple components work together:

```python
def test_end_to_end_extraction_flow():
    """
    Full flow: API request → Celery task → Model inference → DB save → API response
    """
    # 1. Create test product
    product = create_test_product(shopify_product_id=12345)
    
    # 2. Trigger extraction via API
    response = client.post("/api/extractions", json={
        "product_ids": [str(product.id)]
    })
    assert response.status_code == 202  # Accepted (async)
    job_id = response.json()["job_id"]
    
    # 3. Wait for Celery task to complete (with timeout)
    max_wait = 10  # seconds
    start_time = time.time()
    while time.time() - start_time < max_wait:
        job_status = client.get(f"/api/jobs/{job_id}")
        if job_status.json()["status"] == "complete":
            break
        time.sleep(0.5)
    else:
        pytest.fail(f"Job did not complete within {max_wait} seconds")
    
    # 4. Verify result in database
    extraction = db.query(Extraction).filter_by(product_id=product.id).first()
    assert extraction is not None
    assert extraction.attributes["brand"] is not None
    
    # 5. Verify API returns correct result
    final_response = client.get(f"/api/extractions/{extraction.id}")
    assert final_response.status_code == 200
    assert final_response.json()["attributes"]["brand"] == extraction.attributes["brand"]
```

### 4. Define Performance Tests
```python
def test_concurrent_extractions_do_not_exceed_vram():
    """
    Verify that running 10 extractions in parallel does not exceed 4GB VRAM
    """
    import torch
    
    # Start 10 concurrent extractions
    tasks = [
        extract_attributes(product_id=uuid, image_url=test_image_url)
        for uuid in test_uuids[:10]
    ]
    results = await asyncio.gather(*tasks)
    
    # Check VRAM usage never exceeded 4GB during execution
    # (This would be captured by a monitoring hook in the test)
    assert max_vram_usage < 4_000_000_000, f"VRAM peaked at {max_vram_usage}, expected < 4GB"
```

### 5. Test Sign-Off
**Tests are READY when:**
- ✅ Every acceptance criterion from Gate 1 has at least one test
- ✅ Every edge case from Gate 1 has at least one test
- ✅ All tests are deterministic (no flaky tests with random/timing dependencies)
- ✅ All tests have clear Arrange-Act-Assert structure
- ✅ Mock objects are used for external dependencies (Shopify API, Model inference)
- ✅ Tests can run in isolation (no shared state between tests)

**If any criterion lacks a test → STOP and write the test before proceeding.**
