# asr_ocr_server.py
# -------------------------------------------------------------
# Separate ASR/OCR Server for Whisper and dots_ocr processing
# -------------------------------------------------------------

import os
import logging
import tempfile
import uuid
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import structured JSON logging
import sys
sys.path.append(str(Path(__file__).parent.parent / "main backend"))
from json_logging import setup_json_logging, log_with_context, log_error, log_performance

# Import X-Ray tracing
from xray_tracing import setup_xray, add_trace_annotation, add_trace_metadata

# Configure structured JSON logging
log = setup_json_logging(
    service_name="asr-ocr-server",
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    log_file="logs/asr_ocr_server.log",
    environment=os.getenv("ENVIRONMENT", "production"),
    enable_console=True
)

# Configuration
CONFIG = {
    "max_file_size": 25 * 1024 * 1024,  # 25MB
    "allowed_audio": {"audio/wav", "audio/mpeg", "audio/mp3"},
    "allowed_image": {"image/jpeg", "image/png", "image/jpg"},
    "model_dir": Path(os.getenv("MODEL_DIR", "./models")),
    "temp_dir": Path("./temp_asr_ocr"),
}

CONFIG["temp_dir"].mkdir(exist_ok=True)

# Response models
class ASRResponse(BaseModel):
    success: bool
    transcript: Optional[str] = None
    error: Optional[str] = None

class OCRResponse(BaseModel):
    success: bool
    extracted_text: Optional[str] = None
    error: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    models: dict
    message: Optional[str] = None

# Global model storage
MODELS = {
    "whisper": None,
    "dots_model": None,
    "dots_processor": None
}

# Track model loading errors
MODEL_ERRORS = {}

# Required models (at least one must load)
REQUIRED_MODELS = ["whisper"]  # Whisper is more critical than OCR

def sanitise_text(text: str) -> str:
    """Clean and sanitize extracted text"""
    if not text:
        return ""
    import re
    import string
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    text = "".join(ch for ch in text if ch in string.printable)
    return text

def load_whisper_model(retry_count: int = 1):
    """Load Whisper model for ASR with validation and retry logic
    
    PERFORMANCE: Default retry_count reduced to 1 for faster cold start
    """
    for attempt in range(retry_count):
        try:
            log.info(f"Loading Whisper model (attempt {attempt + 1}/{retry_count})...")
            import whisper
            
            # Load model (you can change to "base", "small", etc.)
            model = whisper.load_model("tiny")
            
            # Validate model loaded correctly
            if model is None:
                raise RuntimeError("Whisper model loaded but returned None")
            
            # PERFORMANCE: Skip test inference during startup to reduce cold start time
            # Model will be validated on first actual use
            
            MODELS["whisper"] = model
            MODEL_ERRORS.pop("whisper", None)  # Clear any previous errors
            log.info("✅ Whisper model loaded and validated successfully")
            return True
            
        except Exception as e:
            error_msg = f"Load attempt {attempt + 1} failed: {str(e)}"
            log.warning(f"⚠️  Whisper: {error_msg}")
            
            if attempt == retry_count - 1:  # Last attempt
                log.error(f"❌ Failed to load Whisper model after {retry_count} attempts")
                MODEL_ERRORS["whisper"] = str(e)
                MODELS["whisper"] = None
                return False
            
            # PERFORMANCE: Minimal wait before retry
            import time
            time.sleep(0.5)
    
    return False

