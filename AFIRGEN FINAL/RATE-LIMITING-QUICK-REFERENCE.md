# Rate Limiting Quick Reference

## Configuration

```bash
# Environment Variables
RATE_LIMIT_REQUESTS=100    # Max requests per window
RATE_LIMIT_WINDOW=60       # Window size in seconds
```

## Default Limits

- **100 requests per minute** per IP address
- Sliding window algorithm
- Automatic cleanup of old requests

## Response Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Request processed |
| 429 | Too Many Requests | Wait and retry |

## Response Headers

### All Responses
```http
X-RateLimit-Limit: 100
X-RateLimit-Window: 60
```

### Rate Limited (429)
```http
Retry-After: 60
X-RateLimit-Limit: 100
X-RateLimit-Window: 60
```

## Error Response Format

```json
{
  "detail": "Rate limit exceeded. Maximum 100 requests per minute allowed. Please try again later.",
  "error": "too_many_requests"
}
```

## Exempt Endpoints

These endpoints are NOT rate limited:
- `/health`
- `/docs`
- `/redoc`
- `/openapi.json`

## Client IP Detection

Priority order:
1. `X-Forwarded-For` header (first IP)
2. `X-Real-IP` header
3. Direct connection IP

## Testing

```bash
# Run test suite
python test_rate_limiting.py

# With custom API key
python test_rate_limiting.py your-api-key
```

## Manual Testing

```bash
# Test rate limit
for i in {1..105}; do
  curl -H "X-API-Key: key" http://localhost:8000/health
done

# Check headers
curl -i -H "X-API-Key: key" http://localhost:8000/health | grep X-RateLimit

# Test with proxy header
curl -H "X-API-Key: key" \
     -H "X-Forwarded-For: 192.168.1.100" \
     http://localhost:8000/health
```

## Client Implementation

### Python Example

```python
import httpx
import asyncio

async def request_with_retry(url, headers):
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            await asyncio.sleep(retry_after)
            return await client.get(url, headers=headers)
        
        return response
```

### JavaScript Example

```javascript
async function requestWithRetry(url, headers) {
  const response = await fetch(url, { headers });
  
  if (response.status === 429) {
    const retryAfter = response.headers.get('Retry-After') || 60;
    await new Promise(resolve => setTimeout(resolve, retryAfter * 1000));
    return fetch(url, { headers });
  }
  
  return response;
}
```

## Troubleshooting

### Getting 429 Too Quickly

**Check**:
- Current rate limit: `echo $RATE_LIMIT_REQUESTS`
- Recent request count
- Multiple clients sharing same IP?

**Fix**:
- Increase `RATE_LIMIT_REQUESTS`
- Implement request batching
- Add caching on client side

### Rate Limiting Not Working

**Check**:
- Middleware is registered: Check `agentv5.py`
- Server logs for rate limit messages
- IP detection working correctly

**Fix**:
- Verify middleware order in FastAPI app
- Check proxy headers are set correctly
- Review logs for errors

### All Requests Same IP

**Check**:
- Behind reverse proxy?
- `X-Forwarded-For` header set?

**Fix**:
```nginx
# Nginx configuration
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Real-IP $remote_addr;
```

## Production Checklist

- [ ] Rate limits configured appropriately
- [ ] Proxy headers configured (if behind proxy)
- [ ] Monitoring for 429 responses
- [ ] Client retry logic implemented
- [ ] Rate limit headers documented for API users
- [ ] Consider Redis for distributed rate limiting

## Monitoring

### Key Metrics

- Rate limit hits per minute
- Top IPs hitting rate limits
- 429 response rate
- Average requests per IP

### Log Messages

```
WARNING - Rate limit exceeded for IP: 192.168.1.100 on path: /process
```

## Common Scenarios

### Development
```bash
RATE_LIMIT_REQUESTS=1000  # Generous for testing
```

### Production
```bash
RATE_LIMIT_REQUESTS=100   # Standard limit
```

### High Traffic
```bash
RATE_LIMIT_REQUESTS=500   # With Redis backend
```

## Security Notes

- Rate limiting is per-IP, not per-user
- Attackers can use multiple IPs to bypass
- Consider AWS WAF for additional protection
- Monitor for distributed attacks
- Implement global rate limits if needed

## Performance Impact

- **Memory**: ~100 bytes per tracked IP
- **CPU**: Minimal (O(n) cleanup per request)
- **Latency**: <1ms overhead per request

## Compliance

- ✅ OWASP API Security - API4:2019
- ✅ RFC 6585 - HTTP 429 Status Code
- ✅ Industry best practices

## Support

For issues or questions:
1. Check logs: `tail -f fir_pipeline.log`
2. Review test results: `python test_rate_limiting.py`
3. Verify configuration: `env | grep RATE_LIMIT`
