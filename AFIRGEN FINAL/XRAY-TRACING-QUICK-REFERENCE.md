# AWS X-Ray Distributed Tracing - Quick Reference

## Configuration

### Environment Variables
```bash
XRAY_ENABLED=true                    # Enable/disable tracing
XRAY_SAMPLING_RATE=0.1              # 10% sampling (cost optimization)
XRAY_DAEMON_ADDRESS=127.0.0.1:2000  # X-Ray daemon address
XRAY_CONTEXT_MISSING=LOG_ERROR      # Error handling mode
```

## Common Operations

### Add Annotations (Searchable)
```python
from xray_tracing import add_trace_annotation

add_trace_annotation("session_id", session_id)
add_trace_annotation("model_name", "summariser")
add_trace_annotation("error", False)
```

### Add Metadata (Detailed Info)
```python
from xray_tracing import add_trace_metadata

add_trace_metadata("prompt_length", 1500)
add_trace_metadata("error_details", {"type": "timeout"})
```

### Trace Custom Operations
```python
from xray_tracing import AsyncXRaySubsegment

async with AsyncXRaySubsegment("custom_operation") as subsegment:
    subsegment.put_annotation("operation_type", "processing")
    # Your code here
```

## ECS Configuration

### X-Ray Daemon Sidecar
```json
{
  "name": "xray-daemon",
  "image": "public.ecr.aws/xray/aws-xray-daemon:latest",
  "cpu": 32,
  "memoryReservation": 256,
  "portMappings": [{"containerPort": 2000, "protocol": "udp"}]
}
```

### IAM Permissions
```json
{
  "Effect": "Allow",
  "Action": [
    "xray:PutTraceSegments",
    "xray:PutTelemetryRecords"
  ],
  "Resource": "*"
}
```

## X-Ray Console Queries

### Find Slow Requests
```
service("afirgen-main-backend") AND responsetime > 5
```

### Find Errors
```
service("afirgen-main-backend") AND error = true
```

### Find Specific Operations
```
annotation.model_name = "summariser"
annotation.endpoint = "/process"
```

## Troubleshooting

### No Traces Appearing
1. Check X-Ray daemon is running
2. Verify IAM permissions
3. Check `XRAY_DAEMON_ADDRESS` is correct
4. Review application logs for X-Ray errors

### High Costs
1. Reduce `XRAY_SAMPLING_RATE` to 0.05 (5%)
2. Implement custom sampling rules
3. Reduce trace retention to 7 days

## Local Testing

### Without X-Ray Daemon
```bash
export XRAY_ENABLED=true
export XRAY_CONTEXT_MISSING=LOG_ERROR
python agentv5.py
```

### With X-Ray Daemon
```bash
# Start daemon
docker run --rm -p 2000:2000/udp \
  public.ecr.aws/xray/aws-xray-daemon:latest

# Run application
export XRAY_ENABLED=true
export XRAY_DAEMON_ADDRESS=127.0.0.1:2000
python agentv5.py
```

## Cost Estimates

- **10% sampling**: ~$5-10/month (moderate traffic)
- **100% sampling**: ~$50-100/month (moderate traffic)
- **Per trace**: $0.000005 (first 100K traces/month free)

## Service Names

- Main Backend: `afirgen-main-backend`
- GGUF Server: `afirgen-gguf-server`
- ASR/OCR Server: `afirgen-asr-ocr-server`

## Key Features

✅ Automatic HTTP client tracing (httpx, requests)
✅ Automatic AWS SDK tracing (boto3)
✅ Automatic database tracing (MySQL)
✅ Custom annotations and metadata
✅ Service map visualization
✅ Performance analytics
✅ Error tracking
