# Input Validation for AFIRGen API

## Overview

Comprehensive input validation has been implemented across all AFIRGen API endpoints to protect against common security vulnerabilities including XSS, SQL injection, and DoS attacks.

## Quick Start

### Running Tests

```bash
# Ensure the backend is running
cd "AFIRGEN FINAL/main backend"
python agentv5.py

# In another terminal, run the test suite
cd "AFIRGEN FINAL"
python test_input_validation.py
```

### Example Usage

```python
import requests

# Valid request
response = requests.post(
    "http://localhost:8000/process",
    headers={"X-API-Key": "your-api-key"},
    json={"text": "I want to report a theft that occurred yesterday..."}
)

# Invalid request (text too short)
response = requests.post(
    "http://localhost:8000/process",
    headers={"X-API-Key": "your-api-key"},
    json={"text": "short"}
)
# Returns: 400 Bad Request
```

## Features

### 1. Input Validation
- **Length Constraints**: Min/max limits for all text inputs
- **Format Validation**: Regex patterns for UUIDs, FIR numbers
- **Type Validation**: Pydantic models ensure correct data types
- **Range Validation**: Limits for pagination parameters

### 2. Security Protection
- **XSS Prevention**: HTML escaping and dangerous pattern detection
- **SQL Injection Prevention**: Parameterized queries and format validation
- **DoS Prevention**: Size limits and depth validation
- **File Upload Security**: Type, size, and extension validation

### 3. Error Handling
- **Clear Error Messages**: Descriptive messages for validation failures
- **Appropriate Status Codes**: 400, 413, 415, 422 for different errors
- **No Sensitive Data**: Error messages don't leak sensitive information

## Validation Limits

| Input Type | Minimum | Maximum | Default |
|------------|---------|---------|---------|
| Text input | 10 chars | 50,000 chars | - |
| User input | - | 10,000 chars | - |
| File size | - | 25 MB | - |
| Auth key | 8 chars | 256 chars | - |
| List limit | 1 | 100 | 20 |
| List offset | 0 | ∞ | 0 |

## Supported File Types

### Images
- JPEG (.jpg, .jpeg)
- PNG (.png)

### Audio
- WAV (.wav)
- MP3 (.mp3)
- MPEG (.mpeg)

## Validation Patterns

### Session ID
- Format: UUID v4
- Example: `550e8400-e29b-41d4-a716-446655440000`

### FIR Number
- Format: `FIR-[8 hex digits]-[14 digit timestamp]`
- Example: `FIR-12345678-20240101120000`

### Circuit Breaker Names
- Allowed: `model_server`, `asr_ocr_server`, `database`

## Common Error Responses

### Text Too Short (400)
```json
{
  "detail": "Text input too short. Minimum length: 10 characters"
}
```

### Invalid Session ID (400)
```json
{
  "detail": "Invalid session ID format"
}
```

### XSS Attempt (400)
```json
{
  "detail": "Input contains potentially dangerous content"
}
```

### File Too Large (413)
```json
{
  "detail": "File too large. Maximum size: 25.0MB"
}
```

### Invalid File Type (415)
```json
{
  "detail": "Unsupported file extension: .exe. Allowed: .jpg, .jpeg, .png, .wav, .mp3, .mpeg"
}
```

## Documentation

- **Implementation Guide**: `INPUT-VALIDATION-IMPLEMENTATION.md`
- **Quick Reference**: `INPUT-VALIDATION-QUICK-REFERENCE.md`
- **Checklist**: `INPUT-VALIDATION-CHECKLIST.md`
- **Summary**: `INPUT-VALIDATION-SUMMARY.md`

## Architecture

### Validation Module (`input_validation.py`)
```
input_validation.py
├── ValidationConstants      # Centralized limits and patterns
├── sanitize_text()         # XSS prevention
├── validate_file_upload()  # File validation
├── Pydantic Models         # Request/response validation
└── Parameter Validators    # Path/query validation
```

### Integration (`agentv5.py`)
- Import validation module
- Apply validators to all endpoints
- Use Pydantic models for request/response
- Sanitize all user inputs

## Testing

The test suite (`test_input_validation.py`) includes:

1. **Input Length Tests**: Too short, too long, valid
2. **Format Tests**: Invalid formats, valid formats
3. **XSS Tests**: Script tags, event handlers, dangerous patterns
4. **SQL Injection Tests**: Format validation, parameterized queries
5. **File Upload Tests**: Invalid types, size limits
6. **Authentication Tests**: Missing key, invalid key, valid key
7. **Pagination Tests**: Invalid limits, invalid offsets

Run all tests:
```bash
python test_input_validation.py
```

Expected output:
```
✅ PASS: 1.1 /process - No input provided
✅ PASS: 1.2 /process - Text too short
✅ PASS: 1.3 /process - Text too long
...
📊 Total: 30+ tests
```

## Maintenance

### Adding Validation to New Endpoints

1. **Define Pydantic Model** in `input_validation.py`:
```python
class NewRequest(BaseModel):
    field: constr(min_length=10, max_length=100)
    
    @validator('field')
    def sanitize_field(cls, v):
        return sanitize_text(v, allow_html=False)
```

2. **Use Model in Endpoint**:
```python
@app.post("/new-endpoint")
async def new_endpoint(request: NewRequest):
    # Field is already validated and sanitized
    pass
```

3. **Add Tests**:
```python
def test_new_endpoint():
    # Test invalid input
    resp = make_request("POST", "/new-endpoint", json={"field": "short"})
    assert resp.status_code == 422
    
    # Test valid input
    resp = make_request("POST", "/new-endpoint", json={"field": "valid input"})
    assert resp.status_code == 200
```

### Updating Validation Limits

Edit `ValidationConstants` in `input_validation.py`:
```python
class ValidationConstants:
    MAX_TEXT_LENGTH = 50_000  # Adjust as needed
    MIN_TEXT_LENGTH = 10
    # ...
```

## Security Best Practices

1. ✅ All user inputs are validated before processing
2. ✅ All user inputs are sanitized to prevent XSS
3. ✅ All database queries use parameterized statements
4. ✅ All file uploads are validated for type and size
5. ✅ All path parameters are validated with regex
6. ✅ All query parameters have range limits
7. ✅ All secrets use constant-time comparison
8. ✅ All HTML output is escaped
9. ✅ All error messages are safe (no sensitive data)
10. ✅ All endpoints have appropriate error handling

## Troubleshooting

### Test Failures

**Problem**: Tests fail with connection error
**Solution**: Ensure backend is running on `http://localhost:8000`

**Problem**: Tests fail with 401 Unauthorized
**Solution**: Update `API_KEY` in test file to match your environment

### Validation Too Strict

**Problem**: Valid inputs are being rejected
**Solution**: Review validation limits in `ValidationConstants` and adjust if needed

### Validation Too Lenient

**Problem**: Invalid inputs are being accepted
**Solution**: Add more specific validators or tighten existing limits

## Support

For issues or questions:
1. Check the documentation files
2. Review the test suite for examples
3. Check the validation module source code
4. Review error logs for specific validation failures

## License

This implementation is part of the AFIRGen project.
