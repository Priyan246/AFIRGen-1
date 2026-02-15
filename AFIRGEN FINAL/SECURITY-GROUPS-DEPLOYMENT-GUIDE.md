# AFIRGen Security Groups - Deployment Guide

## Overview

This guide walks you through deploying AWS security groups with least privilege configuration for the AFIRGen system.

## Prerequisites

### 1. AWS Account Setup

- AWS account with appropriate permissions
- AWS CLI installed and configured
- IAM user/role with the following permissions:
  - VPC management (ec2:CreateVpc, ec2:CreateSubnet, etc.)
  - Security group management (ec2:CreateSecurityGroup, etc.)
  - VPC endpoint management (ec2:CreateVpcEndpoint, etc.)
  - CloudWatch Logs management (logs:CreateLogGroup, etc.)
  - IAM role management (iam:CreateRole, iam:AttachRolePolicy)

### 2. Tools Installation

#### AWS CLI
```bash
# macOS
brew install awscli

# Windows
choco install awscli

# Linux
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

#### Terraform
```bash
# macOS
brew install terraform

# Windows
choco install terraform

# Linux
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/
```

#### Python Dependencies
```bash
pip install -r test_requirements.txt
```

### 3. AWS Configuration

```bash
# Configure AWS credentials
aws configure

# Verify configuration
aws sts get-caller-identity
```

## Deployment Steps

### Step 1: Review Configuration

1. Navigate to the terraform directory:
   ```bash
   cd "AFIRGEN FINAL/terraform"
   ```

2. Review `variables.tf` and customize if needed:
   ```hcl
   # Create terraform.tfvars
   cat > terraform.tfvars <<EOF
   project_name = "afirgen"
   environment  = "prod"
   aws_region   = "us-east-1"
   
   vpc_cidr             = "10.0.0.0/16"
   availability_zones   = ["us-east-1a", "us-east-1b"]
   public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24"]
   private_subnet_cidrs = ["10.0.10.0/24", "10.0.11.0/24"]
   
   enable_nat_gateway   = true
   enable_sts_endpoint  = false
   enable_xray_endpoint = false
   EOF
   ```

### Step 2: Initialize Terraform

```bash
# Initialize Terraform (downloads providers)
terraform init

# Expected output:
# Terraform has been successfully initialized!
```

### Step 3: Plan Deployment

```bash
# Generate execution plan
terraform plan -out=tfplan

# Review the plan carefully
# You should see:
# - 1 VPC
# - 4 subnets (2 public, 2 private)
# - 1 Internet Gateway
# - 2 NAT Gateways
# - 10 security groups
# - 8 VPC endpoints
# - VPC Flow Logs configuration
```

### Step 4: Deploy Infrastructure

```bash
# Apply the plan
terraform apply tfplan

# Or apply directly (will prompt for confirmation)
terraform apply

# Type 'yes' when prompted
```

**Deployment time**: Approximately 5-10 minutes

### Step 5: Verify Deployment

```bash
# View all outputs
terraform output

# Get security group IDs
terraform output security_group_ids

# Get VPC endpoint IDs
terraform output vpc_endpoint_ids

# Get VPC ID
terraform output vpc_id
```

### Step 6: Validate Security Groups

```bash
# Navigate back to main directory
cd ..

# Run validation script
python test_security_groups.py --region us-east-1 --project afirgen

# Expected output:
# ✓ All security group checks passed!
# ✓ Security groups follow least privilege principles
```

### Step 7: Enable Monitoring

```bash
# Verify VPC Flow Logs are enabled
aws ec2 describe-flow-logs \
  --filter "Name=resource-id,Values=$(terraform output -raw vpc_id)"

# Check CloudWatch Log Group
aws logs describe-log-groups \
  --log-group-name-prefix "/aws/vpc/afirgen"
```

## Post-Deployment Configuration

### 1. Update ECS Task Definitions

Update your ECS task definitions to use the new security groups:

```json
{
  "networkConfiguration": {
    "awsvpcConfiguration": {
      "subnets": ["subnet-xxxxx", "subnet-yyyyy"],
      "securityGroups": ["sg-main-backend-xxxxx"],
      "assignPublicIp": "DISABLED"
    }
  }
}
```

### 2. Update RDS Configuration

Update RDS instance to use the new security group:

```bash
aws rds modify-db-instance \
  --db-instance-identifier afirgen-db \
  --vpc-security-group-ids sg-rds-xxxxx
