# CloudWatch Dashboards & Metrics - README

## Overview

This directory contains the complete CloudWatch monitoring implementation for AFIRGen, including dashboards, alarms, metrics publishing, and comprehensive documentation.

## What's Included

### Core Components

1. **CloudWatch Metrics Module** (`main backend/cloudwatch_metrics.py`)
   - Python module for publishing custom metrics to AWS CloudWatch
   - Automatic buffering, batching, and error handling
   - 14+ metric types covering all aspects of the application

2. **Terraform Infrastructure** (`terraform/`)
   - `cloudwatch_dashboards.tf` - 3 comprehensive dashboards
   - `cloudwatch_alarms.tf` - 10 alarms with SNS notifications
   - `variables.tf` - Configuration variables

3. **Application Integration** (`main backend/agentv5.py`)
   - Automatic metric recording in middleware
   - Rate limiting, authentication, and health check tracking
   - Graceful shutdown with metric flushing

### Documentation

- **`CLOUDWATCH-DASHBOARDS-IMPLEMENTATION.md`** - Detailed implementation guide
- **`CLOUDWATCH-DASHBOARDS-QUICK-REFERENCE.md`** - Quick reference for common operations
- **`CLOUDWATCH-DASHBOARDS-SUMMARY.md`** - Implementation summary and status
- **`CLOUDWATCH-DEPLOYMENT-CHECKLIST.md`** - Step-by-step deployment checklist
- **`CLOUDWATCH-README.md`** - This file

### Testing

- **`test_cloudwatch_metrics.py`** - Comprehensive test suite (8 tests)
- **`validate_cloudwatch_terraform.py`** - Terraform validation (7 tests)

## Quick Start

### 1. Deploy Infrastructure

```bash
cd terraform
terraform init
terraform apply -var="alarm_email=ops@example.com"
```

### 2. Confirm SNS Subscription

Check your email and confirm the SNS subscription.

### 3. Deploy Application

Ensure environment variables are set:
```bash
export AWS_REGION=us-east-1
export ENVIRONMENT=production
```

### 4. View Dashboards

AWS Console → CloudWatch → Dashboards → Select dashboard

## Dashboards

### Main Dashboard
**Name:** `production-afirgen-main-dashboard`

Monitors:
- API requests, errors, and latency
- FIR generation success/failure and duration
- Model inference activity and duration
- Database operations and latency
- Cache performance
- Security events (rate limiting, authentication)
- Health check status

### Error Dashboard
**Name:** `production-afirgen-errors-dashboard`

Monitors:
- Real-time error rate
- Errors by status code
- Recent error logs

### Performance Dashboard
**Name:** `production-afirgen-performance-dashboard`

Monitors:
- API latency by endpoint
- FIR generation duration by step
- Model inference duration by type
- Cache hit rate
- Database latency by operation

## Alarms

| Alarm | Threshold | Severity |
|-------|-----------|----------|
| High Error Rate | >5% | High |
| High API Latency | P95 > 30s | Medium |
| FIR Generation Failures | >5 in 5min | High |
| Database Failures | >10 in 5min | Critical |
| High Rate Limiting | >100 in 5min | Medium |
| Authentication Failures | >50 in 5min | High |
| Service Unhealthy | >3 in 1min | Critical |
| Slow Model Inference | Avg > 10s | Medium |
| Low Cache Hit Rate | <50% | Low |
| Critical System Health | Composite | Critical |

## Metrics Published

| Metric | Description | Unit |
|--------|-------------|------|
| `APIRequests` | Total API requests | Count |
| `APILatency` | API response time | Milliseconds |
| `APIErrors` | API errors | Count |
| `FIRGenerations` | FIR generation attempts | Count |
| `FIRGenerationDuration` | FIR generation time | Milliseconds |
| `ModelInferences` | Model inference calls | Count |
| `ModelInferenceDuration` | Model inference time | Milliseconds |
| `TokensGenerated` | Tokens generated | Count |
| `DatabaseOperations` | Database operations | Count |
| `DatabaseLatency` | Database query time | Milliseconds |
| `CacheOperations` | Cache operations | Count |
| `RateLimitEvents` | Rate limiting events | Count |
| `AuthenticationEvents` | Auth attempts | Count |
| `HealthChecks` | Health check results | Count |

