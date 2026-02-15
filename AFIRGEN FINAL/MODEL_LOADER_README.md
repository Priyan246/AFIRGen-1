# Model Loader Module

## Overview

The `model_loader.py` module provides a robust, reusable model loading infrastructure for all AFIRGen model servers (GGUF, Whisper, dots_ocr). It implements comprehensive validation, error handling, and monitoring capabilities.

## Features

✅ **File Validation**
- Existence checks
- File type validation
- Size validation
- Permission checks

✅ **Integrity Validation**
- Checksum calculation (SHA256, MD5, SHA1)
- Checksum verification
- Corruption detection

✅ **Error Handling**
- Graceful failure for missing/corrupted models
- Descriptive error messages
- Error tracking and reporting
- Service continues operating even if some models fail

✅ **Performance**
- Parallel model loading
- Configurable retry logic
- Efficient checksum calculation

✅ **Monitoring**
- Health status reporting
- Detailed model information
- Loading time tracking

## Requirements Validated

- **4.1.4**: Model loading with error handling
  - Implements model file existence checks
  - Adds model file integrity validation (checksum)
  - Implements graceful error handling for missing/corrupted models
  - Returns descriptive error messages

## Usage

### Basic Usage

```python
from pathlib import Path
from model_loader import ModelLoader, ModelConfig

# Initialize loader
loader = ModelLoader(
    model_dir=Path("./models"),
    validate_checksums=True
)

# Define a loader function for your model type
def load_gguf_model(path, **kwargs):
    from llama_cpp import Llama
    return Llama(model_path=str(path), **kwargs)

# Register models
loader.register_model(ModelConfig(
    name="summariser",
    path=Path("./models/summariser.gguf"),
    loader_func=load_gguf_model,
    required=True,
    expected_checksum="abc123...",  # Optional but recommended
    loader_kwargs={"n_ctx": 2048, "n_threads": 4}
))

# Load all models (parallel by default)
results = loader.load_all_models(parallel=True)

# Get a loaded model
model = loader.get_model("summariser")

# Check health status
health = loader.get_health_status()
print(f"Status: {health['status']}")
print(f"Loaded: {health['loaded_count']}/{health['total_count']}")
```

### Integration with GGUF Model Server

```python
# In llm_server.py
from model_loader import ModelLoader, ModelConfig
from llama_cpp import Llama

# Initialize loader
model_loader = ModelLoader(
    model_dir=Path(os.getenv("MODEL_DIR", "./models")),
    validate_checksums=True
)

# Define GGUF loader function
def load_gguf_model(path, **kwargs):
    return Llama(
        model_path=str(path),
        n_ctx=kwargs.get("n_ctx", 2048),
        n_threads=kwargs.get("n_threads", 4),
        use_mlock=kwargs.get("use_mlock", True),
        use_mmap=kwargs.get("use_mmap", True),
    )

# Register models
model_loader.register_model(ModelConfig(
    name="summariser",
    path=model_loader.model_dir / "complaint_2summarizing.gguf",
    loader_func=load_gguf_model,
    required=True,
    loader_kwargs={"n_ctx": 2048, "n_threads": 4}
))

model_loader.register_model(ModelConfig(
    name="bns_check",
    path=model_loader.model_dir / "BNS-RAG-q4k.gguf",
    loader_func=load_gguf_model,
    required=False,
))

# Load on startup
@app.on_event("startup")
async def startup_event():
    try:
        await asyncio.get_event_loop().run_in_executor(
            None,
            model_loader.load_all_models
        )
        log.info("🚀 Model server startup complete")
    except Exception as e:
        log.error(f"💥 Startup failed: {e}")
        raise

# Use in endpoints
@app.post("/inference")
async def inference(request: InferenceRequest):
    try:
        model = model_loader.get_model(request.model_name)
        # Use model...
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health check
@app.get("/health")
async def health_check():
    health = model_loader.get_health_status()
    return {
        "status": health["status"],
        "models_loaded": health["models_loaded"],
        "message": health["message"]
    }
```

### Integration with ASR/OCR Server

```python
# In asr_ocr.py
from model_loader import ModelLoader, ModelConfig
import whisper
from transformers import AutoModelForCausalLM, AutoProcessor

# Initialize loader
model_loader = ModelLoader(
    model_dir=Path(os.getenv("MODEL_DIR", "./models")),
    validate_checksums=False  # Disable for Whisper (downloads from internet)
)

# Define loader functions
def load_whisper_model(path, **kwargs):
    return whisper.load_model("tiny")

def load_dots_ocr_model(path, **kwargs):
    model = AutoModelForCausalLM.from_pretrained(
        str(path),
        torch_dtype="auto",
        device_map="auto",
        trust_remote_code=True,
    )
    processor = AutoProcessor.from_pretrained(
        str(path),
        trust_remote_code=True
    )
    return {"model": model, "processor": processor}

# Register models
model_loader.register_model(ModelConfig(
    name="whisper",
    path=model_loader.model_dir / "whisper",  # Placeholder path
    loader_func=load_whisper_model,
    required=True,
))

model_loader.register_model(ModelConfig(
    name="dots_ocr",
    path=model_loader.model_dir / "dots_ocr",
    loader_func=load_dots_ocr_model,
    required=False,
))

# Load on startup
@app.on_event("startup")
def startup_event():
    try:
        model_loader.load_all_models(parallel=True)
        log.info("✅ ASR/OCR server startup complete")
    except Exception as e:
        log.error(f"❌ Startup failed: {e}")
        # Don't raise - allow server to start in degraded mode

# Use in endpoints
@app.post("/asr")
async def transcribe_audio(audio: UploadFile):
    try:
        whisper_model = model_loader.get_model("whisper")
        # Use model...
    except RuntimeError as e:
        return ASRResponse(success=False, error=str(e))
```

