# AFIRGen AWS Security Groups - Least Privilege Implementation

## Overview

This document describes the implementation of AWS security groups following the principle of least privilege for the AFIRGen system. Each component has its own security group with minimal required permissions.

## Security Architecture

### Network Layers

```
Internet
    ↓
[ALB Security Group] - Port 443/80 from 0.0.0.0/0
    ↓
[Nginx Security Group] - Port 443/80 from ALB only
    ↓
[Main Backend SG] - Port 8000 from Nginx only
    ↓
├─→ [GGUF Model Server SG] - Port 8001 from Main Backend only
├─→ [ASR/OCR Server SG] - Port 8002 from Main Backend only
├─→ [RDS MySQL SG] - Port 3306 from Main Backend and Backup only
├─→ [EFS SG] - Port 2049 (NFS) from Main Backend only
└─→ [VPC Endpoints SG] - Port 443 from ECS services only

[Frontend SG] - Port 80 from Nginx only
[Backup SG] - Connects to RDS and S3 only
```

## Security Groups

### 1. Application Load Balancer (ALB) Security Group

**Purpose**: Accept HTTPS traffic from the internet and forward to Nginx

**Inbound Rules**:
- Port 443 (HTTPS) from 0.0.0.0/0 - Public internet access
- Port 80 (HTTP) from 0.0.0.0/0 - Redirect to HTTPS

**Outbound Rules**:
- Port 80 to Nginx Security Group - Forward HTTP traffic
- Port 443 to Nginx Security Group - Forward HTTPS traffic

**Justification**: ALB is the only public-facing component. All other services are internal.

### 2. Nginx Reverse Proxy Security Group

**Purpose**: TLS termination and routing to backend services

**Inbound Rules**:
- Port 80 from ALB Security Group only
- Port 443 from ALB Security Group only

**Outbound Rules**:
- Port 8000 to Main Backend Security Group - API requests
- Port 80 to Frontend Security Group - Static content

**Justification**: Nginx only accepts traffic from ALB and forwards to internal services.

### 3. Main Backend Security Group

**Purpose**: Core API and orchestration service

**Inbound Rules**:
- Port 8000 from Nginx Security Group only

**Outbound Rules**:
- Port 8001 to GGUF Model Server Security Group - LLM inference
- Port 8002 to ASR/OCR Server Security Group - Speech/OCR processing
- Port 3306 to RDS Security Group - Database queries
- Port 2049 to EFS Security Group - ChromaDB access
- Port 443 to 0.0.0.0/0 - AWS services (via VPC endpoints)

**Justification**: Main backend orchestrates all services and needs access to models, database, and storage.

### 4. GGUF Model Server Security Group

**Purpose**: LLM inference service

**Inbound Rules**:
- Port 8001 from Main Backend Security Group only

**Outbound Rules**:
- Port 443 to 0.0.0.0/0 - S3 model downloads (via VPC endpoint)

**Justification**: Model server only serves requests from main backend and downloads models from S3.

### 5. ASR/OCR Server Security Group

**Purpose**: Speech-to-text and OCR processing

**Inbound Rules**:
- Port 8002 from Main Backend Security Group only

**Outbound Rules**:
- Port 443 to 0.0.0.0/0 - S3 model downloads (via VPC endpoint)

**Justification**: ASR/OCR server only serves requests from main backend and downloads models from S3.

### 6. Frontend Security Group

**Purpose**: Static web content serving

**Inbound Rules**:
- Port 80 from Nginx Security Group only

**Outbound Rules**:
- None (static content only)

**Justification**: Frontend is static HTML/CSS/JS served by Nginx.

### 7. RDS MySQL Security Group

**Purpose**: Database service

**Inbound Rules**:
- Port 3306 from Main Backend Security Group - Application queries
- Port 3306 from Backup Security Group - Backup operations

