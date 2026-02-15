# model_server.py
# -------------------------------------------------------------
# External Model Server for GGUF Models (LLM Inference)
# -------------------------------------------------------------

import os
import logging
import asyncio
from pathlib import Path
from typing import Optional, List

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import llama-cpp-python for GGUF model loading
from llama_cpp import Llama

# Import structured JSON logging
import sys
sys.path.append(str(Path(__file__).parent.parent / "main backend"))
from json_logging import setup_json_logging, log_with_context, log_error, log_performance

# Import X-Ray tracing
from xray_tracing import setup_xray, add_trace_annotation, add_trace_metadata

# Configure structured JSON logging
log = setup_json_logging(
    service_name="gguf-server",
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    log_file="logs/gguf_server.log",
    environment=os.getenv("ENVIRONMENT", "production"),
    enable_console=True
)

# Configuration
CONFIG = {
    "model_dir": Path(os.getenv("MODEL_DIR", "./models")),
    "n_ctx": 2048,  # Context length
    "n_threads": os.cpu_count() or 4,
    "n_batch": 512,  # PERFORMANCE: Batch size for prompt processing
    "verbose": False,
    "use_mlock": True,  # PERFORMANCE: Lock model in RAM to prevent swapping
    "use_mmap": True,  # PERFORMANCE: Memory-map model file for faster loading
}

# Pydantic Models
class InferenceRequest(BaseModel):
    model_name: str
    prompt: str
    max_tokens: Optional[int] = 120
    temperature: Optional[float] = 0.1
    stop: Optional[List[str]] = None

class InferenceResponse(BaseModel):
    result: str

class HealthResponse(BaseModel):
    status: str
    models_loaded: dict
    message: Optional[str] = None

