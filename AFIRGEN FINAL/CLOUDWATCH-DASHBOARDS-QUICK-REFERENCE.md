# CloudWatch Dashboards Quick Reference

## Quick Start

### Deploy Dashboards
```bash
cd terraform
terraform apply -var="alarm_email=ops@example.com"
```

### View Dashboards
AWS Console → CloudWatch → Dashboards → Select dashboard

### Check Metrics
```bash
aws cloudwatch list-metrics --namespace AFIRGen --region us-east-1
```

## Key Metrics

| Metric | Description | Unit | Dimensions |
|--------|-------------|------|------------|
| `APIRequests` | Total API requests | Count | Endpoint, Method, StatusCode |
| `APILatency` | API response time | Milliseconds | Endpoint, Method, StatusCode |
| `APIErrors` | API errors | Count | Endpoint, StatusCode |
| `FIRGenerations` | FIR generation attempts | Count | Status (Success/Failure) |
| `FIRGenerationDuration` | FIR generation time | Milliseconds | Status, Step |
| `ModelInferences` | Model inference calls | Count | Model |
| `ModelInferenceDuration` | Model inference time | Milliseconds | Model |
| `TokensGenerated` | Tokens generated | Count | Model |
| `DatabaseOperations` | Database operations | Count | Operation, Status |
| `DatabaseLatency` | Database query time | Milliseconds | Operation |
| `CacheOperations` | Cache operations | Count | Cache, Result (Hit/Miss) |
| `RateLimitEvents` | Rate limiting events | Count | Result (Blocked/Allowed) |
| `AuthenticationEvents` | Auth attempts | Count | Status, Reason |
| `HealthChecks` | Health check results | Count | Service, Status |

## Dashboards

### Main Dashboard
**Name:** `{environment}-afirgen-main-dashboard`

**Widgets:**
- API Requests & Errors
- API Latency (Avg, P95, P99)
- FIR Generations (Success/Failure)
- FIR Generation Duration
- Model Inference Activity
- Model Inference Duration
- Database Operations
- Database Latency
- Cache Performance
- Rate Limiting Events
- Authentication Events
- Health Check Status

### Error Dashboard
**Name:** `{environment}-afirgen-errors-dashboard`

**Widgets:**
- API Error Rate (1 min)
- Errors by Status Code
- Recent Error Logs

### Performance Dashboard
**Name:** `{environment}-afirgen-performance-dashboard`

**Widgets:**
- API Latency by Endpoint
- FIR Generation Duration by Step
- Model Inference Duration by Type
- Cache Hit Rate
- Database Latency by Operation

## Alarms

| Alarm | Threshold | Severity | Description |
|-------|-----------|----------|-------------|
| `high-error-rate` | >5% | High | API error rate exceeds 5% |
| `high-api-latency` | P95 > 30s | Medium | API latency exceeds 30 seconds |
| `fir-generation-failures` | >5 in 5min | High | FIR generation failures |
| `database-failures` | >10 in 5min | Critical | Database operation failures |
| `high-rate-limiting` | >100 in 5min | Medium | High rate limiting activity |
| `auth-failures` | >50 in 5min | High | Authentication failures |
| `service-unhealthy` | >3 in 1min | Critical | Service health check failures |
| `slow-model-inference` | Avg > 10s | Medium | Slow model inference |
| `low-cache-hit-rate` | <50% | Low | Low cache hit rate |
| `critical-system-health` | Composite | Critical | Multiple critical issues |

## Common Commands

### View Metrics
```bash
# List all metrics
aws cloudwatch list-metrics --namespace AFIRGen

# Get metric statistics
aws cloudwatch get-metric-statistics \
  --namespace AFIRGen \
  --metric-name APIRequests \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-01T23:59:59Z \
  --period 300 \
  --statistics Sum
```

### View Alarms
```bash
# List alarms
aws cloudwatch describe-alarms --alarm-name-prefix production-afirgen

# Get alarm history
aws cloudwatch describe-alarm-history \
  --alarm-name production-afirgen-high-error-rate
```

### Test Alarms
```bash
# Trigger alarm manually
aws cloudwatch set-alarm-state \
  --alarm-name production-afirgen-high-error-rate \
  --state-value ALARM \
  --state-reason "Testing"
```

### View Dashboards
```bash
# List dashboards
aws cloudwatch list-dashboards

# Get dashboard
aws cloudwatch get-dashboard \
  --dashboard-name production-afirgen-main-dashboard
```

## Python Usage

### Record Custom Metrics
```python
from cloudwatch_metrics import get_metrics

# Record count
get_metrics().record_count("CustomMetric", 1, {"Type": "Example"})

# Record duration
get_metrics().record_duration("OperationTime", 150.5, {"Operation": "Process"})

# Record percentage
get_metrics().record_percentage("SuccessRate", 95.5)

# Flush metrics
get_metrics().flush()
```

### Use Decorator
```python
from cloudwatch_metrics import track_duration

@track_duration("MyFunction", {"Service": "Backend"})
async def my_function():
    # Function code
    pass
```

### Convenience Functions
```python
from cloudwatch_metrics import (
    record_api_request,
    record_fir_generation,
    record_model_inference,
    record_database_operation,
    record_cache_operation,
    record_rate_limit_event,
    record_auth_event,
    record_health_check
)

# Record API request
record_api_request("/process", "POST", 200, 1500.0)

# Record FIR generation
record_fir_generation(success=True, duration_ms=25000.0, step="summary")

# Record model inference
record_model_inference("llama", 5000.0, token_count=150)

# Record database operation
record_database_operation("save", 50.0, success=True)

# Record cache operation
record_cache_operation("session_cache", hit=True)

# Record rate limit event
record_rate_limit_event("192.168.1.1", blocked=False)

# Record auth event
record_auth_event(success=True)

# Record health check
record_health_check("model_server", healthy=True, response_time_ms=100.0)
```

## Configuration

### Environment Variables
```bash
AWS_REGION=us-east-1
ENVIRONMENT=production  # Enables CloudWatch in production
```

### Terraform Variables
```hcl
environment = "production"
aws_region  = "us-east-1"
alarm_email = "ops@example.com"
```

## IAM Permissions

### Application Role
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:PutMetricData"
      ],
      "Resource": "*"
    }
  ]
}
```

### Admin Role (for Terraform)
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:*",
        "sns:*"
      ],
      "Resource": "*"
    }
  ]
}
```

## Troubleshooting

### Metrics Not Appearing
1. Check IAM permissions
2. Verify `ENVIRONMENT=production`
3. Check application logs for CloudWatch errors
4. Verify boto3 is installed

### Dashboard Not Loading
1. Verify dashboard exists: `aws cloudwatch list-dashboards`
2. Check metric data: `aws cloudwatch list-metrics --namespace AFIRGen`
3. Verify AWS region matches

### Alarms Not Triggering
1. Check alarm state: `aws cloudwatch describe-alarms`
2. Verify SNS subscription is confirmed
3. Test alarm manually: `aws cloudwatch set-alarm-state`

## Cost Estimates

| Component | Quantity | Cost/Month |
|-----------|----------|------------|
| Custom Metrics | ~50-100 streams | $15-30 |
| Dashboards | 3 dashboards | $9 |
| Alarms | 10 alarms | Free (first 10) |
| API Requests | ~1M/month | $10 |
| **Total** | | **$34-49** |

## Support

- **Documentation:** See `CLOUDWATCH-DASHBOARDS-IMPLEMENTATION.md`
- **AWS Docs:** https://docs.aws.amazon.com/cloudwatch/
- **Boto3 Docs:** https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudwatch.html
