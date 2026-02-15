# Model Loading Validation & Error Handling Improvements

## Overview

This document describes the comprehensive model loading validation and error handling improvements implemented across the AFIRGen system.

## Changes Summary

### 1. GGUF Model Server (`gguf model server/llm_server.py`)

#### Enhanced ModelManager Class

**New Features:**
- **File Validation**: Validates model files before loading
  - Checks file existence
  - Verifies file is readable
  - Validates file extension (.gguf)
  - Checks file size (not empty)
  
- **Retry Logic**: Attempts to load each model up to 2 times with delays between attempts

- **Test Inference**: Validates loaded models by running a simple test inference

- **Error Tracking**: Maintains detailed error messages for each failed model in `model_errors` dict

- **Required Models**: Defines critical models (`summariser`, `fir_summariser`) that must load for server to start

- **Comprehensive Logging**: Detailed startup logs with clear status indicators

**Validation Flow:**
```
1. Check model directory exists
2. For each model:
   a. Validate file (exists, readable, correct extension, not empty)
   b. Attempt load with retry (up to 2 attempts)
   c. Run test inference to validate model works
   d. Track success/failure
3. Verify required models loaded
4. Fail startup if no models or required models missing
```

**Error Messages:**
- Clear, actionable error messages for each failure type
- Detailed summary at startup showing which models loaded/failed
- Health endpoint returns error details for debugging

### 2. ASR/OCR Server (`asr ocr model server/asr_ocr.py`)

#### Enhanced Model Loading Functions

**New Features:**
- **Retry Logic**: Both Whisper and dots_ocr loading retry up to 2 times

- **Model Validation**: 
  - Whisper: Tests with silent audio sample
  - dots_ocr: Tests with small white image
  
- **Error Tracking**: Global `MODEL_ERRORS` dict tracks loading failures

- **Required Models**: Defines Whisper as critical (OCR is optional)

- **Directory Validation**: Checks model directory exists before loading

- **Comprehensive Logging**: Detailed startup logs with status indicators

**Validation Flow:**
```
1. Check model directory exists (create if missing)
2. Load Whisper:
   a. Import whisper library
   b. Load model
   c. Test with silent audio
   d. Track success/failure
3. Load dots_ocr:
   a. Check model directory exists
   b. Load model and processor
   c. Test with white image
   d. Track success/failure
4. Log summary of loaded models
```

**Error Handling:**
- Processing functions check model availability before use
- Return detailed error messages including original loading error
- Health endpoint reports model status and errors

### 3. Main Backend (`main backend/agentv5.py`)

#### Enhanced ModelPool Class

**New Features:**
- **Health Check Validation**: Checks server health before making requests

- **Health Check Caching**: Caches health check results for 30 seconds to reduce overhead

- **Detailed Error Messages**: Propagates server error messages to caller

- **Empty Response Validation**: Validates that ASR/OCR return non-empty results

**Health Check Flow:**
```
1. Check cache for recent health check (< 30s old)
2. If not cached:
   a. Call server /health endpoint
   b. Parse status (healthy/degraded/unhealthy)
   c. Cache result
3. Return health status and message
```

**Request Flow:**
```
1. Check server health (with caching)
2. If unhealthy, fail immediately with clear error
3. Make actual request
4. Validate response
5. Return result or detailed error
```

## Health Check Endpoints

### GGUF Model Server `/health`

**Response:**
```json
{
  "status": "healthy|degraded|unhealthy",
  "models_loaded": {
    "summariser": true,
    "bns_check": false,
    "fir_summariser": true
  },
  "message": "2/3 models loaded. Errors: bns_check: Model file not found: ..."
}
```

**Status Definitions:**
- `healthy`: All models loaded
- `degraded`: Some models loaded, all required models present
- `unhealthy`: Required models missing or no models loaded

### ASR/OCR Server `/health`

