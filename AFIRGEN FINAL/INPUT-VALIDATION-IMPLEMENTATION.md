# Input Validation Implementation Guide

## Overview

Comprehensive input validation has been implemented across all AFIRGen API endpoints to prevent security vulnerabilities including XSS, SQL injection, and DoS attacks.

## Implementation Details

### 1. Validation Module (`input_validation.py`)

A dedicated validation module provides:
- Centralized validation constants
- Sanitization functions
- Pydantic request/response models
- Path and query parameter validators

### 2. Security Features

#### XSS Prevention
- HTML escaping for all user inputs
- Detection of dangerous patterns (script tags, event handlers)
- Content sanitization before processing

#### SQL Injection Prevention
- Parameterized queries throughout
- Input format validation (UUID, FIR number patterns)
- Regex-based validation for all identifiers

#### DoS Prevention
- Request size limits
- JSON nesting depth validation
- Rate limiting (already implemented)
- File size validation

### 3. Validated Endpoints

All endpoints now have comprehensive input validation:


#### POST /process
- Text length validation (10-50,000 characters)
- File type and size validation
- XSS pattern detection
- Single input type enforcement

#### POST /validate
- UUID format validation for session_id
- User input length limits (max 10,000 chars)
- XSS sanitization
- Pydantic model validation

#### GET /session/{session_id}/status
- UUID format validation
- Session existence check

#### POST /regenerate/{session_id}
- UUID format validation
- ValidationStep enum validation
- User input sanitization

#### POST /authenticate
- FIR number format validation (FIR-[hex8]-[timestamp14])
- Auth key length validation (min 8 chars)
- Constant-time comparison for auth keys

#### GET /fir/{fir_number}
- FIR number format validation
- SQL injection prevention

#### GET /list_firs
- Pagination parameter validation
- Limit: 1-100 (default 20)
- Offset: >= 0 (default 0)

#### POST /reliability/circuit-breaker/{name}/reset
- Allowed names: model_server, asr_ocr_server, database
- Name format validation

## Testing

Run the comprehensive test suite:

```bash
python test_input_validation.py
```

The test suite validates:
- Input length constraints
- Format validation
- XSS prevention
- SQL injection prevention
- Authentication requirements
- Error handling

## Configuration

Validation constants in `input_validation.py`:
- MAX_TEXT_LENGTH: 50,000 characters
- MIN_TEXT_LENGTH: 10 characters
- MAX_USER_INPUT_LENGTH: 10,000 characters
- MAX_FILE_SIZE: 25MB
- MAX_FIR_NUMBER_LENGTH: 50 characters

## Security Best Practices

1. All user inputs are sanitized before processing
2. HTML is escaped by default
3. Dangerous patterns are detected and rejected
4. File uploads are validated for type and size
5. Path parameters are validated with regex patterns
6. Query parameters have range limits
7. Constant-time comparison for secrets

## Error Responses

Validation errors return appropriate HTTP status codes:
- 400: Bad Request (invalid input format)
- 413: Payload Too Large (file/text too large)
- 415: Unsupported Media Type (invalid file type)
- 422: Unprocessable Entity (Pydantic validation error)

## Maintenance

To add validation to new endpoints:

1. Define Pydantic models in `input_validation.py`
2. Add validators using `@validator` decorator
3. Use validation functions for path/query parameters
4. Add tests to `test_input_validation.py`