# Model Manager - Loads and manages GGUF models
class ModelManager:
    def __init__(self):
        self.models = {
            "summariser": None,
            "bns_check": None, 
            "fir_summariser": None
        }
        self.model_paths = {
            "summariser": CONFIG["model_dir"] / "complaint_2summarizing.gguf",
            "bns_check": CONFIG["model_dir"] / "BNS-RAG-q4k.gguf",
            "fir_summariser": CONFIG["model_dir"] / "complaint_summarizing_model.gguf"
        }
        self.model_errors = {}  # Track loading errors for each model
        self.required_models = {"summariser", "fir_summariser"}  # Critical models

    def _validate_model_file(self, model_path: Path) -> tuple[bool, str]:
        """Validate model file exists and is readable"""
        if not model_path.exists():
            return False, f"Model file not found: {model_path}"
        
        if not model_path.is_file():
            return False, f"Path is not a file: {model_path}"
        
        if model_path.stat().st_size == 0:
            return False, f"Model file is empty: {model_path}"
        
        # Check file extension
        if not model_path.suffix.lower() == ".gguf":
            return False, f"Invalid model file extension (expected .gguf): {model_path}"
        
        # Check read permissions
        if not os.access(model_path, os.R_OK):
            return False, f"Model file is not readable: {model_path}"
        
        return True, "Valid"

    def _load_single_model(self, model_name: str, model_path: Path, retry_count: int = 1) -> bool:
        """Load a single model with validation and retry logic
        
        PERFORMANCE: Default retry_count reduced to 1 for faster cold start
        """
        # Validate file first
        is_valid, validation_msg = self._validate_model_file(model_path)
        if not is_valid:
            log.error(f"❌ {model_name} validation failed: {validation_msg}")
            self.model_errors[model_name] = validation_msg
            return False
        
        # Attempt to load with retries
        for attempt in range(retry_count):
            try:
                log.info(f"Loading {model_name} from {model_path} (attempt {attempt + 1}/{retry_count})")
                
                # PERFORMANCE: Optimized model loading parameters
                model = Llama(
                    model_path=str(model_path),
                    n_ctx=CONFIG["n_ctx"],
                    n_threads=CONFIG["n_threads"],
                    n_batch=CONFIG["n_batch"],
                    use_mlock=CONFIG["use_mlock"],
                    use_mmap=CONFIG["use_mmap"],
                    verbose=CONFIG["verbose"],
                )
                
                # PERFORMANCE: Minimal validation - just check model object is valid
                # Skip test inference during startup to reduce cold start time
                # Model will be validated on first actual use
                if model is None:
                    raise RuntimeError("Model object is None after loading")
                
                self.models[model_name] = model
                self.model_errors.pop(model_name, None)  # Clear any previous errors
                log.info(f"✅ {model_name} loaded and validated successfully")
                return True
                
            except Exception as e:
                error_msg = f"Load attempt {attempt + 1} failed: {str(e)}"
                log.warning(f"⚠️  {model_name}: {error_msg}")
                
                if attempt == retry_count - 1:  # Last attempt
                    log.error(f"❌ Failed to load {model_name} after {retry_count} attempts")
                    self.model_errors[model_name] = str(e)
                    self.models[model_name] = None
                    return False
                
                # PERFORMANCE: Minimal wait before retry
                import time
                time.sleep(0.5)
        
        return False

    def load_models(self):
        """Load all GGUF models on startup with comprehensive validation
        
        PERFORMANCE: Uses parallel loading to reduce cold start time
        """
        import concurrent.futures
        import time
        
        start_time = time.time()
        
        log.info("=" * 60)
        log.info("Starting GGUF model loading process...")
        log.info(f"Model directory: {CONFIG['model_dir']}")
        log.info("PERFORMANCE: Using parallel model loading")
        log.info("=" * 60)
        
        # Check if model directory exists
        if not CONFIG["model_dir"].exists():
            error_msg = f"Model directory does not exist: {CONFIG['model_dir']}"
            log.error(f"❌ {error_msg}")
            raise RuntimeError(error_msg)
        
        if not CONFIG["model_dir"].is_dir():
            error_msg = f"Model path is not a directory: {CONFIG['model_dir']}"
            log.error(f"❌ {error_msg}")
            raise RuntimeError(error_msg)
        
        # PERFORMANCE: Load models in parallel using ThreadPoolExecutor
        # This significantly reduces cold start time when multiple models need loading
        load_results = {}
        max_workers = min(len(self.model_paths), 3)  # Limit to 3 concurrent loads to avoid memory pressure
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all model loading tasks
            future_to_model = {
                executor.submit(self._load_single_model, model_name, model_path): model_name
                for model_name, model_path in self.model_paths.items()
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_model):
                model_name = future_to_model[future]
                try:
                    load_results[model_name] = future.result()
                    log.info(f"✅ {model_name} loading completed")
                except Exception as e:
                    log.error(f"❌ {model_name} loading failed with exception: {e}")
                    load_results[model_name] = False
                    self.model_errors[model_name] = str(e)
        
        # Analyze results
        loaded_count = sum(load_results.values())
        total_count = len(self.model_paths)
        elapsed_time = time.time() - start_time
        
        log.info("\n" + "=" * 60)
        log.info("Model Loading Summary:")
        log.info("=" * 60)
        
        for model_name, loaded in load_results.items():
            status = "✅ LOADED" if loaded else "❌ FAILED"
            log.info(f"{model_name:20s}: {status}")
            if not loaded and model_name in self.model_errors:
                log.info(f"  Error: {self.model_errors[model_name]}")
        
        log.info("=" * 60)
        log.info(f"Total: {loaded_count}/{total_count} models loaded successfully")
        log.info(f"Loading time: {elapsed_time:.2f} seconds")
        log.info("=" * 60)
        
        # Check if required models are loaded
        missing_required = [m for m in self.required_models if not load_results.get(m, False)]
        if missing_required:
            error_msg = f"Critical models failed to load: {', '.join(missing_required)}"
            log.error(f"❌ {error_msg}")
            raise RuntimeError(error_msg)
        
        if loaded_count == 0:
            raise RuntimeError("No models loaded successfully!")
        
        log.info("✅ Model loading complete - server ready")

    def get_model(self, model_name: str):
        """Get a specific model by name with detailed error reporting"""
        if model_name not in self.models:
            available = ", ".join(self.models.keys())
            raise ValueError(f"Unknown model: {model_name}. Available models: {available}")
        
        model = self.models[model_name]
        if model is None:
            error_detail = self.model_errors.get(model_name, "Unknown error")
            raise RuntimeError(
                f"Model '{model_name}' is not available. "
                f"Loading failed with: {error_detail}"
            )
        
        return model

    def inference(self, model_name: str, prompt: str, max_tokens: int = 120, 
                 temperature: float = 0.1, stop: Optional[List[str]] = None) -> str:
        """Run inference on specified model with error handling"""
        try:
            model = self.get_model(model_name)
            
            # Validate inputs
            if not prompt or not isinstance(prompt, str):
                raise ValueError("Prompt must be a non-empty string")
            
            if max_tokens <= 0:
                raise ValueError(f"max_tokens must be positive, got {max_tokens}")
            
            if not 0 <= temperature <= 2:
                raise ValueError(f"temperature must be between 0 and 2, got {temperature}")
            
            # Prepare generation parameters
            generate_params = {
                "max_tokens": max_tokens,
                "temperature": temperature,
                "echo": False,  # Don't include prompt in response
            }
            
            if stop:
                generate_params["stop"] = stop
            
            # Run inference
            result = model(prompt, **generate_params)
            
            # Extract text from response
            if isinstance(result, dict) and "choices" in result:
                generated_text = result["choices"][0]["text"].strip()
            else:
                generated_text = str(result).strip()
            
            # Validate output
            if not generated_text:
                log.warning(f"Model {model_name} returned empty output")
                return ""
            
            return generated_text
                
        except (ValueError, RuntimeError) as e:
            # Re-raise validation and model errors
            log.error(f"Inference error for {model_name}: {e}")
            raise
        except Exception as e:
            # Catch unexpected errors
            log.error(f"Unexpected inference error for {model_name}: {e}", exc_info=True)
            raise RuntimeError(f"Inference failed unexpectedly: {e}")