```

### 3. Update ALB Configuration

Update Application Load Balancer to use the new security group:

```bash
aws elbv2 set-security-groups \
  --load-balancer-arn arn:aws:elasticloadbalancing:... \
  --security-groups sg-alb-xxxxx
```

### 4. Configure CloudWatch Alarms

Create alarms for security monitoring:

```bash
# Create SNS topic for alerts
aws sns create-topic --name afirgen-security-alerts

# Subscribe to topic
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:ACCOUNT:afirgen-security-alerts \
  --protocol email \
  --notification-endpoint admin@example.com

# Create alarm for rejected connections
aws cloudwatch put-metric-alarm \
  --alarm-name afirgen-rejected-connections \
  --alarm-description "Alert on high number of rejected connections" \
  --metric-name PacketsDroppedNoSecurityGroup \
  --namespace AWS/VPC \
  --statistic Sum \
  --period 300 \
  --evaluation-periods 2 \
  --threshold 100 \
  --comparison-operator GreaterThanThreshold \
  --alarm-actions arn:aws:sns:us-east-1:ACCOUNT:afirgen-security-alerts
```

## Testing

### 1. Connectivity Testing

Test that services can communicate as expected:

```bash
# Test ALB to Nginx (should work)
curl -k https://your-alb-dns-name/health

# Test direct access to backend (should fail)
curl http://backend-private-ip:8000/health
# Expected: Connection timeout

# Test RDS from backend (should work)
# From within ECS task:
mysql -h rds-endpoint -u user -p

# Test RDS from internet (should fail)
mysql -h rds-endpoint -u user -p
# Expected: Connection timeout
```

### 2. Negative Testing

Verify that unauthorized access is blocked:

```bash
# Try to SSH to instances (should fail)
ssh ec2-user@instance-ip
# Expected: Connection timeout

# Try to access RDS directly (should fail)
mysql -h rds-endpoint -u user -p
# Expected: Connection timeout

# Try to access internal services (should fail)
curl http://gguf-server-ip:8001/health
# Expected: Connection timeout
```

### 3. VPC Endpoint Testing

Verify VPC endpoints are working:

```bash
# Test S3 access via VPC endpoint
# From within ECS task:
aws s3 ls s3://your-bucket/

# Test Secrets Manager access
aws secretsmanager get-secret-value --secret-id your-secret

# Check VPC endpoint DNS resolution
nslookup secretsmanager.us-east-1.amazonaws.com
# Should resolve to private IP (10.x.x.x)
```

## Monitoring

### 1. VPC Flow Logs

View VPC Flow Logs to monitor traffic:

```bash
# Tail flow logs
aws logs tail /aws/vpc/afirgen-flow-logs --follow

# Filter for rejected connections
aws logs filter-log-events \
  --log-group-name /aws/vpc/afirgen-flow-logs \
  --filter-pattern "[version, account, eni, source, destination, srcport, destport, protocol, packets, bytes, windowstart, windowend, action=REJECT, flowlogstatus]"
```

### 2. CloudWatch Metrics

Monitor key metrics:

```bash
# View network bytes in/out
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name NetworkIn \
  --dimensions Name=InstanceId,Value=i-xxxxx \
  --start-time 2024-02-12T00:00:00Z \
  --end-time 2024-02-12T23:59:59Z \
  --period 3600 \
  --statistics Average
```

### 3. Security Hub

Enable AWS Security Hub for continuous monitoring:

```bash
# Enable Security Hub
aws securityhub enable-security-hub

# Enable CIS benchmark
aws securityhub batch-enable-standards \
  --standards-subscription-requests StandardsArn=arn:aws:securityhub:::ruleset/cis-aws-foundations-benchmark/v/1.2.0

# Get findings
aws securityhub get-findings \
  --filters '{"ResourceType":[{"Value":"AwsEc2SecurityGroup","Comparison":"EQUALS"}]}'
```

## Troubleshooting

### Issue: Terraform apply fails with "VPC already exists"

**Solution**: Import existing VPC or use different project name

```bash
# Import existing VPC
terraform import aws_vpc.main vpc-xxxxx

# Or change project name in terraform.tfvars
project_name = "afirgen-new"
```

### Issue: Connection timeouts after deployment

**Solution**: Check security group rules and VPC Flow Logs

```bash
# Check security group rules
aws ec2 describe-security-groups --group-ids sg-xxxxx

