# CloudWatch Dashboards Deployment Checklist

## Pre-Deployment

- [ ] AWS account configured with appropriate credentials
- [ ] Terraform installed (version >= 1.0)
- [ ] AWS CLI installed and configured
- [ ] IAM permissions verified for CloudWatch and SNS
- [ ] Email address for alarm notifications ready

## Deployment Steps

### 1. Review Configuration

- [ ] Review `terraform/variables.tf` for default values
- [ ] Update `alarm_email` variable with your email address
- [ ] Verify `environment` and `aws_region` settings
- [ ] Review alarm thresholds in `cloudwatch_alarms.tf`

### 2. Initialize Terraform

```bash
cd terraform
terraform init
```

- [ ] Terraform initialization successful
- [ ] Provider plugins downloaded

### 3. Plan Deployment

```bash
terraform plan -var="alarm_email=ops@example.com"
```

- [ ] Review planned changes
- [ ] Verify 3 dashboards will be created
- [ ] Verify 10 alarms will be created
- [ ] Verify SNS topic and subscription will be created

### 4. Deploy Infrastructure

```bash
terraform apply -var="alarm_email=ops@example.com"
```

- [ ] Deployment successful
- [ ] No errors in output
- [ ] Resources created successfully

### 5. Verify Deployment

#### Check Dashboards
```bash
aws cloudwatch list-dashboards --region us-east-1
```

- [ ] `production-afirgen-main-dashboard` exists
- [ ] `production-afirgen-errors-dashboard` exists
- [ ] `production-afirgen-performance-dashboard` exists

#### Check Alarms
```bash
aws cloudwatch describe-alarms --alarm-name-prefix production-afirgen --region us-east-1
```

- [ ] 10 alarms created
- [ ] All alarms in OK state initially
- [ ] Alarm actions configured

#### Check SNS Topic
```bash
aws sns list-topics --region us-east-1 | grep afirgen
```

- [ ] SNS topic created
- [ ] Email subscription pending confirmation

### 6. Confirm SNS Subscription

- [ ] Check email inbox for AWS SNS subscription confirmation
- [ ] Click confirmation link in email
- [ ] Verify subscription status:
```bash
aws sns list-subscriptions-by-topic \
  --topic-arn arn:aws:sns:us-east-1:ACCOUNT_ID:production-afirgen-cloudwatch-alarms
```

### 7. Test Alarms (Optional)

```bash
# Trigger test alarm
aws cloudwatch set-alarm-state \
  --alarm-name production-afirgen-high-error-rate \
  --state-value ALARM \
  --state-reason "Testing alarm notification" \
  --region us-east-1
```

- [ ] Test alarm triggered
- [ ] Email notification received
- [ ] Reset alarm to OK state

### 8. Deploy Application

- [ ] Update application environment variables:
  - `AWS_REGION=us-east-1`
  - `ENVIRONMENT=production`
- [ ] Deploy application with CloudWatch metrics enabled
- [ ] Verify boto3 is installed in application container

### 9. Verify Metrics Publishing

Wait 5-10 minutes after application deployment, then:

```bash
# List metrics
aws cloudwatch list-metrics --namespace AFIRGen --region us-east-1
```

- [ ] Metrics appearing in CloudWatch
- [ ] At least 5-10 metric names visible
- [ ] Metrics have recent timestamps

### 10. View Dashboards

- [ ] Open AWS Console → CloudWatch → Dashboards
- [ ] Open main dashboard - verify widgets loading
- [ ] Open errors dashboard - verify error tracking
- [ ] Open performance dashboard - verify performance metrics

## Post-Deployment

### Monitoring Setup

- [ ] Add dashboard URLs to team documentation
- [ ] Configure additional SNS subscribers if needed
- [ ] Set up Slack/PagerDuty integration (optional)
- [ ] Document alarm response procedures

### Baseline Metrics

- [ ] Monitor dashboards for 24-48 hours
- [ ] Record baseline metrics:
  - Average API latency: _______
  - Average FIR generation time: _______
  - Error rate: _______
  - Cache hit rate: _______
- [ ] Adjust alarm thresholds based on baseline

### Cost Monitoring

- [ ] Enable AWS Cost Explorer
- [ ] Set up CloudWatch cost alerts
- [ ] Review CloudWatch costs after 1 week
- [ ] Verify costs are within budget ($34-49/month)

### Documentation

- [ ] Update team wiki with dashboard links
- [ ] Share quick reference guide with team
- [ ] Document alarm escalation procedures
- [ ] Schedule monthly dashboard review meetings

## Troubleshooting

### Metrics Not Appearing

If metrics don't appear after 10 minutes:

1. Check application logs:
```bash
docker logs afirgen-main-backend | grep -i cloudwatch
```

2. Verify IAM permissions:
```bash
aws iam get-role-policy --role-name afirgen-ecs-task-role --policy-name CloudWatchMetrics
```

3. Check environment variables:
```bash
docker exec afirgen-main-backend env | grep -E "AWS_REGION|ENVIRONMENT"
```

4. Test metrics manually:
```python
from cloudwatch_metrics import get_metrics
print(f"CloudWatch enabled: {get_metrics().enabled}")
get_metrics().record_count("TestMetric", 1)
get_metrics().flush()
```

### Alarms Not Triggering

If alarms don't trigger when expected:

1. Check alarm state:
```bash
aws cloudwatch describe-alarms --alarm-names production-afirgen-high-error-rate
```

2. Verify metric data exists:
```bash
aws cloudwatch get-metric-statistics \
  --namespace AFIRGen \
  --metric-name APIErrors \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

3. Check SNS subscription:
```bash
aws sns list-subscriptions | grep afirgen
```

### Dashboard Not Loading

If dashboard doesn't load:

1. Verify dashboard exists:
```bash
aws cloudwatch get-dashboard --dashboard-name production-afirgen-main-dashboard
```

2. Check for errors in dashboard JSON
3. Verify metrics exist in namespace
4. Try recreating dashboard:
```bash
terraform taint aws_cloudwatch_dashboard.afirgen_main
terraform apply
```

## Rollback Procedure

If deployment fails or causes issues:

```bash
cd terraform
terraform destroy -var="alarm_email=ops@example.com"
```

- [ ] Confirm destruction
- [ ] Verify all resources deleted
- [ ] Check for any orphaned resources

## Sign-Off

- [ ] Deployment completed successfully
- [ ] All verification steps passed
- [ ] Team notified of new dashboards
- [ ] Documentation updated

**Deployed By:** _________________  
**Date:** _________________  
**Environment:** _________________  
**Notes:** _________________

## Support

- **Implementation Guide:** `CLOUDWATCH-DASHBOARDS-IMPLEMENTATION.md`
- **Quick Reference:** `CLOUDWATCH-DASHBOARDS-QUICK-REFERENCE.md`
- **Summary:** `CLOUDWATCH-DASHBOARDS-SUMMARY.md`
- **AWS Support:** https://console.aws.amazon.com/support/
