# input_validation.py
# -------------------------------------------------------------
# Comprehensive Input Validation for AFIRGen API
# -------------------------------------------------------------
import re
import string
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator, constr, conint
from enum import Enum
from fastapi import HTTPException, UploadFile
import logging

# Note: Logger will be configured by json_logging module when imported by main application
log = logging.getLogger("validation")

# ------------------------------------------------------------- VALIDATION CONSTANTS
class ValidationConstants:
    """Centralized validation constants"""
    # Text limits
    MAX_TEXT_LENGTH = 50_000
    MIN_TEXT_LENGTH = 10
    MAX_USER_INPUT_LENGTH = 10_000
    MAX_FIR_NUMBER_LENGTH = 50
    MAX_AUTH_KEY_LENGTH = 256
    
    # File limits
    MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB
    
    # Allowed MIME types
    ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/jpg"}
    ALLOWED_AUDIO_TYPES = {"audio/wav", "audio/mpeg", "audio/mp3", "audio/x-wav"}
    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".wav", ".mp3", ".mpeg"}
    
    # Regex patterns
    UUID_PATTERN = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    FIR_NUMBER_PATTERN = r'^FIR-[a-f0-9]{8}-\d{14}$'
    ALPHANUMERIC_PATTERN = r'^[a-zA-Z0-9_-]+$'
    
    # Dangerous patterns for XSS/injection prevention
    DANGEROUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',  # Event handlers like onclick=
        r'<iframe',
        r'<object',
        r'<embed',
        r'eval\s*\(',
        r'expression\s*\(',
    ]

