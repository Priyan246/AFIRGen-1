# Rate Limiting Implementation Guide

## Overview

This document describes the implementation of rate limiting for the AFIRGen API to prevent abuse and ensure fair resource allocation. The system enforces a limit of **100 requests per minute per IP address**.

## Implementation Details

### 1. Rate Limiter Class

**Location**: `main backend/agentv5.py` (lines ~1131-1150)

```python
class RateLimiter:
    """Simple in-memory rate limiter using sliding window algorithm"""
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
    
    def is_allowed(self, client_id: str) -> bool:
        now = time()
        # Clean old requests outside the window
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if now - req_time < self.window_seconds
        ]
        
        # Check if limit exceeded
        if len(self.requests[client_id]) >= self.max_requests:
            return False
        
        # Record this request
        self.requests[client_id].append(now)
        return True
```

**Algorithm**: Sliding window
- Tracks timestamps of all requests per client
- Automatically removes requests older than the time window
- Allows exactly `max_requests` within any `window_seconds` period

### 2. Rate Limit Middleware

**Location**: `main backend/agentv5.py` (lines ~1411-1450)

```python
class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Get client IP (supports proxied requests)
        client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        if not client_ip:
            client_ip = request.headers.get("X-Real-IP", "")
        if not client_ip:
            client_ip = request.client.host if request.client else "unknown"
        
        # Skip rate limiting for public endpoints
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Check rate limit
        if not rate_limiter.is_allowed(client_ip):
            log.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Maximum 100 requests per minute allowed.",
                    "error": "too_many_requests"
                },
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(rate_limiter.max_requests),
                    "X-RateLimit-Window": str(rate_limiter.window_seconds)
                }
            )
        
        response = await call_next(request)
        
        # Add rate limit headers to all responses
        response.headers["X-RateLimit-Limit"] = str(rate_limiter.max_requests)
        response.headers["X-RateLimit-Window"] = str(rate_limiter.window_seconds)
        
        return response
```

### 3. Configuration

Rate limiting is configured via environment variables:

```bash
# .env file
RATE_LIMIT_REQUESTS=100    # Maximum requests per window
RATE_LIMIT_WINDOW=60       # Window size in seconds
```

**Default values**: 100 requests per 60 seconds (1 minute)

### 4. Client IP Detection

The middleware supports multiple methods for identifying client IP:

1. **X-Forwarded-For header** (for proxied requests, e.g., behind Nginx/ALB)
   - Takes the first IP in the comma-separated list
   - Most common in production deployments

2. **X-Real-IP header** (alternative proxy header)
   - Used by some reverse proxies

3. **Direct connection IP** (fallback)
   - Uses `request.client.host` for direct connections

This ensures rate limiting works correctly whether the API is:
- Accessed directly
- Behind a reverse proxy (Nginx)
- Behind a load balancer (AWS ALB/ELB)

### 5. Response Headers

All API responses include rate limit information:

```http
X-RateLimit-Limit: 100
X-RateLimit-Window: 60
```

When rate limited (429 response):

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 60
X-RateLimit-Limit: 100
X-RateLimit-Window: 60
Content-Type: application/json

{
  "detail": "Rate limit exceeded. Maximum 100 requests per minute allowed. Please try again later.",
  "error": "too_many_requests"
}
```

### 6. Exempt Endpoints

The following endpoints are exempt from rate limiting:
- `/health` - Health check endpoint
- `/docs` - API documentation
- `/redoc` - Alternative API documentation
- `/openapi.json` - OpenAPI schema

## Testing

### Running Tests

```bash
# Make sure server is running
cd "AFIRGEN FINAL"
python test_rate_limiting.py

# With custom API key
python test_rate_limiting.py your-api-key-here
```

### Test Coverage

The test suite (`test_rate_limiting.py`) validates:

1. **Rate limit enforcement** - Requests are blocked after exceeding limit
2. **Per-IP tracking** - Each IP has independent rate limit
3. **Window reset** - Rate limit resets after time window
4. **Response headers** - Proper headers included in responses
5. **Exempt endpoints** - Health check and docs are accessible
6. **Concurrent requests** - Rate limiting works with concurrent traffic
7. **Proxy support** - X-Forwarded-For header is respected
8. **Error format** - 429 responses have correct structure

### Manual Testing

```bash
# Test basic rate limiting
for i in {1..105}; do
  curl -H "X-API-Key: your-key" http://localhost:8000/health
  echo "Request $i"
done

# Test with X-Forwarded-For
curl -H "X-API-Key: your-key" \
     -H "X-Forwarded-For: 192.168.1.100" \
     http://localhost:8000/health

# Check rate limit headers
curl -i -H "X-API-Key: your-key" http://localhost:8000/health | grep X-RateLimit
```

## Production Considerations

### 1. Distributed Rate Limiting

**Current limitation**: In-memory rate limiter doesn't work across multiple instances.

**Solution for production**:
- Use Redis for distributed rate limiting
- Implement with `redis-py` or `aioredis`
- Share rate limit state across all API instances

Example Redis-based implementation:

```python
import redis
from datetime import timedelta

class RedisRateLimiter:
    def __init__(self, redis_client, max_requests=100, window_seconds=60):
        self.redis = redis_client
        self.max_requests = max_requests
        self.window_seconds = window_seconds
    
    def is_allowed(self, client_id: str) -> bool:
        key = f"rate_limit:{client_id}"
        pipe = self.redis.pipeline()
        now = time()
        
        # Remove old entries
        pipe.zremrangebyscore(key, 0, now - self.window_seconds)
        # Count current requests
        pipe.zcard(key)
        # Add current request
        pipe.zadd(key, {str(now): now})
        # Set expiry
        pipe.expire(key, self.window_seconds)
        
        results = pipe.execute()
        request_count = results[1]
        
        return request_count < self.max_requests
