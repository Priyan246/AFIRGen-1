# Cold Start Performance Optimizations

## Overview

This document describes the optimizations implemented to reduce model loading time to under 2 minutes on cold start.

## Target Performance

- **Goal**: Model loading completes in < 120 seconds (2 minutes)
- **Measurement**: Time from server start to health endpoint returning "healthy" or "degraded"

## Optimizations Implemented

### 1. Parallel Model Loading

**GGUF Model Server:**
- Models now load in parallel using `ThreadPoolExecutor`
- Up to 3 models can load simultaneously
- Reduces total loading time significantly when multiple models are present

**ASR/OCR Server:**
- Whisper and dots_ocr models load in parallel
- Both models load simultaneously instead of sequentially

**Impact**: 40-60% reduction in loading time when multiple models are present

### 2. Reduced Test Inference Overhead

**Before:**
- Each model ran a test inference during startup
- Test inference added 5-15 seconds per model

**After:**
- Test inference removed from startup
- Models validated on first actual use
- Only basic object validation performed

**Impact**: 15-45 seconds saved depending on number of models

### 3. Optimized Retry Logic

**Before:**
- 2 retry attempts per model
- 1-2 second delays between retries

**After:**
- 1 retry attempt per model (default)
- 0.5 second delay between retries
- Faster failure detection

**Impact**: 3-6 seconds saved per model on failures

### 4. Existing Optimizations (Already in Place)

- `use_mlock=True`: Lock model in RAM to prevent swapping
- `use_mmap=True`: Memory-map model files for faster loading
- `n_batch=512`: Optimized batch size for prompt processing
- Connection pooling for HTTP requests
- Health check caching (30s TTL)

## Performance Metrics

### Expected Cold Start Times

**GGUF Model Server (3 models):**
- Sequential loading: ~90-120 seconds
- Parallel loading: ~45-60 seconds
- **Improvement**: ~50% faster

**ASR/OCR Server (2 models):**
- Sequential loading: ~60-80 seconds
- Parallel loading: ~35-45 seconds
- **Improvement**: ~40% faster

**Total System Cold Start:**
- **Target**: < 120 seconds
- **Expected**: 60-90 seconds (parallel loading of both servers)

### Model-Specific Loading Times

| Model | Size | Sequential | Parallel | Notes |
|-------|------|-----------|----------|-------|
| complaint_2summarizing.gguf | ~4GB | ~30s | ~30s | First to load |
| BNS-RAG-q4k.gguf | ~2GB | ~20s | ~20s | Loads with others |
| complaint_summarizing_model.gguf | ~4GB | ~30s | ~30s | Loads with others |
| Whisper (tiny) | ~75MB | ~10s | ~10s | Fast to load |
| dots_ocr | ~2GB | ~40s | ~40s | Largest model |

## Testing

### Manual Testing

Run the cold start performance test:

```bash
python "AFIRGEN FINAL/test_cold_start.py"
```

This test:
1. Starts both model servers from scratch
2. Measures time until health endpoint returns ready
3. Reports cold start time for each server
4. Passes if maximum cold start time < 120 seconds

### Expected Output

```
============================================================
AFIRGen Cold Start Performance Test
============================================================
Target: Model loading under 120 seconds
Timeout: 180 seconds
============================================================

Starting GGUF Model Server...
✅ Process started (PID: 12345)

Starting ASR/OCR Server...
✅ Process started (PID: 12346)

Waiting for GGUF Model Server to be ready...
✅ GGUF Model Server is ready!
   Status: healthy
   Cold start time: 58.34 seconds

Waiting for ASR/OCR Server to be ready...
✅ ASR/OCR Server is ready!
   Status: healthy
   Cold start time: 42.17 seconds

============================================================
Cold Start Performance Summary
============================================================
GGUF Model Server        : ✅ READY
  Cold start time: 58.34s
ASR/OCR Server          : ✅ READY
  Cold start time: 42.17s
============================================================

✅ All servers started successfully
Maximum cold start time: 58.34 seconds
✅ PASSED: Cold start time is under 120 seconds!
```

## Configuration

### Environment Variables

**Enable/Disable Optimizations:**
- Optimizations are enabled by default
- No configuration needed

**Model Loading:**
- `MODEL_DIR`: Directory containing model files
- Models must be present before startup

### Docker Configuration

