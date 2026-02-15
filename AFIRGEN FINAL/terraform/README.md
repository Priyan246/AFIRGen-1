# AFIRGen AWS Infrastructure - Terraform Configuration

This directory contains Terraform configurations for deploying AFIRGen infrastructure to AWS with security groups following the principle of least privilege.

## Files

- `main.tf` - Main Terraform configuration and provider setup
- `variables.tf` - Input variables for customization
- `vpc.tf` - VPC, subnets, route tables, and NAT gateways
- `security_groups.tf` - Security group definitions for all components
- `vpc_endpoints.tf` - VPC endpoints for private AWS service access
- `README.md` - This file

## Prerequisites

1. **AWS CLI** configured with appropriate credentials:
   ```bash
   aws configure
   ```

2. **Terraform** >= 1.0 installed:
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

3. **AWS Permissions** - Your AWS user/role needs:
   - VPC management (create VPC, subnets, route tables, etc.)
   - Security group management
   - VPC endpoint management
   - CloudWatch Logs management
   - IAM role management (for VPC Flow Logs)

## Quick Start

### 1. Initialize Terraform

```bash
cd terraform
terraform init
```

### 2. Review Configuration

Edit `variables.tf` to customize:
- `project_name` - Project name (default: "afirgen")
- `environment` - Environment (dev/staging/prod)
- `aws_region` - AWS region (default: "us-east-1")
- `vpc_cidr` - VPC CIDR block (default: "10.0.0.0/16")
- `availability_zones` - AZs to use
- `public_subnet_cidrs` - Public subnet CIDR blocks
- `private_subnet_cidrs` - Private subnet CIDR blocks

### 3. Plan Deployment

```bash
terraform plan
```

Review the planned changes carefully. You should see:
- 1 VPC
- 4 subnets (2 public, 2 private)
- 1 Internet Gateway
- 2 NAT Gateways
- 10 security groups
- 8 VPC endpoints
- VPC Flow Logs configuration

### 4. Deploy Infrastructure

```bash
terraform apply
```

Type `yes` when prompted to confirm.

### 5. Verify Deployment

```bash
# View outputs
terraform output

# Get security group IDs
terraform output security_group_ids

# Get VPC endpoint IDs
terraform output vpc_endpoint_ids
```

## Configuration Options

### Basic Configuration

Create a `terraform.tfvars` file:

```hcl
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

tags = {
  Owner       = "DevOps Team"
  CostCenter  = "Engineering"
  Compliance  = "PCI-DSS"
}
```

### Cost Optimization

To reduce costs, you can:

1. **Disable NAT Gateway** (use VPC endpoints only):
   ```hcl
   enable_nat_gateway = false
   ```
   Saves: ~$65/month per AZ

2. **Use single AZ** (not recommended for production):
   ```hcl
   availability_zones   = ["us-east-1a"]
   public_subnet_cidrs  = ["10.0.1.0/24"]
   private_subnet_cidrs = ["10.0.10.0/24"]
   ```
   Saves: ~$100/month (NAT Gateway + VPC endpoints)

3. **Disable optional endpoints**:
   ```hcl
   enable_sts_endpoint  = false
   enable_xray_endpoint = false
   ```
   Saves: ~$14/month per endpoint per AZ

## Security Groups

### Components and Ports

| Component | Inbound | Outbound |
|-----------|---------|----------|
| ALB | 443, 80 from Internet | 80, 443 to Nginx |
| Nginx | 80, 443 from ALB | 8000 to Backend, 80 to Frontend |
| Main Backend | 8000 from Nginx | 8001, 8002, 3306, 2049, 443 |
| GGUF Server | 8001 from Backend | 443 to S3 |
| ASR/OCR Server | 8002 from Backend | 443 to S3 |
| Frontend | 80 from Nginx | None |
| RDS | 3306 from Backend, Backup | None |
| EFS | 2049 from Backend | None |
| Backup | None | 3306, 443 |
| VPC Endpoints | 443 from ECS services | None |

### Least Privilege Principles

1. **No direct internet access** for internal services
2. **Service-to-service** communication only where needed
3. **Port restrictions** - only required ports open
4. **Source restrictions** - security group references, not CIDR blocks
5. **Egress filtering** - explicit egress rules

## VPC Endpoints

### Gateway Endpoints (Free)
- **S3** - Model downloads, backups, logs

