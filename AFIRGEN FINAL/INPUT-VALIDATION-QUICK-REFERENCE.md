# Input Validation Quick Reference

## Validation Limits

| Parameter | Min | Max | Default |
|-----------|-----|-----|---------|
| Text input | 10 chars | 50,000 chars | - |
| User input | - | 10,000 chars | - |
| File size | - | 25 MB | - |
| Auth key | 8 chars | 256 chars | - |
| List limit | 1 | 100 | 20 |
| List offset | 0 | ∞ | 0 |

## Validation Patterns

| Field | Pattern | Example |
|-------|---------|---------|
| Session ID | UUID v4 | `550e8400-e29b-41d4-a716-446655440000` |
| FIR Number | `FIR-[hex8]-[timestamp14]` | `FIR-12345678-20240101120000` |
| Circuit Breaker | `model_server\|asr_ocr_server\|database` | `model_server` |

## Allowed File Types

### Images
- image/jpeg
- image/png
- image/jpg

### Audio
- audio/wav
- audio/mpeg
- audio/mp3
- audio/x-wav

### Extensions
- .jpg, .jpeg, .png
- .wav, .mp3, .mpeg

## XSS Prevention

Blocked patterns:
- `<script>` tags
- `javascript:` protocol
- Event handlers (`onclick=`, etc.)
- `<iframe>`, `<object>`, `<embed>`
- `eval()`, `expression()`

## Error Codes

| Code | Meaning | Common Causes |
|------|---------|---------------|
| 400 | Bad Request | Invalid format, dangerous content |
| 401 | Unauthorized | Missing/invalid API key |
| 404 | Not Found | Invalid session/FIR ID |
| 413 | Payload Too Large | File/text exceeds limits |
| 415 | Unsupported Media Type | Invalid file type |
| 422 | Unprocessable Entity | Pydantic validation failed |

## Testing Commands

```bash
# Run full test suite
python test_input_validation.py

# Test specific endpoint
curl -X POST http://localhost:8000/process \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"text": "Valid complaint text here..."}'

# Test with invalid input
curl -X POST http://localhost:8000/process \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"text": "short"}'  # Should return 400
```

## Common Validation Errors

### Text Too Short
```json
{
  "detail": "Text input too short. Minimum length: 10 characters"
}
```

### Invalid Session ID
```json
{
  "detail": "Invalid session ID format"
}
```

### XSS Attempt
```json
{
  "detail": "Input contains potentially dangerous content"
}
```

### File Too Large
```json
{
  "detail": "File too large. Maximum size: 25.0MB"
}
```