**Response:**
```json
{
  "status": "healthy|degraded|unhealthy",
  "models": {
    "whisper": true,
    "dots_ocr": false
  },
  "message": "1/2 models loaded. Errors: dots_ocr: Model directory not found: ..."
}
```

**Status Definitions:**
- `healthy`: All models loaded
- `degraded`: Some models loaded, Whisper (required) present
- `unhealthy`: Whisper not loaded or no models loaded

## Testing

### Manual Testing

Run the test script to validate model loading:

```bash
python "AFIRGEN FINAL/test_model_loading.py"
```

**Tests Performed:**
1. GGUF Model Server health check
2. ASR/OCR Server health check
3. Model inference validation
4. Invalid model error handling

### Expected Behavior

**With Models Present:**
- All models load successfully
- Health checks return "healthy"
- Inference requests succeed
- Invalid model requests return 400/500 with clear error

**With Missing Models:**
- Server logs show which models failed and why
- Health checks return "degraded" or "unhealthy"
- Health response includes error details
- Processing requests fail with clear error messages

## Error Messages

### Common Error Scenarios

1. **Model File Not Found**
   ```
   Model file not found: /path/to/model.gguf
   ```
   **Solution**: Download model file to correct location

2. **Model File Empty**
   ```
   Model file is empty: /path/to/model.gguf
   ```
   **Solution**: Re-download model file

3. **Model Directory Missing**
   ```
   Model directory does not exist: /path/to/models
   ```
   **Solution**: Create directory and add model files

4. **Model Load Failed**
   ```
   Load attempt 2 failed: [Errno 2] No such file or directory
   ```
   **Solution**: Check file path and permissions

5. **Model Test Failed**
   ```
   Model test inference failed: Model returned None
   ```
   **Solution**: Model file may be corrupted, re-download

6. **Server Unhealthy**
   ```
   Model server is not healthy: Critical models not loaded: summariser
   ```
   **Solution**: Check model server logs, ensure models present

## Configuration

### Environment Variables

**GGUF Model Server:**
- `MODEL_DIR`: Directory containing GGUF model files (default: `./models`)
- `MODEL_SERVER_PORT`: Server port (default: `8001`)

**ASR/OCR Server:**
- `MODEL_DIR`: Directory containing model files (default: `./models`)
- `ASR_OCR_PORT`: Server port (default: `8002`)

### Model Paths

**GGUF Models:**
- `complaint_2summarizing.gguf` - Summarizer model (required)
- `BNS-RAG-q4k.gguf` - BNS check model (optional)
- `complaint_summarizing_model.gguf` - FIR summarizer (required)

**ASR/OCR Models:**
- Whisper: Downloaded automatically by library (required)
- dots_ocr: Must be in `{MODEL_DIR}/dots_ocr/` directory (optional)

## Benefits

1. **Early Failure Detection**: Problems detected at startup, not during processing
2. **Clear Error Messages**: Detailed errors help diagnose issues quickly
3. **Graceful Degradation**: System can run with subset of models
4. **Better Monitoring**: Health endpoints provide detailed status
5. **Reduced Downtime**: Health check caching reduces overhead
6. **Improved Reliability**: Retry logic handles transient failures

## Monitoring Recommendations

1. **Monitor Health Endpoints**: Poll `/health` every 30-60 seconds
2. **Alert on Unhealthy**: Alert when status is "unhealthy"
3. **Track Model Status**: Monitor which models are loaded
4. **Log Analysis**: Review startup logs for loading issues
5. **Performance**: Monitor health check cache hit rate

## Future Improvements

1. **Model Hot-Reloading**: Reload models without server restart
2. **Model Versioning**: Track and validate model versions
3. **S3 Integration**: Download models from S3 on startup
4. **Metrics Export**: Prometheus metrics for model loading
5. **Circuit Breaker**: Prevent cascading failures
6. **Fallback Models**: Use smaller models if primary fails
