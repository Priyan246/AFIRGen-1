# CORS Configuration Guide

## Overview

All three AFIRGen services (Main Backend, GGUF Model Server, and ASR/OCR Server) now support configurable CORS (Cross-Origin Resource Sharing) origins instead of allowing all origins with the wildcard `*`.

## Configuration

### Environment Variable

Set the `CORS_ORIGINS` environment variable with a comma-separated list of allowed origins:

```bash
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com,https://app.yourdomain.com
```

### Default Values

If `CORS_ORIGINS` is not set, the services default to:
```
http://localhost:3000,http://localhost:8000
```

This is suitable for local development.

### Docker Compose

The `docker-compose.yaml` file is configured to read `CORS_ORIGINS` from your `.env` file:

```yaml
environment:
  - CORS_ORIGINS=${CORS_ORIGINS:-http://localhost:3000,http://localhost:8000}
```

### .env File

Add the following to your `.env` file:

```bash
# Development (allows localhost)
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Production (specific domains only)
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

## Security Considerations

### ⚠️ Wildcard Warning

Using `*` as an origin is **NOT RECOMMENDED** for production:

```bash
# ❌ INSECURE - Do not use in production
CORS_ORIGINS=*
```

If you set `CORS_ORIGINS=*`, all services will log a warning:
```
⚠️  CORS configured with wildcard (*) - This should only be used in development!
```

### Best Practices

1. **Development**: Use specific localhost origins
   ```bash
   CORS_ORIGINS=http://localhost:3000,http://localhost:8000
   ```

2. **Staging**: Use staging domain
   ```bash
   CORS_ORIGINS=https://staging.yourdomain.com
   ```

3. **Production**: Use production domains only
   ```bash
   CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
   ```

4. **Multiple Environments**: Use different `.env` files for each environment

## Verification

When services start, they will log the configured CORS origins:

```
INFO: CORS allowed origins: ['https://yourdomain.com', 'https://www.yourdomain.com']
```

Check the logs to verify your configuration is correct.

## Troubleshooting

### CORS Errors in Browser

If you see CORS errors in the browser console:

1. Check that your frontend origin is in the `CORS_ORIGINS` list
2. Ensure there are no typos in the origin URLs
3. Verify the protocol (http vs https) matches
4. Check for trailing slashes (they matter!)

### Service Not Starting

If a service fails to start after CORS configuration:

1. Check the `.env` file syntax
2. Ensure no spaces around the `=` sign
3. Verify comma-separated format (no spaces after commas)
4. Check service logs for specific error messages

## Implementation Details

All three services use the same CORS configuration pattern:

```python
# Load from environment variable
cors_origins_env = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000")
cors_origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]

# Warn if wildcard is used
if "*" in cors_origins:
    log.warning("⚠️  CORS configured with wildcard (*) - This should only be used in development!")

# Apply to FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Related Files

- `.env.example` - Example environment configuration
- `docker-compose.yaml` - Docker service configuration
- `AFIRGEN FINAL/main backend/agentv5.py` - Main backend CORS config
- `AFIRGEN FINAL/gguf model server/llm_server.py` - Model server CORS config
- `AFIRGEN FINAL/asr ocr model server/asr_ocr.py` - ASR/OCR server CORS config
