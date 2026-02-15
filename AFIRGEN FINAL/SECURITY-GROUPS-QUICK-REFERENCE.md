# AFIRGen Security Groups - Quick Reference

## Security Group Summary

| Component | Inbound | Outbound | Purpose |
|-----------|---------|----------|---------|
| **ALB** | 443, 80 from Internet | 80, 443 to Nginx | Public entry point |
| **Nginx** | 80, 443 from ALB | 8000 to Backend, 80 to Frontend | Reverse proxy |
| **Main Backend** | 8000 from Nginx | 8001 to GGUF, 8002 to ASR/OCR, 3306 to RDS, 2049 to EFS, 443 to AWS | API orchestrator |
| **GGUF Server** | 8001 from Backend | 443 to S3 | LLM inference |
| **ASR/OCR Server** | 8002 from Backend | 443 to S3 | Speech/OCR |
| **Frontend** | 80 from Nginx | None | Static content |
| **RDS** | 3306 from Backend, Backup | None | Database |
| **EFS** | 2049 from Backend | None | ChromaDB storage |
| **Backup** | None | 3306 to RDS, 443 to S3 | Backups |
| **VPC Endpoints** | 443 from ECS services | None | AWS services |

## Quick Commands

### Deploy Security Groups
```bash
cd terraform
terraform init
terraform plan
terraform apply
```

### List Security Groups
```bash
aws ec2 describe-security-groups \
  --filters "Name=tag:Project,Values=afirgen" \
  --query 'SecurityGroups[*].[GroupId,GroupName,Description]' \
  --output table
```

### Check for Open Ports
```bash
# Find security groups with 0.0.0.0/0 access
aws ec2 describe-security-groups \
  --filters "Name=ip-permission.cidr,Values=0.0.0.0/0" \
  --query 'SecurityGroups[*].[GroupId,GroupName]' \
  --output table
```

### View VPC Flow Logs
```bash
aws logs tail /aws/vpc/afirgen-flow-logs --follow
```

### Test Connectivity
```bash
# From main backend to GGUF server
curl http://gguf-server:8001/health

# From main backend to RDS
mysql -h rds-endpoint -u user -p
```

## Security Rules Matrix

### Inbound Rules

| Source | Destination | Port | Protocol | Purpose |
|--------|-------------|------|----------|---------|
| Internet (0.0.0.0/0) | ALB | 443 | TCP | HTTPS access |
| Internet (0.0.0.0/0) | ALB | 80 | TCP | HTTP redirect |
| ALB SG | Nginx SG | 80, 443 | TCP | Proxy traffic |
| Nginx SG | Main Backend SG | 8000 | TCP | API requests |
| Nginx SG | Frontend SG | 80 | TCP | Static content |
| Main Backend SG | GGUF SG | 8001 | TCP | LLM inference |
| Main Backend SG | ASR/OCR SG | 8002 | TCP | Speech/OCR |
| Main Backend SG | RDS SG | 3306 | TCP | Database |
| Main Backend SG | EFS SG | 2049 | TCP | ChromaDB |
| Backup SG | RDS SG | 3306 | TCP | Backups |
| ECS Services | VPC Endpoints SG | 443 | TCP | AWS APIs |

### Outbound Rules

| Source | Destination | Port | Protocol | Purpose |
|--------|-------------|------|----------|---------|
| ALB SG | Nginx SG | 80, 443 | TCP | Forward traffic |
| Nginx SG | Main Backend SG | 8000 | TCP | API calls |
| Nginx SG | Frontend SG | 80 | TCP | Static files |
| Main Backend SG | GGUF SG | 8001 | TCP | Model calls |
| Main Backend SG | ASR/OCR SG | 8002 | TCP | Processing |
| Main Backend SG | RDS SG | 3306 | TCP | Queries |
| Main Backend SG | EFS SG | 2049 | TCP | File access |
| Main Backend SG | 0.0.0.0/0 | 443 | TCP | AWS services |
| GGUF SG | 0.0.0.0/0 | 443 | TCP | S3 models |
| ASR/OCR SG | 0.0.0.0/0 | 443 | TCP | S3 models |
| Backup SG | RDS SG | 3306 | TCP | Backup data |
| Backup SG | 0.0.0.0/0 | 443 | TCP | S3 upload |

## VPC Endpoints

### Gateway Endpoints (Free)
- **S3**: Model downloads, backups, logs

### Interface Endpoints ($7.20/month each per AZ)
- **Secrets Manager**: Credentials
- **CloudWatch Logs**: Application logs
- **ECR API**: Docker image metadata
- **ECR DKR**: Docker image layers

## Validation Checklist

- [ ] No security groups allow 0.0.0.0/0 except ALB
- [ ] All internal services in private subnets
- [ ] RDS not publicly accessible
- [ ] VPC Flow Logs enabled
- [ ] Security group rules use SG references (not CIDR)
- [ ] No unused security groups
- [ ] All egress rules are explicit (no 0.0.0.0/0 all ports)
- [ ] VPC endpoints configured for AWS services
- [ ] CloudWatch alarms for rejected connections
- [ ] Security Hub enabled

## Common Issues

### Connection Timeout
1. Check security group rules
2. Verify service is running
3. Check VPC Flow Logs for REJECT
4. Verify route tables

### Can't Access RDS
1. Ensure ECS task in same VPC
2. Check RDS security group allows ECS SG
3. Verify RDS endpoint is correct
4. Check network ACLs

### High NAT Gateway Costs
1. Implement VPC endpoints for S3, Secrets Manager
2. Use S3 gateway endpoint (free)
3. Monitor data transfer with CloudWatch

## Monitoring

### Key Metrics
- VPC Flow Logs: Rejected connections
- CloudWatch: Network bytes in/out
- Security Hub: Security group findings
- AWS Config: Compliance rules

### Alerts
```bash
# Create SNS topic for alerts
aws sns create-topic --name afirgen-security-alerts

# Subscribe email
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:ACCOUNT:afirgen-security-alerts \
  --protocol email \
  --notification-endpoint admin@example.com
```

## Cost Estimate

| Component | Monthly Cost |
|-----------|--------------|
| NAT Gateway (2 AZ) | $64.80 |
| NAT Data Transfer (100GB) | $4.50 |
| VPC Endpoints (4 × 2 AZ) | $57.60 |
| VPC Flow Logs (100GB) | $0.50 |
| **Total** | **~$127.40** |

**Optimization**: Use VPC endpoints instead of NAT Gateway to save ~$50/month.

## Emergency Procedures

### Lockdown All Access
```bash
# Remove all ingress rules from ALB
aws ec2 revoke-security-group-ingress \
  --group-id sg-alb-id \
  --ip-permissions '[{"IpProtocol": "-1", "IpRanges": [{"CidrIp": "0.0.0.0/0"}]}]'
```

### Allow Specific IP Only
```bash
# Add your IP to ALB
aws ec2 authorize-security-group-ingress \
  --group-id sg-alb-id \
  --protocol tcp \
  --port 443 \
  --cidr YOUR_IP/32
```

### Restore Default Rules
```bash
terraform apply -auto-approve
```

## Support

For issues or questions:
1. Check VPC Flow Logs
2. Review CloudWatch metrics
3. Run validation script: `python test_security_groups.py`
4. Contact AWS Support for limit increases
