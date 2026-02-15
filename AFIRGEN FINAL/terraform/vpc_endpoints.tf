# AFIRGen VPC Endpoints Configuration
# VPC endpoints provide private connectivity to AWS services without internet gateway

# ============================================================================
# S3 Gateway Endpoint (No additional cost)
# ============================================================================
resource "aws_vpc_endpoint" "s3" {
  vpc_id       = aws_vpc.main.id
  service_name = "com.amazonaws.${var.aws_region}.s3"
  
  # Gateway endpoints use route tables
  route_table_ids = concat(
    [aws_route_table.public.id],
    aws_route_table.private[*].id
  )

  tags = merge(
    {
      Name        = "${var.project_name}-s3-endpoint"
      Service     = "S3"
      Type        = "Gateway"
      Environment = var.environment
      ManagedBy   = "Terraform"
    },
    var.tags
  )
}

# S3 Endpoint Policy - Restrict to project buckets only
resource "aws_vpc_endpoint_policy" "s3" {
  vpc_endpoint_id = aws_vpc_endpoint.s3.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = "*"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${var.project_name}-*",
          "arn:aws:s3:::${var.project_name}-*/*"
        ]
      }
    ]
  })
}

# ============================================================================
# Secrets Manager Interface Endpoint
# ============================================================================
resource "aws_vpc_endpoint" "secrets_manager" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.aws_region}.secretsmanager"
  vpc_endpoint_type   = "Interface"
  
  # Deploy in private subnets
  subnet_ids = aws_subnet.private[*].id
  
  # Use VPC endpoints security group
  security_group_ids = [aws_security_group.vpc_endpoints.id]
  
  # Enable private DNS
  private_dns_enabled = true

  tags = merge(
    {
      Name        = "${var.project_name}-secrets-manager-endpoint"
      Service     = "SecretsManager"
      Type        = "Interface"
      Environment = var.environment
      ManagedBy   = "Terraform"
    },
    var.tags
  )
}

# ============================================================================
# CloudWatch Logs Interface Endpoint
# ============================================================================
resource "aws_vpc_endpoint" "logs" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.aws_region}.logs"
  vpc_endpoint_type   = "Interface"
  
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true

  tags = merge(
    {
      Name        = "${var.project_name}-logs-endpoint"
      Service     = "CloudWatchLogs"
      Type        = "Interface"
      Environment = var.environment
      ManagedBy   = "Terraform"
    },
    var.tags
  )
}

# ============================================================================
# ECR API Interface Endpoint (for Docker image metadata)
# ============================================================================
resource "aws_vpc_endpoint" "ecr_api" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.aws_region}.ecr.api"
  vpc_endpoint_type   = "Interface"
  
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true

  tags = merge(
    {
      Name        = "${var.project_name}-ecr-api-endpoint"
      Service     = "ECR-API"
      Type        = "Interface"
      Environment = var.environment
      ManagedBy   = "Terraform"
    },
    var.tags
  )
}

# ============================================================================
# ECR DKR Interface Endpoint (for Docker image layers)
# ============================================================================
resource "aws_vpc_endpoint" "ecr_dkr" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.aws_region}.ecr.dkr"
  vpc_endpoint_type   = "Interface"
  
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true

  tags = merge(
    {
      Name        = "${var.project_name}-ecr-dkr-endpoint"
      Service     = "ECR-DKR"
      Type        = "Interface"
      Environment = var.environment
      ManagedBy   = "Terraform"
    },
    var.tags
  )
}

# ============================================================================
# ECS Interface Endpoint (for ECS API calls)
# ============================================================================
resource "aws_vpc_endpoint" "ecs" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.aws_region}.ecs"
  vpc_endpoint_type   = "Interface"
  
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true

  tags = merge(
    {
      Name        = "${var.project_name}-ecs-endpoint"
      Service     = "ECS"
      Type        = "Interface"
      Environment = var.environment
      ManagedBy   = "Terraform"
    },
    var.tags
  )
}

# ============================================================================
# ECS Telemetry Interface Endpoint (for ECS task metrics)
# ============================================================================
resource "aws_vpc_endpoint" "ecs_telemetry" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.aws_region}.ecs-telemetry"
  vpc_endpoint_type   = "Interface"
  
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true

  tags = merge(
    {
      Name        = "${var.project_name}-ecs-telemetry-endpoint"
      Service     = "ECS-Telemetry"
      Type        = "Interface"
      Environment = var.environment
      ManagedBy   = "Terraform"
    },
    var.tags
  )
}

# ============================================================================
# CloudWatch Monitoring Interface Endpoint (for CloudWatch metrics)
# ============================================================================
resource "aws_vpc_endpoint" "monitoring" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.aws_region}.monitoring"
  vpc_endpoint_type   = "Interface"
  
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true

  tags = merge(
    {
      Name        = "${var.project_name}-monitoring-endpoint"
      Service     = "CloudWatchMonitoring"
      Type        = "Interface"
      Environment = var.environment
      ManagedBy   = "Terraform"
    },
    var.tags
  )
}

# ============================================================================
# Optional: STS Interface Endpoint (for IAM role assumption)
# ============================================================================
resource "aws_vpc_endpoint" "sts" {
  count               = var.enable_sts_endpoint ? 1 : 0
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.aws_region}.sts"
  vpc_endpoint_type   = "Interface"
  
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true

  tags = merge(
    {
      Name        = "${var.project_name}-sts-endpoint"
      Service     = "STS"
      Type        = "Interface"
      Environment = var.environment
      ManagedBy   = "Terraform"
    },
    var.tags
  )
}

# ============================================================================
# Optional: X-Ray Interface Endpoint (for distributed tracing)
# ============================================================================
resource "aws_vpc_endpoint" "xray" {
  count               = var.enable_xray_endpoint ? 1 : 0
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.aws_region}.xray"
  vpc_endpoint_type   = "Interface"
  
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true

  tags = merge(
    {
      Name        = "${var.project_name}-xray-endpoint"
      Service     = "X-Ray"
      Type        = "Interface"
      Environment = var.environment
      ManagedBy   = "Terraform"
    },
    var.tags
  )
}

# ============================================================================
# Outputs
# ============================================================================
output "vpc_endpoint_ids" {
  description = "Map of VPC endpoint IDs"
  value = {
    s3              = aws_vpc_endpoint.s3.id
    secrets_manager = aws_vpc_endpoint.secrets_manager.id
    logs            = aws_vpc_endpoint.logs.id
    ecr_api         = aws_vpc_endpoint.ecr_api.id
    ecr_dkr         = aws_vpc_endpoint.ecr_dkr.id
    ecs             = aws_vpc_endpoint.ecs.id
    ecs_telemetry   = aws_vpc_endpoint.ecs_telemetry.id
    monitoring      = aws_vpc_endpoint.monitoring.id
  }
}

output "vpc_endpoint_dns_entries" {
  description = "DNS entries for VPC endpoints"
  value = {
    secrets_manager = aws_vpc_endpoint.secrets_manager.dns_entry
    logs            = aws_vpc_endpoint.logs.dns_entry
    ecr_api         = aws_vpc_endpoint.ecr_api.dns_entry
    ecr_dkr         = aws_vpc_endpoint.ecr_dkr.dns_entry
    ecs             = aws_vpc_endpoint.ecs.dns_entry
    ecs_telemetry   = aws_vpc_endpoint.ecs_telemetry.dns_entry
    monitoring      = aws_vpc_endpoint.monitoring.dns_entry
  }
}