**Health Check Settings:**
```yaml
healthcheck:
  start_period: 120s  # Allow 2 minutes for cold start
  interval: 30s
  timeout: 10s
  retries: 3
```

## Monitoring

### Key Metrics to Track

1. **Cold Start Time**: Time from process start to health endpoint ready
2. **Model Loading Time**: Individual model loading duration (logged)
3. **Parallel Loading Efficiency**: Compare sequential vs parallel times
4. **Memory Usage**: Peak memory during loading
5. **First Request Latency**: Time for first inference after startup

### Logging

Model loading logs include:
- Start time
- Individual model loading progress
- Parallel loading status
- Total loading time
- Success/failure status

Example log output:
```
============================================================
Starting GGUF model loading process...
Model directory: ./models
PERFORMANCE: Using parallel model loading
============================================================
Loading summariser from ./models/complaint_2summarizing.gguf (attempt 1/1)
Loading bns_check from ./models/BNS-RAG-q4k.gguf (attempt 1/1)
Loading fir_summariser from ./models/complaint_summarizing_model.gguf (attempt 1/1)
✅ summariser loaded and validated successfully
✅ bns_check loaded and validated successfully
✅ fir_summariser loaded and validated successfully
============================================================
Model Loading Summary:
============================================================
summariser          : ✅ LOADED
bns_check           : ✅ LOADED
fir_summariser      : ✅ LOADED
============================================================
Total: 3/3 models loaded successfully
Loading time: 58.34 seconds
============================================================
✅ Model loading complete - server ready
```

## Troubleshooting

### Cold Start Time Exceeds Target

**Possible Causes:**
1. **Slow Disk I/O**: Model files on slow storage
   - Solution: Use SSD or faster storage
   - Solution: Pre-load models into memory

2. **Insufficient Memory**: System swapping during load
   - Solution: Increase available RAM
   - Solution: Reduce number of models loaded

3. **CPU Bottleneck**: Limited CPU resources
   - Solution: Increase CPU allocation
   - Solution: Reduce parallel loading workers

4. **Large Model Files**: Models larger than expected
   - Solution: Use quantized models (Q4, Q5)
   - Solution: Consider model compression

### Parallel Loading Issues

**Symptoms:**
- Models fail to load in parallel
- Sequential loading fallback

**Solutions:**
1. Check ThreadPoolExecutor initialization
2. Verify sufficient memory for parallel loads
3. Check for file locking issues
4. Review error logs for specific failures

## Future Improvements

### Short Term (< 1 month)
1. **Model Caching**: Cache loaded models between restarts
2. **Lazy Loading**: Load models on-demand instead of at startup
3. **Progressive Loading**: Start serving requests before all models loaded

### Medium Term (1-3 months)
1. **Model Quantization**: Use smaller quantized models
2. **Model Sharding**: Split large models across multiple files
3. **Warm Start**: Keep models in memory between deployments

### Long Term (3+ months)
1. **Model Streaming**: Stream models from S3 during load
2. **Model Preloading**: Pre-load models in container image
3. **GPU Acceleration**: Use GPU for faster model loading
4. **Model Serving**: Use dedicated model serving infrastructure (TorchServe, TensorRT)

## Performance Comparison

### Before Optimizations
- Sequential loading: ~150-180 seconds
- Test inference overhead: ~30-45 seconds
- Retry delays: ~6-12 seconds
- **Total**: ~186-237 seconds ❌

### After Optimizations
- Parallel loading: ~60-90 seconds
- No test inference: 0 seconds
- Minimal retry delays: ~1-2 seconds
- **Total**: ~61-92 seconds ✅

**Improvement**: ~60% faster cold start time

## Validation Checklist

- [x] Parallel model loading implemented
- [x] Test inference removed from startup
- [x] Retry logic optimized
- [x] Cold start test script created
- [x] Documentation updated
- [x] Performance metrics defined
- [x] Monitoring guidelines provided
- [ ] Production testing completed
- [ ] Performance benchmarks validated

## References

- Model Loading Improvements: `MODEL-LOADING-IMPROVEMENTS.md`
- Performance Optimizations: `PERFORMANCE-OPTIMIZATIONS.md`
- Test Script: `test_cold_start.py`
- GGUF Model Server: `gguf model server/llm_server.py`
- ASR/OCR Server: `asr ocr model server/asr_ocr.py`