```

### 2. Rate Limit Tiers

Consider implementing different rate limits for different user types:

```python
RATE_LIMITS = {
    "free": {"requests": 100, "window": 60},
    "premium": {"requests": 1000, "window": 60},
    "enterprise": {"requests": 10000, "window": 60}
}
```

### 3. Monitoring

Add metrics for rate limiting:

```python
# Track rate limit hits
rate_limit_hits = Counter('rate_limit_hits_total', 'Total rate limit hits', ['ip'])

# Track requests per IP
requests_per_ip = Histogram('requests_per_ip', 'Requests per IP distribution')
```

### 4. Logging

Current implementation logs rate limit violations:

```python
log.warning(f"Rate limit exceeded for IP: {client_ip} on path: {request.url.path}")
```

Consider adding:
- User agent logging
- Request path patterns
- Time-based analysis

### 5. DDoS Protection

Rate limiting alone is not sufficient for DDoS protection. Consider:

- **AWS WAF** - Web Application Firewall with rate-based rules
- **CloudFlare** - DDoS protection and rate limiting at edge
- **Fail2ban** - Automatic IP blocking for repeated violations
- **Connection limits** - Limit concurrent connections per IP

### 6. Graceful Degradation

When under heavy load:

```python
# Reduce rate limits dynamically
if system_load > 0.8:
    rate_limiter.max_requests = 50  # Reduce to 50 req/min
```

## Configuration Examples

### Development

```bash
# .env
RATE_LIMIT_REQUESTS=1000   # Generous limit for testing
RATE_LIMIT_WINDOW=60
```

### Production

```bash
# .env
RATE_LIMIT_REQUESTS=100    # Strict limit
RATE_LIMIT_WINDOW=60
```

### High-Traffic Production

```bash
# .env
RATE_LIMIT_REQUESTS=500    # Higher limit with Redis backend
RATE_LIMIT_WINDOW=60
```

## Troubleshooting

### Issue: Rate limit hit too quickly

**Symptoms**: Legitimate users getting 429 errors

**Solutions**:
1. Increase `RATE_LIMIT_REQUESTS`
2. Implement user authentication with per-user limits
3. Add rate limit exemptions for trusted IPs

### Issue: Rate limiting not working behind proxy

**Symptoms**: All requests appear to come from same IP

**Solutions**:
1. Ensure proxy sets `X-Forwarded-For` header
2. Configure Nginx:
   ```nginx
   proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
   proxy_set_header X-Real-IP $remote_addr;
   ```
3. Verify middleware reads correct header

### Issue: Memory usage growing

**Symptoms**: Rate limiter consuming too much memory

**Solutions**:
1. Implement periodic cleanup of old entries
2. Set maximum number of tracked IPs
3. Switch to Redis-based rate limiting

```python
# Add cleanup to RateLimiter
def cleanup_old_clients(self):
    """Remove clients with no recent requests"""
    now = time()
    to_remove = [
        client_id for client_id, requests in self.requests.items()
        if not requests or (now - max(requests)) > self.window_seconds * 2
    ]
    for client_id in to_remove:
        del self.requests[client_id]
```

## Security Considerations

### 1. IP Spoofing

**Risk**: Attackers may spoof `X-Forwarded-For` header

**Mitigation**:
- Only trust `X-Forwarded-For` from known proxies
- Validate proxy IP before using forwarded headers
- Use `X-Real-IP` from trusted reverse proxy

### 2. Distributed Attacks

**Risk**: Attacker uses multiple IPs to bypass rate limiting

**Mitigation**:
- Implement global rate limits (total requests across all IPs)
- Use AWS WAF rate-based rules
- Monitor for suspicious patterns

### 3. Resource Exhaustion

**Risk**: Rate limiter itself consumes too many resources

**Mitigation**:
- Limit number of tracked IPs (LRU cache)
- Use efficient data structures (sorted sets in Redis)
- Implement cleanup of stale entries

## API Client Guidelines

### Handling Rate Limits

Clients should:

1. **Check rate limit headers** in responses
2. **Implement exponential backoff** when rate limited
3. **Respect Retry-After header**

Example client code:

```python
import httpx
import asyncio

async def make_request_with_retry(url, headers, max_retries=3):
    for attempt in range(max_retries):
        response = await client.get(url, headers=headers)
        
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            print(f"Rate limited, waiting {retry_after}s...")
            await asyncio.sleep(retry_after)
            continue
        
        return response
    
    raise Exception("Max retries exceeded")
```

### Best Practices

1. **Batch requests** when possible
2. **Cache responses** to reduce API calls
3. **Implement client-side rate limiting** to stay under limits
4. **Monitor rate limit headers** to adjust request rate

## Compliance

### OWASP API Security

Rate limiting addresses:
- **API4:2019 - Lack of Resources & Rate Limiting**
- **API10:2019 - Insufficient Logging & Monitoring**

### Industry Standards

- **IETF RFC 6585** - HTTP Status Code 429 (Too Many Requests)
- **IETF Draft** - RateLimit Header Fields for HTTP

## Future Enhancements

1. **Redis integration** for distributed rate limiting
2. **Per-user rate limits** based on authentication
3. **Dynamic rate limits** based on system load
4. **Rate limit analytics** dashboard
5. **Whitelist/blacklist** IP management
6. **Geographic rate limits** (different limits per region)
7. **Endpoint-specific limits** (stricter for expensive operations)

## References

- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [RFC 6585 - HTTP Status Code 429](https://tools.ietf.org/html/rfc6585)
- [Rate Limiting Strategies](https://cloud.google.com/architecture/rate-limiting-strategies-techniques)