def load_dots_ocr_model(retry_count: int = 1):
    """Load dots_ocr model for OCR with validation and retry logic
    
    PERFORMANCE: Default retry_count reduced to 1 for faster cold start
    """
    model_path = CONFIG["model_dir"] / "dots_ocr"
    
    # Validate model directory exists
    if not model_path.exists():
        error_msg = f"dots_ocr model directory not found: {model_path}"
        log.error(f"❌ {error_msg}")
        MODEL_ERRORS["dots_ocr"] = error_msg
        return False
    
    if not model_path.is_dir():
        error_msg = f"dots_ocr path is not a directory: {model_path}"
        log.error(f"❌ {error_msg}")
        MODEL_ERRORS["dots_ocr"] = error_msg
        return False
    
    for attempt in range(retry_count):
        try:
            log.info(f"Loading dots_ocr model (attempt {attempt + 1}/{retry_count})...")
            from transformers import AutoModelForCausalLM, AutoProcessor
            import torch
            
            device_map = "auto" if torch.cuda.is_available() else "cpu"
            torch_dtype = "auto" if torch.cuda.is_available() else torch.float32
            
            log.info(f"Loading model from {model_path} (device: {device_map})")
            
            model = AutoModelForCausalLM.from_pretrained(
                str(model_path),
                torch_dtype=torch_dtype,
                device_map=device_map,
                trust_remote_code=True,
            )
            processor = AutoProcessor.from_pretrained(
                str(model_path), 
                trust_remote_code=True
            )
            
            # Validate models loaded
            if model is None or processor is None:
                raise RuntimeError("Model or processor loaded but returned None")
            
            # PERFORMANCE: Skip test inference during startup to reduce cold start time
            # Model will be validated on first actual use
            
            MODELS["dots_model"] = model
            MODELS["dots_processor"] = processor
            MODEL_ERRORS.pop("dots_ocr", None)  # Clear any previous errors
            log.info("✅ dots_ocr model loaded and validated successfully")
            return True
            
        except Exception as e:
            error_msg = f"Load attempt {attempt + 1} failed: {str(e)}"
            log.warning(f"⚠️  dots_ocr: {error_msg}")
            
            if attempt == retry_count - 1:  # Last attempt
                log.error(f"❌ Failed to load dots_ocr model after {retry_count} attempts")
                MODEL_ERRORS["dots_ocr"] = str(e)
                MODELS["dots_model"] = None
                MODELS["dots_processor"] = None
                return False
            
            # PERFORMANCE: Minimal wait before retry
            import time
            time.sleep(0.5)
    
    return False

def process_audio_file(file_path: str) -> str:
    """Process audio file with Whisper"""
    if MODELS["whisper"] is None:
        error_detail = MODEL_ERRORS.get("whisper", "Model not loaded")
        raise RuntimeError(f"Whisper model not available: {error_detail}")
    
    try:
        result = MODELS["whisper"].transcribe(file_path)
        
        # Validate result
        if result is None or "text" not in result:
            raise RuntimeError("Whisper returned invalid result")
        
        return sanitise_text(result["text"])
        
    except Exception as e:
        log.error(f"Audio processing failed: {e}")
        raise RuntimeError(f"ASR processing failed: {e}")

def process_image_file(file_path: str) -> str:
    """Process image file with dots_ocr"""
    if MODELS["dots_model"] is None or MODELS["dots_processor"] is None:
        error_detail = MODEL_ERRORS.get("dots_ocr", "Model not loaded")
        raise RuntimeError(f"dots_ocr model not available: {error_detail}")
    
    try:
        from PIL import Image
        import torch
        
        device = next(MODELS["dots_model"].parameters()).device
        
        with Image.open(file_path) as img:
            img = img.convert("RGB")
            
            # Validate image
            if img.size[0] == 0 or img.size[1] == 0:
                raise ValueError("Invalid image dimensions")
            
            prompt = "Extract the text from this image in plain text."
            inputs = MODELS["dots_processor"](text=prompt, images=img, return_tensors="pt")
            
            if inputs is None or "input_ids" not in inputs:
                raise RuntimeError("Processor failed to create inputs")
            
            inputs = {k: v.to(device) if isinstance(v, torch.Tensor) else v 
                     for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = MODELS["dots_model"].generate(**inputs, max_new_tokens=1024)
            
            if outputs is None or len(outputs) == 0:
                raise RuntimeError("Model generated no output")
            
            generated_text = MODELS["dots_processor"].decode(
                outputs[0][len(inputs['input_ids'][0]):], 
                skip_special_tokens=True
            )
            
            return sanitise_text(generated_text)
            
    except Exception as e:
        log.error(f"Image processing failed: {e}")
        raise RuntimeError(f"OCR processing failed: {e}")

# FastAPI app
app = FastAPI(title="ASR/OCR Server", version="1.0.0")

# Setup X-Ray distributed tracing
setup_xray(app, service_name="afirgen-asr-ocr-server")

# CORS Configuration - Load from environment variable
cors_origins_env = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000")
cors_origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]