# ------------------------------------------------------------- SANITIZATION FUNCTIONS
def sanitize_text(text: str, allow_html: bool = False) -> str:
    """
    Sanitize text input to prevent XSS and injection attacks
    
    Args:
        text: Input text to sanitize
        allow_html: If False, escape HTML characters
    
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove non-printable characters except newlines and tabs
    text = ''.join(ch for ch in text if ch in string.printable or ch in '\n\t')
    
    # Check for dangerous patterns
    for pattern in ValidationConstants.DANGEROUS_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            log.warning(f"Dangerous pattern detected in input: {pattern}")
            raise HTTPException(
                status_code=400,
                detail="Input contains potentially dangerous content"
            )
    
    # Escape HTML if not allowed
    if not allow_html:
        text = text.replace('<', '&lt;').replace('>', '&gt;')
        text = text.replace('"', '&quot;').replace("'", '&#x27;')
    
    return text.strip()

def validate_file_upload(file: UploadFile, allowed_types: set, max_size: int = ValidationConstants.MAX_FILE_SIZE) -> None:
    """
    Validate uploaded file
    
    Args:
        file: UploadFile object
        allowed_types: Set of allowed MIME types
        max_size: Maximum file size in bytes
    
    Raises:
        HTTPException: If validation fails
    """
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Check filename
    if not file.filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    # Check extension
    from pathlib import Path
    ext = Path(file.filename).suffix.lower()
    if ext not in ValidationConstants.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file extension: {ext}. Allowed: {', '.join(ValidationConstants.ALLOWED_EXTENSIONS)}"
        )
    
    # Check MIME type
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported content type: {file.content_type}. Allowed: {', '.join(allowed_types)}"
        )
    
    # Check file size (if available)
    if hasattr(file, 'size') and file.size:
        if file.size > max_size:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {max_size / (1024*1024):.1f}MB"
            )

# ------------------------------------------------------------- VALIDATION STEP ENUM
class ValidationStep(str, Enum):
    TRANSCRIPT_REVIEW = "transcript_review"
    SUMMARY_REVIEW = "summary_review"
    VIOLATIONS_REVIEW = "violations_review"
    FIR_NARRATIVE_REVIEW = "fir_narrative_review"
    FINAL_REVIEW = "final_review"

# ------------------------------------------------------------- VALIDATED REQUEST MODELS
class ProcessRequest(BaseModel):
    """Validated request model for /process endpoint"""
    text: Optional[constr(min_length=ValidationConstants.MIN_TEXT_LENGTH, max_length=ValidationConstants.MAX_TEXT_LENGTH)] = None
    
    @validator('text')
    def sanitize_text_input(cls, v):
        if v:
            return sanitize_text(v, allow_html=False)
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "I want to report a theft that occurred yesterday..."
            }
        }

class ValidationRequest(BaseModel):
    """Validated request model for /validate endpoint"""
    session_id: constr(regex=ValidationConstants.UUID_PATTERN)
    approved: bool
    user_input: Optional[constr(max_length=ValidationConstants.MAX_USER_INPUT_LENGTH)] = None
    regenerate: bool = False
    
    @validator('session_id')
    def validate_session_id(cls, v):
        if not re.match(ValidationConstants.UUID_PATTERN, v, re.IGNORECASE):
            raise ValueError("Invalid session ID format")
        return v.lower()
    
    @validator('user_input')
    def sanitize_user_input(cls, v):
        if v:
            return sanitize_text(v, allow_html=False)
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "approved": True,
                "user_input": "Additional context about the incident",
                "regenerate": False
            }
        }

class RegenerateRequest(BaseModel):
    """Validated request model for /regenerate endpoint"""
    session_id: constr(regex=ValidationConstants.UUID_PATTERN)
    step: ValidationStep
    user_input: Optional[constr(max_length=ValidationConstants.MAX_USER_INPUT_LENGTH)] = None
    
    @validator('session_id')
    def validate_session_id(cls, v):
        if not re.match(ValidationConstants.UUID_PATTERN, v, re.IGNORECASE):
            raise ValueError("Invalid session ID format")
        return v.lower()
    
    @validator('user_input')
    def sanitize_user_input(cls, v):
        if v:
            return sanitize_text(v, allow_html=False)
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "step": "summary_review",
                "user_input": "Please include more details about the suspect"
            }
        }

class AuthRequest(BaseModel):
    """Validated request model for /authenticate endpoint"""
    fir_number: constr(regex=ValidationConstants.FIR_NUMBER_PATTERN, max_length=ValidationConstants.MAX_FIR_NUMBER_LENGTH)
    auth_key: constr(min_length=8, max_length=ValidationConstants.MAX_AUTH_KEY_LENGTH)
    
    @validator('fir_number')
    def validate_fir_number(cls, v):
        if not re.match(ValidationConstants.FIR_NUMBER_PATTERN, v):
            raise ValueError("Invalid FIR number format")
        return v
    
    @validator('auth_key')
    def validate_auth_key(cls, v):
        if not v or len(v.strip()) < 8:
            raise ValueError("Auth key must be at least 8 characters")
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "fir_number": "FIR-12345678-20240101120000",
                "auth_key": "your-secret-auth-key"
            }
        }

class CircuitBreakerResetRequest(BaseModel):
    """Validated request model for circuit breaker reset"""
    name: constr(regex=r'^[a-z_]+$')
    
    @validator('name')
    def validate_name(cls, v):
        allowed_names = {'model_server', 'asr_ocr_server', 'database'}
        if v not in allowed_names:
            raise ValueError(f"Invalid circuit breaker name. Allowed: {', '.join(allowed_names)}")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "model_server"
            }
        }

# ------------------------------------------------------------- PATH PARAMETER VALIDATORS
def validate_session_id_param(session_id: str) -> str:
    """Validate session_id path parameter"""
    if not re.match(ValidationConstants.UUID_PATTERN, session_id, re.IGNORECASE):
        raise HTTPException(status_code=400, detail="Invalid session ID format")
    return session_id.lower()

def validate_fir_number_param(fir_number: str) -> str:
    """Validate fir_number path parameter"""
    if not re.match(ValidationConstants.FIR_NUMBER_PATTERN, fir_number):
        raise HTTPException(status_code=400, detail="Invalid FIR number format")
    return fir_number

def validate_circuit_breaker_name(name: str) -> str:
    """Validate circuit breaker name parameter"""
    allowed_names = {'model_server', 'asr_ocr_server', 'database'}
    if name not in allowed_names:
        raise HTTPException(
            status_code=404,
            detail=f"Circuit breaker '{name}' not found. Allowed: {', '.join(allowed_names)}"
        )
    return name

def validate_recovery_name(name: str) -> str:
    """Validate recovery handler name parameter"""
    allowed_names = {'model_server', 'asr_ocr_server', 'database'}
    if name not in allowed_names:
        raise HTTPException(
            status_code=404,
            detail=f"Recovery handler '{name}' not found. Allowed: {', '.join(allowed_names)}"
        )
    return name

# ------------------------------------------------------------- QUERY PARAMETER VALIDATORS
def validate_limit_param(limit: Optional[int] = None, default: int = 100, max_limit: int = 1000) -> int:
    """Validate limit query parameter"""
    if limit is None:
        return default
    
    if limit < 1:
        raise HTTPException(status_code=400, detail="Limit must be at least 1")
    
    if limit > max_limit:
        raise HTTPException(status_code=400, detail=f"Limit cannot exceed {max_limit}")
    
    return limit

def validate_offset_param(offset: Optional[int] = None, default: int = 0) -> int:
    """Validate offset query parameter"""
    if offset is None:
        return default
    
    if offset < 0:
        raise HTTPException(status_code=400, detail="Offset cannot be negative")
    
    return offset

# ------------------------------------------------------------- RESPONSE MODELS
class FIRResp(BaseModel):
    """Response model for /process endpoint"""
    success: bool
    session_id: str
    fir_number: Optional[str] = None
    fir_content: Optional[str] = None
    error: Optional[str] = None
    steps: List[str] = Field(default_factory=list)
    requires_validation: bool = False
    current_step: Optional[ValidationStep] = None
    content_for_validation: Optional[Dict[str, Any]] = None

class ValidationResponse(BaseModel):
    """Response model for /validate endpoint"""
    success: bool
    session_id: str
    current_step: ValidationStep
    content: Dict[str, Any]
    message: str
    requires_validation: bool = True
    completed: bool = False

class AuthResponse(BaseModel):
    """Response model for /authenticate endpoint"""
    success: bool
    message: str
    fir_number: Optional[str] = None

class ErrorResponse(BaseModel):
    """Standard error response model"""
    detail: str
    error_code: Optional[str] = None
    timestamp: Optional[str] = None

# ------------------------------------------------------------- VALIDATION UTILITIES
def validate_request_size(content_length: Optional[int], max_size: int = 10 * 1024 * 1024) -> None:
    """
    Validate request body size
    
    Args:
        content_length: Content-Length header value
        max_size: Maximum allowed size in bytes
    
    Raises:
        HTTPException: If request is too large
    """
    if content_length and content_length > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"Request body too large. Maximum size: {max_size / (1024*1024):.1f}MB"
        )

def validate_json_depth(data: Any, max_depth: int = 10, current_depth: int = 0) -> None:
    """
    Validate JSON nesting depth to prevent DoS attacks
    
    Args:
        data: JSON data to validate
        max_depth: Maximum allowed nesting depth
        current_depth: Current depth (used in recursion)
    
    Raises:
        HTTPException: If nesting is too deep
    """
    if current_depth > max_depth:
        raise HTTPException(
            status_code=400,
            detail=f"JSON nesting too deep. Maximum depth: {max_depth}"
        )
    
    if isinstance(data, dict):
        for value in data.values():
            validate_json_depth(value, max_depth, current_depth + 1)
    elif isinstance(data, list):
        for item in data:
            validate_json_depth(item, max_depth, current_depth + 1)

# ------------------------------------------------------------- LOGGING
log.info("Input validation module loaded successfully")