# Check VPC Flow Logs for rejected connections
aws logs filter-log-events \
  --log-group-name /aws/vpc/afirgen-flow-logs \
  --filter-pattern "REJECT"

# Verify service is running
aws ecs describe-tasks --cluster afirgen --tasks task-id
```

### Issue: VPC endpoints not working

**Solution**: Verify private DNS is enabled and security group allows traffic

```bash
# Check VPC endpoint configuration
aws ec2 describe-vpc-endpoints --vpc-endpoint-ids vpce-xxxxx

# Verify private DNS is enabled
# Should show "PrivateDnsEnabled": true

# Check security group allows port 443
aws ec2 describe-security-groups --group-ids sg-vpc-endpoints-xxxxx
```

### Issue: High costs

**Solution**: Optimize VPC endpoints and NAT Gateway usage

```bash
# Check NAT Gateway data transfer
aws cloudwatch get-metric-statistics \
  --namespace AWS/NATGateway \
  --metric-name BytesOutToDestination \
  --dimensions Name=NatGatewayId,Value=nat-xxxxx \
  --start-time 2024-02-01T00:00:00Z \
  --end-time 2024-02-12T23:59:59Z \
  --period 86400 \
  --statistics Sum

# Consider disabling NAT Gateway if using VPC endpoints
# Edit terraform.tfvars:
enable_nat_gateway = false
```

## Rollback

If you need to rollback the deployment:

```bash
# Destroy all resources
cd terraform
terraform destroy

# Type 'yes' when prompted

# Or destroy specific resources
terraform destroy -target=aws_security_group.main_backend
```

## Maintenance

### Regular Tasks

1. **Weekly**: Run validation script
   ```bash
   python test_security_groups.py
   ```

2. **Weekly**: Review VPC Flow Logs for anomalies
   ```bash
   aws logs tail /aws/vpc/afirgen-flow-logs --follow
   ```

3. **Monthly**: Review security group rules
   ```bash
   aws ec2 describe-security-groups \
     --filters "Name=tag:Project,Values=afirgen"
   ```

4. **Quarterly**: Full security audit
   ```bash
   # Run Security Hub assessment
   aws securityhub get-findings
   ```

### Updating Security Groups

To update security group rules:

1. Edit `terraform/security_groups.tf`
2. Run `terraform plan` to preview changes
3. Run `terraform apply` to apply changes
4. Run validation script to verify

## Cost Breakdown

| Component | Monthly Cost | Notes |
|-----------|--------------|-------|
| NAT Gateway (2 AZ) | $64.80 | $0.045/hour per AZ |
| NAT Data Transfer (100GB) | $4.50 | $0.045/GB |
| VPC Endpoints (7 × 2 AZ) | $100.80 | $7.20/month per endpoint per AZ |
| VPC Flow Logs (100GB) | $0.50 | $0.50/GB ingested |
| **Total** | **~$170.60** | |

**Cost Optimization Tips**:
- Use VPC endpoints instead of NAT Gateway for AWS services (saves data transfer costs)
- Disable optional endpoints (STS, X-Ray) if not needed
- Use single AZ for dev/staging (not recommended for production)

## Support

For issues or questions:

1. Check [SECURITY-GROUPS-IMPLEMENTATION.md](SECURITY-GROUPS-IMPLEMENTATION.md) for detailed documentation
2. Check [SECURITY-GROUPS-QUICK-REFERENCE.md](SECURITY-GROUPS-QUICK-REFERENCE.md) for quick commands
3. Run validation script: `python test_security_groups.py`
4. Review VPC Flow Logs for connection issues
5. Contact AWS Support for limit increases or technical issues

## Next Steps

After successful deployment:

1. ✅ Deploy ECS services with new security groups
2. ✅ Update RDS and ALB configurations
3. ✅ Configure CloudWatch alarms
4. ✅ Enable AWS Security Hub
5. ✅ Set up regular monitoring and audits
6. ✅ Document any custom configurations
7. ✅ Train team on security group management

## References

- [AWS VPC Documentation](https://docs.aws.amazon.com/vpc/)
- [AWS Security Groups](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_SecurityGroups.html)
- [AWS VPC Endpoints](https://docs.aws.amazon.com/vpc/latest/privatelink/vpc-endpoints.html)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [CIS AWS Foundations Benchmark](https://www.cisecurity.org/benchmark/amazon_web_services)

---

**Deployment Status**: Ready for production
**Last Updated**: 2024-02-12
**Maintained By**: AFIRGen DevOps Team
