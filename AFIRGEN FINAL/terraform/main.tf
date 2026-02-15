# AFIRGen AWS Infrastructure - Main Configuration

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  # Uncomment to use S3 backend for state management
  # backend "s3" {
  #   bucket         = "afirgen-terraform-state"
  #   key            = "security-groups/terraform.tfstate"
  #   region         = "us-east-1"
  #   encrypt        = true
  #   dynamodb_table = "afirgen-terraform-locks"
  # }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
      Repository  = "afirgen"
    }
  }
}

# Data sources for existing resources (if any)
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Outputs
output "account_id" {
  description = "AWS Account ID"
  value       = data.aws_caller_identity.current.account_id
}

output "region" {
  description = "AWS Region"
  value       = data.aws_region.current.name
}

output "deployment_summary" {
  description = "Summary of deployed resources"
  value = {
    vpc_id              = aws_vpc.main.id
    public_subnets      = aws_subnet.public[*].id
    private_subnets     = aws_subnet.private[*].id
    security_groups     = keys(local.security_group_ids)
    vpc_endpoints       = keys(local.vpc_endpoint_ids)
    nat_gateway_ips     = aws_eip.nat[*].public_ip
  }
}

locals {
  security_group_ids = {
    alb                = aws_security_group.alb.id
    nginx              = aws_security_group.nginx.id
    main_backend       = aws_security_group.main_backend.id
    gguf_model_server  = aws_security_group.gguf_model_server.id
    asr_ocr_server     = aws_security_group.asr_ocr_server.id
    frontend           = aws_security_group.frontend.id
    rds                = aws_security_group.rds.id
    efs                = aws_security_group.efs.id
    backup             = aws_security_group.backup.id
    vpc_endpoints      = aws_security_group.vpc_endpoints.id
  }
  
  vpc_endpoint_ids = {
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