# Global model manager
model_manager = ModelManager()

# FastAPI app
app = FastAPI(title="GGUF Model Server", version="1.0.0")

# Setup X-Ray distributed tracing
setup_xray(app, service_name="afirgen-gguf-server")

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
async def startup_event():
    """Load models on startup"""
    try:
        # Run model loading in thread pool to avoid blocking
        await asyncio.get_event_loop().run_in_executor(None, model_manager.load_models)
        log.info("🚀 Model server startup complete")
    except Exception as e:
        log.error(f"💥 Startup failed: {e}")
        raise

@app.post("/inference", response_model=InferenceResponse)
async def inference(request: InferenceRequest):
    """Run inference on specified model"""
    # Add X-Ray annotations
    add_trace_annotation("model_name", request.model_name)
    add_trace_annotation("max_tokens", request.max_tokens)
    add_trace_metadata("prompt_length", len(request.prompt))
    
    try:
        # Validate model name
        if request.model_name not in model_manager.models:
            add_trace_annotation("error", "invalid_model")
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid model_name: {request.model_name}. Available: {list(model_manager.models.keys())}"
            )
        
        # Run inference in thread pool to avoid blocking
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            model_manager.inference,
            request.model_name,
            request.prompt,
            request.max_tokens,
            request.temperature,
            request.stop
        )
        
        return InferenceResponse(result=result)
        
    except RuntimeError as e:
        log.error(f"Inference error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        log.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check server health and model status with detailed diagnostics"""
    try:
        models_status = {
            name: model is not None 
            for name, model in model_manager.models.items()
        }
        
        loaded_models = sum(models_status.values())
        total_models = len(models_status)
        
        # Determine health status
        if loaded_models == total_models:
            status = "healthy"
            message = "All models loaded successfully"
        elif loaded_models > 0:
            # Check if required models are loaded
            missing_required = [m for m in model_manager.required_models 
                              if not models_status.get(m, False)]
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
        if model_manager.model_errors:
            error_summary = "; ".join([f"{k}: {v}" for k, v in model_manager.model_errors.items()])
            message = f"{message}. Errors: {error_summary}"
        
        return HealthResponse(
            status=status,
            models_loaded=models_status,
            message=message
        )
        
    except Exception as e:
        log.error(f"Health check error: {e}")
        return HealthResponse(
            status="unhealthy",
            models_loaded={},
            message=f"Health check failed: {e}"
        )

@app.get("/")
async def root():
    """Root endpoint with basic info"""
    return {
        "service": "GGUF Model Server",
        "version": "1.0.0",
        "endpoints": {
            "inference": "POST /inference",
            "health": "GET /health"
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "model_server:app",
        host="0.0.0.0", 
        port=int(os.getenv("MODEL_SERVER_PORT", 8001)),
        log_level="info"
    )