if "*" in cors_origins:
    log.warning("⚠️  CORS configured with wildcard (*) - This should only be used in development!")

log.info(f"CORS allowed origins: {cors_origins}")

# Use enhanced CORS middleware with validation and logging
import sys
sys.path.append("..")
from cors_middleware import setup_cors_middleware

setup_cors_middleware(
    app,
    cors_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    max_age=3600,
    use_enhanced=True,
)

@app.on_event("startup")
def startup_event():
    """Load models on startup with comprehensive validation
    
    PERFORMANCE: Uses parallel loading to reduce cold start time
    """
    import concurrent.futures
    import time
    
    start_time = time.time()
    
    log.info("=" * 60)
    log.info("Starting ASR/OCR server...")
    log.info(f"Model directory: {CONFIG['model_dir']}")
    log.info("PERFORMANCE: Using parallel model loading")
    log.info("=" * 60)
    
    # Check if model directory exists
    if not CONFIG["model_dir"].exists():
        log.warning(f"⚠️  Model directory does not exist: {CONFIG['model_dir']}")
        log.warning("Creating model directory...")
        CONFIG["model_dir"].mkdir(parents=True, exist_ok=True)
    
    # PERFORMANCE: Load models in parallel
    # Whisper and dots_ocr can load simultaneously
    load_results = {}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        # Submit both model loading tasks
        future_whisper = executor.submit(load_whisper_model)
        future_dots = executor.submit(load_dots_ocr_model)
        
        # Collect results
        try:
            load_results['whisper'] = future_whisper.result()
        except Exception as e:
            log.error(f"Whisper loading failed with exception: {e}")
            load_results['whisper'] = False
        
        try:
            load_results['dots_ocr'] = future_dots.result()
        except Exception as e:
            log.error(f"dots_ocr loading failed with exception: {e}")
            load_results['dots_ocr'] = False
    
    whisper_loaded = load_results.get('whisper', False)
    dots_loaded = load_results.get('dots_ocr', False)
    elapsed_time = time.time() - start_time
    
    log.info("\n" + "=" * 60)
    log.info("Model Loading Summary:")
    log.info("=" * 60)
    log.info(f"Whisper (ASR):  {'✅ LOADED' if whisper_loaded else '❌ FAILED'}")
    if not whisper_loaded and "whisper" in MODEL_ERRORS:
        log.info(f"  Error: {MODEL_ERRORS['whisper']}")
    
    log.info(f"dots_ocr (OCR): {'✅ LOADED' if dots_loaded else '❌ FAILED'}")
    if not dots_loaded and "dots_ocr" in MODEL_ERRORS:
        log.info(f"  Error: {MODEL_ERRORS['dots_ocr']}")
    log.info("=" * 60)
    log.info(f"Loading time: {elapsed_time:.2f} seconds")
    log.info("=" * 60)
    
    if not whisper_loaded:
        log.warning("⚠️  Whisper model failed to load - ASR will be unavailable")
    if not dots_loaded:
        log.warning("⚠️  dots_ocr model failed to load - OCR will be unavailable")
    
    if not (whisper_loaded or dots_loaded):
        log.error("❌ No models loaded successfully!")
        log.error("Server will start but all processing requests will fail")
    else:
        log.info("✅ ASR/OCR server startup complete")