### Interface Endpoints ($7.20/month each per AZ)
- **Secrets Manager** - Credentials
- **CloudWatch Logs** - Application logs
- **CloudWatch Monitoring** - Metrics
- **ECR API** - Docker image metadata
- **ECR DKR** - Docker image layers
- **ECS** - Container orchestration
- **ECS Telemetry** - Task metrics

### Optional Endpoints
- **STS** - IAM role assumption (set `enable_sts_endpoint = true`)
- **X-Ray** - Distributed tracing (set `enable_xray_endpoint = true`)

## Validation

After deployment, validate the configuration:

```bash
# Run validation script
cd ..
python test_security_groups.py --region us-east-1 --project afirgen

# Check VPC Flow Logs
aws logs tail /aws/vpc/afirgen-flow-logs --follow

# List security groups
aws ec2 describe-security-groups \
  --filters "Name=tag:Project,Values=afirgen" \
  --query 'SecurityGroups[*].[GroupId,GroupName]' \
  --output table
```

## Updating Infrastructure

### Modify Configuration

1. Edit `variables.tf` or create `terraform.tfvars`
2. Run `terraform plan` to preview changes
3. Run `terraform apply` to apply changes

### Add New Security Group Rule

1. Edit `security_groups.tf`
2. Add new rule:
   ```hcl
   resource "aws_security_group_rule" "new_rule" {
     type                     = "ingress"
     from_port                = 8080
     to_port                  = 8080
     protocol                 = "tcp"
     source_security_group_id = aws_security_group.source.id
     description              = "Allow traffic from source"
     security_group_id        = aws_security_group.destination.id
   }
   ```
3. Run `terraform plan` and `terraform apply`

## Destroying Infrastructure

**WARNING**: This will delete all resources created by Terraform.

```bash
# Preview what will be destroyed
terraform plan -destroy

# Destroy all resources
terraform destroy
```

Type `yes` when prompted to confirm.

## State Management

### Local State (Default)

Terraform state is stored locally in `terraform.tfstate`. This is fine for testing but not recommended for production.

### Remote State (Recommended)

For production, use S3 backend:

1. Create S3 bucket and DynamoDB table:
   ```bash
   aws s3 mb s3://afirgen-terraform-state
   aws dynamodb create-table \
     --table-name afirgen-terraform-locks \
     --attribute-definitions AttributeName=LockID,AttributeType=S \
     --key-schema AttributeName=LockID,KeyType=HASH \
     --billing-mode PAY_PER_REQUEST
   ```

2. Uncomment backend configuration in `main.tf`:
   ```hcl
   backend "s3" {
     bucket         = "afirgen-terraform-state"
     key            = "security-groups/terraform.tfstate"
     region         = "us-east-1"
     encrypt        = true
     dynamodb_table = "afirgen-terraform-locks"
   }
   ```

3. Initialize backend:
   ```bash
   terraform init -migrate-state
   ```

## Troubleshooting

### Error: VPC already exists

If you get an error about VPC already existing, either:
1. Import existing VPC: `terraform import aws_vpc.main vpc-xxxxx`
2. Use a different project name in `variables.tf`

### Error: Insufficient permissions

Ensure your AWS user/role has the required permissions. Check IAM policies.

### Error: Resource limit exceeded

AWS has limits on resources (e.g., 5 VPCs per region). Request limit increase via AWS Support.

### Connection timeouts after deployment

1. Check security group rules
2. Verify VPC Flow Logs for rejected connections
3. Ensure services are running in correct subnets
4. Verify route tables

## Cost Estimate

| Component | Monthly Cost |
|-----------|--------------|
| NAT Gateway (2 AZ) | $64.80 |
| NAT Data Transfer (100GB) | $4.50 |
| VPC Endpoints (7 × 2 AZ) | $100.80 |
| VPC Flow Logs (100GB) | $0.50 |
| **Total** | **~$170.60** |

## Support

For issues or questions:
1. Check [SECURITY-GROUPS-IMPLEMENTATION.md](../SECURITY-GROUPS-IMPLEMENTATION.md)
2. Check [SECURITY-GROUPS-QUICK-REFERENCE.md](../SECURITY-GROUPS-QUICK-REFERENCE.md)
3. Run validation script: `python test_security_groups.py`
4. Review VPC Flow Logs
5. Contact AWS Support

## References

- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS VPC Documentation](https://docs.aws.amazon.com/vpc/)
- [AWS Security Groups](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_SecurityGroups.html)
- [AWS VPC Endpoints](https://docs.aws.amazon.com/vpc/latest/privatelink/vpc-endpoints.html)