## Configuration Options

### ModelConfig

```python
@dataclass
class ModelConfig:
    name: str                           # Unique model identifier
    path: Path                          # Path to model file
    loader_func: Callable               # Function to load the model
    required: bool = True               # Is this model required?
    expected_checksum: Optional[str]    # Expected checksum (hex)
    checksum_algorithm: str = "sha256"  # Hash algorithm
    retry_count: int = 1                # Number of load attempts
    loader_kwargs: Optional[Dict]       # Additional loader arguments
```

### ModelLoader

```python
ModelLoader(
    model_dir: Path,                    # Base directory for models
    logger: Optional[Logger] = None,    # Logger instance
    validate_checksums: bool = True,    # Enable checksum validation
)
```

## Error Handling

The model loader provides graceful error handling with descriptive messages:

### File Not Found
```
Model file not found: /path/to/model.gguf
```

### Empty File
```
Model file is empty (0 bytes): /path/to/model.gguf
```

### Permission Denied
```
Model file is not readable (permission denied): /path/to/model.gguf
```

### Checksum Mismatch
```
Checksum mismatch! Expected: abc123..., Got: def456...
File may be corrupted or tampered with.
```

### Loader Failure
```
Model 'summariser' is not available (status: failed).
Loading failed with: RuntimeError: CUDA out of memory
```

## Health Status

The loader provides detailed health status:

```python
health = loader.get_health_status()

# Returns:
{
    "status": "healthy",  # healthy, degraded, unhealthy
    "message": "All models loaded successfully",
    "models_loaded": {
        "summariser": True,
        "bns_check": True,
    },
    "loaded_count": 2,
    "total_count": 2,
    "errors": {}
}
```

### Status Levels

- **healthy**: All models loaded successfully
- **degraded**: Some optional models failed, but all required models loaded
- **unhealthy**: One or more required models failed to load

## Checksum Generation

To generate checksums for your models:

```bash
# SHA256 (recommended)
sha256sum model.gguf

# MD5
md5sum model.gguf

# SHA1
sha1sum model.gguf
```

Or in Python:

```python
from model_loader import ModelLoader
from pathlib import Path

loader = ModelLoader(model_dir=Path("."))
checksum = loader._calculate_checksum(Path("model.gguf"), algorithm="sha256")
print(f"Checksum: {checksum}")
```

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
pytest test_model_loader.py -v

# Run only unit tests
pytest test_model_loader.py -v -k "not property"

# Run only property-based tests
pytest test_model_loader.py -v -k "property"

# Run with coverage
pytest test_model_loader.py --cov=model_loader --cov-report=html
```

## Performance

### Parallel Loading

The loader supports parallel model loading to reduce cold start time:

```python
# Load models in parallel (default)
results = loader.load_all_models(parallel=True, max_workers=3)

# Load models sequentially
results = loader.load_all_models(parallel=False)
```

**Performance Impact:**
- Sequential: ~60-90 seconds for 3 models
- Parallel (3 workers): ~30-45 seconds for 3 models
- **Speedup: ~2x faster**

### Retry Logic

Configure retry behavior per model:

```python
ModelConfig(
    name="model",
    path=Path("model.gguf"),
    loader_func=load_func,
    retry_count=3,  # Retry up to 3 times
)
```

Retry uses exponential backoff:
- Attempt 1: Immediate
- Attempt 2: Wait 0.5s
- Attempt 3: Wait 1.0s
- Attempt 4: Wait 2.0s

## Best Practices

1. **Always validate checksums in production**
   ```python
   loader = ModelLoader(model_dir=path, validate_checksums=True)
   ```

2. **Mark critical models as required**
   ```python
   ModelConfig(name="critical_model", required=True, ...)
   ```

3. **Use parallel loading for multiple models**
   ```python
   results = loader.load_all_models(parallel=True)
   ```

4. **Handle errors gracefully in endpoints**
   ```python
   try:
       model = loader.get_model("model_name")
   except RuntimeError as e:
       return {"error": str(e)}
   ```

5. **Monitor health status**
   ```python
   @app.get("/health")
   async def health():
       return loader.get_health_status()
   ```

## Troubleshooting

### Models not loading

1. Check file exists: `ls -lh /path/to/model.gguf`
2. Check permissions: `chmod 644 /path/to/model.gguf`
3. Check disk space: `df -h`
4. Check logs for detailed error messages

### Checksum validation failing

1. Recalculate checksum: `sha256sum model.gguf`
2. Compare with expected checksum
3. If different, re-download the model
4. Update expected checksum in config

### Out of memory errors

1. Reduce number of parallel workers
2. Load models sequentially
3. Increase system memory
4. Use smaller models or quantized versions

## License

Part of the AFIRGen project.