**Outbound Rules**:
- None (database doesn't initiate connections)

**Justification**: Database only accepts connections from application and backup service.

### 8. EFS Security Group

**Purpose**: Shared file system for ChromaDB

**Inbound Rules**:
- Port 2049 (NFS) from Main Backend Security Group only

**Outbound Rules**:
- None (EFS doesn't initiate connections)

**Justification**: EFS only serves NFS requests from main backend for ChromaDB persistence.

### 9. Backup Service Security Group

**Purpose**: Automated database backups

**Inbound Rules**:
- None (backup service doesn't accept connections)

**Outbound Rules**:
- Port 3306 to RDS Security Group - Database backup
- Port 443 to 0.0.0.0/0 - S3 uploads and Secrets Manager (via VPC endpoints)

**Justification**: Backup service only connects to database and AWS services.

### 10. VPC Endpoints Security Group

**Purpose**: Private connectivity to AWS services (S3, Secrets Manager, CloudWatch)

**Inbound Rules**:
- Port 443 from Main Backend Security Group
- Port 443 from GGUF Model Server Security Group
- Port 443 from ASR/OCR Server Security Group
- Port 443 from Backup Security Group

**Outbound Rules**:
- None (VPC endpoints don't initiate connections)

**Justification**: VPC endpoints allow private access to AWS services without internet gateway.

## Least Privilege Principles Applied

### 1. No Direct Internet Access for Internal Services
- Only ALB has public IP addresses
- All ECS services run in private subnets
- Internet access via NAT Gateway (outbound only) or VPC endpoints

### 2. Service-to-Service Communication
- Each service can only communicate with services it directly needs
- No lateral movement between model servers
- Database only accessible from application and backup

### 3. Port Restrictions
- Only required ports are opened
- No wildcard port ranges (e.g., 0-65535)
- Specific protocols (TCP) instead of "all traffic"

### 4. Source/Destination Restrictions
- Rules reference security groups, not CIDR blocks (where possible)
- No 0.0.0.0/0 for internal services
- VPC endpoints used instead of internet gateway for AWS services

### 5. Egress Filtering
- Explicit egress rules (no default allow all)
- Services can only connect to required destinations
- Frontend has no egress (static content only)

## VPC Endpoints (PrivateLink)

To avoid NAT Gateway costs and improve security, use VPC endpoints for AWS services:

```hcl
# S3 Gateway Endpoint (no cost)
resource "aws_vpc_endpoint" "s3" {
  vpc_id       = aws_vpc.main.id
  service_name = "com.amazonaws.${var.aws_region}.s3"
  route_table_ids = concat(
    [aws_route_table.public.id],
    aws_route_table.private[*].id
  )
}

# Secrets Manager Interface Endpoint
resource "aws_vpc_endpoint" "secrets_manager" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.aws_region}.secretsmanager"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true
}

# CloudWatch Logs Interface Endpoint
resource "aws_vpc_endpoint" "logs" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.aws_region}.logs"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true
}

# ECR API Interface Endpoint (for pulling Docker images)
resource "aws_vpc_endpoint" "ecr_api" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.aws_region}.ecr.api"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true
}

# ECR DKR Interface Endpoint (for pulling Docker images)
resource "aws_vpc_endpoint" "ecr_dkr" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.aws_region}.ecr.dkr"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true
}
```

## Security Best Practices

### 1. Regular Security Audits
```bash
# List all security groups
aws ec2 describe-security-groups --region us-east-1

# Find security groups with 0.0.0.0/0 ingress
aws ec2 describe-security-groups \
  --filters "Name=ip-permission.cidr,Values=0.0.0.0/0" \
  --query 'SecurityGroups[*].[GroupId,GroupName]' \
  --output table
```

### 2. VPC Flow Logs
- Enable VPC Flow Logs for all traffic
- Monitor for unusual patterns
- Alert on rejected connections

### 3. AWS Config Rules
```hcl
# Ensure no security groups allow 0.0.0.0/0 on port 22 (SSH)
resource "aws_config_config_rule" "restricted_ssh" {
  name = "restricted-ssh"

  source {
    owner             = "AWS"
    source_identifier = "INCOMING_SSH_DISABLED"
  }

  depends_on = [aws_config_configuration_recorder.main]
}

# Ensure no security groups allow 0.0.0.0/0 on port 3389 (RDP)
resource "aws_config_config_rule" "restricted_rdp" {
  name = "restricted-rdp"

  source {
    owner             = "AWS"
    source_identifier = "RESTRICTED_INCOMING_TRAFFIC"
  }

  input_parameters = jsonencode({
    blockedPort1 = 3389
  })

  depends_on = [aws_config_configuration_recorder.main]
}
```

### 4. Security Group Naming Convention
- Format: `{project}-{component}-{environment}-sg`
- Example: `afirgen-main-backend-prod-sg`
- Use tags for additional metadata

### 5. Change Management
- All security group changes via Terraform (Infrastructure as Code)
- Require pull request reviews for changes
- Test in staging before production
- Document all rule changes

## Deployment

### Prerequisites
1. AWS CLI configured with appropriate credentials
2. Terraform >= 1.0 installed
3. VPC and subnets created

### Deploy Security Groups

```bash
# Initialize Terraform
cd terraform
terraform init

# Review planned changes
terraform plan

# Apply security groups
terraform apply

# Verify security groups
terraform output security_group_ids
```

### Validation

Run the validation script to ensure security groups follow least privilege:

```bash
python test_security_groups.py
```

## Monitoring and Alerts

### CloudWatch Alarms

```hcl
# Alert on high number of rejected connections
resource "aws_cloudwatch_metric_alarm" "rejected_connections" {
  alarm_name          = "${var.project_name}-rejected-connections"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "PacketsDroppedNoSecurityGroup"
  namespace           = "AWS/VPC"
  period              = "300"
  statistic           = "Sum"
  threshold           = "100"
  alarm_description   = "Alert when many connections are rejected by security groups"
  alarm_actions       = [aws_sns_topic.alerts.arn]
}
```

### Security Hub Integration

Enable AWS Security Hub to continuously monitor security group configurations:

```hcl
resource "aws_securityhub_account" "main" {}

resource "aws_securityhub_standards_subscription" "cis" {
  standards_arn = "arn:aws:securityhub:::ruleset/cis-aws-foundations-benchmark/v/1.2.0"
  depends_on    = [aws_securityhub_account.main]
}
```

## Troubleshooting

### Connection Timeouts

1. Check security group rules:
```bash
aws ec2 describe-security-groups --group-ids sg-xxxxx
```

2. Check VPC Flow Logs:
```bash
aws logs filter-log-events \
  --log-group-name /aws/vpc/afirgen-flow-logs \
  --filter-pattern "[version, account, eni, source, destination, srcport, destport, protocol, packets, bytes, windowstart, windowend, action=REJECT, flowlogstatus]"
```

3. Verify service is listening on expected port:
```bash
# From within ECS task
netstat -tlnp | grep 8000
```

### Security Group Limits

- Default limit: 2,500 security groups per region
- Default limit: 60 inbound rules per security group
- Default limit: 60 outbound rules per security group

Request limit increases via AWS Support if needed.

## Cost Optimization

### VPC Endpoints vs NAT Gateway

**NAT Gateway Costs** (per month):
- NAT Gateway: $32.40 (per AZ)
- Data processing: $0.045/GB
- Estimated: $100-200/month

**VPC Endpoints Costs** (per month):
- Interface endpoint: $7.20 (per AZ per endpoint)
- Data processing: $0.01/GB
- Estimated: $30-50/month

**Recommendation**: Use VPC endpoints for S3, Secrets Manager, and CloudWatch to save ~$100/month.

## Compliance

This security group configuration helps meet the following compliance requirements:

- **CIS AWS Foundations Benchmark**: Sections 4.1-4.5 (VPC security)
- **PCI DSS**: Requirement 1 (Network security controls)
- **HIPAA**: 164.312(e)(1) (Transmission security)
- **SOC 2**: CC6.6 (Logical access controls)

## References

- [AWS Security Groups Best Practices](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_SecurityGroups.html)
- [AWS VPC Endpoints](https://docs.aws.amazon.com/vpc/latest/privatelink/vpc-endpoints.html)
- [CIS AWS Foundations Benchmark](https://www.cisecurity.org/benchmark/amazon_web_services)
- [AWS Well-Architected Framework - Security Pillar](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html)

## Changelog

### 2024-02-12
- Initial implementation of least privilege security groups
- Added VPC endpoints for cost optimization
- Implemented VPC Flow Logs for monitoring
- Created validation scripts and documentation