## Usage Examples

### Record Custom Metrics

```python
from cloudwatch_metrics import get_metrics

# Record count
get_metrics().record_count("CustomMetric", 1, {"Type": "Example"})

# Record duration
get_metrics().record_duration("OperationTime", 150.5)

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
    record_model_inference
)

# Record API request
record_api_request("/process", "POST", 200, 1500.0)

# Record FIR generation
record_fir_generation(success=True, duration_ms=25000.0)

# Record model inference
record_model_inference("llama", 5000.0, token_count=150)
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
enable_cloudwatch_dashboards = true
enable_cloudwatch_alarms = true
```

## Testing

### Run Metrics Tests

```bash
python test_cloudwatch_metrics.py
```

Expected output: 8/8 tests passing

### Run Terraform Validation

```bash
python validate_cloudwatch_terraform.py
```

Expected output: 7/7 tests passing

## Cost Estimate

| Component | Cost/Month |
|-----------|------------|
| Custom Metrics (~50-100 streams) | $15-30 |
| Dashboards (3) | $9 |
| Alarms (10) | Free |
| API Requests (~1M) | $10 |
| **Total** | **$34-49** |

## IAM Permissions

### Application Role

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["cloudwatch:PutMetricData"],
      "Resource": "*"
    }
  ]
}
```

### Terraform Deployment Role

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["cloudwatch:*", "sns:*"],
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

## Support

- **Implementation Guide:** `CLOUDWATCH-DASHBOARDS-IMPLEMENTATION.md`
- **Quick Reference:** `CLOUDWATCH-DASHBOARDS-QUICK-REFERENCE.md`
- **Deployment Checklist:** `CLOUDWATCH-DEPLOYMENT-CHECKLIST.md`
- **AWS CloudWatch Docs:** https://docs.aws.amazon.com/cloudwatch/
- **Boto3 CloudWatch:** https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudwatch.html

## Files

```
AFIRGEN FINAL/
├── main backend/
│   ├── cloudwatch_metrics.py          # Metrics module
│   └── agentv5.py                      # Application integration
├── terraform/
│   ├── cloudwatch_dashboards.tf       # Dashboard definitions
│   ├── cloudwatch_alarms.tf           # Alarm definitions
│   ├── variables.tf                   # Configuration variables
│   └── main.tf                        # Main Terraform config
├── test_cloudwatch_metrics.py         # Metrics test suite
├── validate_cloudwatch_terraform.py   # Terraform validation
├── CLOUDWATCH-DASHBOARDS-IMPLEMENTATION.md
├── CLOUDWATCH-DASHBOARDS-QUICK-REFERENCE.md
├── CLOUDWATCH-DASHBOARDS-SUMMARY.md
├── CLOUDWATCH-DEPLOYMENT-CHECKLIST.md
└── CLOUDWATCH-README.md               # This file
```

## Status

✅ **COMPLETE** - All components implemented, tested, and documented.

- ✅ CloudWatch metrics module
- ✅ 3 comprehensive dashboards
- ✅ 10 alarms with SNS notifications
- ✅ Application integration
- ✅ Terraform infrastructure
- ✅ Comprehensive testing (15/15 tests passing)
- ✅ Complete documentation

## Next Steps

1. Deploy infrastructure using Terraform
2. Confirm SNS email subscription
3. Deploy application with CloudWatch enabled
4. Monitor dashboards for baseline metrics
5. Adjust alarm thresholds based on usage

## License

Part of the AFIRGen project.
