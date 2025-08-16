# Bug Reproduction Guide

## Issue Information
- **Issue ID**: e9ab8a5e-e510-48d0-9ea3-a1c7739f04c4
- **Title**: Large PDF processing timeout
- **Severity**: high
- **Category**: performance
- **Status**: open

## Description
Documents larger than 50MB fail to process due to timeout limits. This affects user experience and prevents processing of academic papers and technical documents.

## Environment
- **os**: Ubuntu 20.04
- **python_version**: 3.9.0
- **memory**: 8GB
- **cpu**: Intel i7-8700K
- **browser**: Chrome 96.0

## Expected Behavior
PDF documents up to 100MB should be processed successfully within 2 minutes

## Actual Behavior
Processing fails with timeout error after 30 seconds for documents >50MB

## Reproduction Steps

### Step 1: Upload a large PDF document (>50MB)

**Expected Result**: Document should be processed within 60 seconds
**Actual Result**: Processing times out after 30 seconds

**Test Data Used**:
```json
{
  "filename": "large_document.pdf",
  "size_mb": 75,
  "pages": 200
}
```


### Step 2: Check processing status in the UI

**Expected Result**: Status should show 'Processing Complete'
**Actual Result**: Status shows 'Processing Failed - Timeout'

**Screenshot**: /screenshots/timeout_error.png


## Error Trace
```

TimeoutError: Document processing exceeded maximum time limit
  at DocumentProcessor.process_pdf (document_processor.py:145)
  at ProcessingQueue.handle_job (queue_service.py:89)
  at Worker.run (worker.py:34)
        
```

## Verification
To verify this issue is fixed:
1. Follow the reproduction steps above
2. Confirm the expected behavior occurs instead of the actual behavior
3. Run any associated regression tests

## Notes
- Created: 2025-08-15 21:28:47
- Last Updated: 2025-08-15 21:28:47