@app.post("/asr", response_model=ASRResponse)
async def transcribe_audio(audio: UploadFile = File(...)):
    """Transcribe audio file using Whisper"""
    # Add X-Ray annotations
    add_trace_annotation("operation", "asr")
    add_trace_annotation("content_type", audio.content_type)
    
    try:
        # Validate file
        if audio.content_type not in CONFIG["allowed_audio"]:
            add_trace_annotation("error", "invalid_content_type")
            raise HTTPException(status_code=415, detail=f"Unsupported audio format: {audio.content_type}")
        
        content = await audio.read()
        if len(content) > CONFIG["max_file_size"]:
            raise HTTPException(status_code=413, detail="Audio file too large")
        
        # Save temporary file
        suffix = Path(audio.filename).suffix.lower() if audio.filename else ".wav"
        temp_file = CONFIG["temp_dir"] / f"{uuid.uuid4().hex}{suffix}"
        
        try:
            temp_file.write_bytes(content)
            transcript = process_audio_file(str(temp_file))
            
            return ASRResponse(
                success=True,
                transcript=transcript
            )
            
        finally:
            # Cleanup temp file
            if temp_file.exists():
                temp_file.unlink()
                
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"ASR processing error: {e}")
        return ASRResponse(
            success=False,
            error=str(e)
        )

@app.post("/ocr", response_model=OCRResponse)
async def extract_text_from_image(image: UploadFile = File(...)):
    """Extract text from image using dots_ocr"""
    # Add X-Ray annotations
    add_trace_annotation("operation", "ocr")
    add_trace_annotation("content_type", image.content_type)
    
    try:
        # Validate file
        if image.content_type not in CONFIG["allowed_image"]:
            add_trace_annotation("error", "invalid_content_type")
            raise HTTPException(status_code=415, detail=f"Unsupported image format: {image.content_type}")
        
        content = await image.read()
        if len(content) > CONFIG["max_file_size"]:
            raise HTTPException(status_code=413, detail="Image file too large")
        
        # Save temporary file
        suffix = Path(image.filename).suffix.lower() if image.filename else ".jpg"
        temp_file = CONFIG["temp_dir"] / f"{uuid.uuid4().hex}{suffix}"
        
        try:
            temp_file.write_bytes(content)
            extracted_text = process_image_file(str(temp_file))
            
            return OCRResponse(
                success=True,
                extracted_text=extracted_text
            )
            
        finally:
            # Cleanup temp file
            if temp_file.exists():
                temp_file.unlink()
                
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"OCR processing error: {e}")
        return OCRResponse(
            success=False,
            error=str(e)
        )

@app.get("/health", response_model=HealthResponse)
def health_check():
    """Check server health and model status with detailed diagnostics"""
    models_status = {
        "whisper": MODELS["whisper"] is not None,
        "dots_ocr": MODELS["dots_model"] is not None and MODELS["dots_processor"] is not None
    }
    
    loaded_models = sum(models_status.values())
    total_models = len(models_status)
    
    # Determine health status
    if loaded_models == total_models:
        status = "healthy"
        message = "All models loaded successfully"
    elif loaded_models > 0:
        # Check if required models are loaded
        missing_required = [m for m in REQUIRED_MODELS if not models_status.get(m, False)]
        if missing_required:
            status = "unhealthy"
            message = f"Critical models not loaded: {', '.join(missing_required)}"
        else:
            status = "degraded"
            message = f"{loaded_models}/{total_models} models loaded (optional models missing)"
    else:
        status = "unhealthy"
        message = "No models loaded"
    
    # Add error details for failed models
    if MODEL_ERRORS:
        error_summary = "; ".join([f"{k}: {v}" for k, v in MODEL_ERRORS.items()])
        message = f"{message}. Errors: {error_summary}"
    
    return HealthResponse(
        status=status,
        models=models_status,
        message=message
    )

if __name__ == "__main__":
    uvicorn.run(
        "asr_ocr_server:app", 
        host="0.0.0.0", 
        port=int(os.getenv("ASR_OCR_PORT", 8002))
    )
