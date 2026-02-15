# AFIRGen AWS Security Groups - Least Privilege Configuration
# This file defines security groups for all AFIRGen components following AWS best practices

# ============================================================================
# Application Load Balancer Security Group
# ============================================================================
resource "aws_security_group" "alb" {
  name_prefix = "${var.project_name}-alb-"
  description = "Security group for Application Load Balancer - allows HTTPS from internet"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name        = "${var.project_name}-alb-sg"
    Component   = "LoadBalancer"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Allow HTTPS inbound from internet
resource "aws_security_group_rule" "alb_https_inbound" {
  type              = "ingress"
  from_port         = 443
  to_port           = 443
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  ipv6_cidr_blocks  = ["::/0"]
  description       = "Allow HTTPS traffic from internet"
  security_group_id = aws_security_group.alb.id
}

# Allow HTTP inbound for redirect to HTTPS
resource "aws_security_group_rule" "alb_http_inbound" {
  type              = "ingress"
  from_port         = 80
  to_port           = 80
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  ipv6_cidr_blocks  = ["::/0"]
  description       = "Allow HTTP traffic for redirect to HTTPS"
  security_group_id = aws_security_group.alb.id
}

# Allow outbound to ECS services only
resource "aws_security_group_rule" "alb_to_nginx" {
  type                     = "egress"
  from_port                = 80
  to_port                  = 80
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.nginx.id
  description              = "Allow traffic to Nginx reverse proxy"
  security_group_id        = aws_security_group.alb.id
}

resource "aws_security_group_rule" "alb_to_nginx_https" {
  type                     = "egress"
  from_port                = 443
  to_port                  = 443
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.nginx.id
  description              = "Allow HTTPS traffic to Nginx reverse proxy"
  security_group_id        = aws_security_group.alb.id
}

# ============================================================================
# Nginx Reverse Proxy Security Group
# ============================================================================
resource "aws_security_group" "nginx" {
  name_prefix = "${var.project_name}-nginx-"
  description = "Security group for Nginx reverse proxy - accepts traffic from ALB only"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name        = "${var.project_name}-nginx-sg"
    Component   = "ReverseProxy"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Allow HTTP from ALB only
resource "aws_security_group_rule" "nginx_from_alb_http" {
  type                     = "ingress"
  from_port                = 80
  to_port                  = 80
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.alb.id
  description              = "Allow HTTP from ALB"
  security_group_id        = aws_security_group.nginx.id
}

# Allow HTTPS from ALB only
resource "aws_security_group_rule" "nginx_from_alb_https" {
  type                     = "ingress"
  from_port                = 443
  to_port                  = 443
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.alb.id
  description              = "Allow HTTPS from ALB"
  security_group_id        = aws_security_group.nginx.id
}

# Allow outbound to main backend
resource "aws_security_group_rule" "nginx_to_main_backend" {
  type                     = "egress"
  from_port                = 8000
  to_port                  = 8000
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.main_backend.id
  description              = "Allow traffic to main backend API"
  security_group_id        = aws_security_group.nginx.id
}

# Allow outbound to frontend
resource "aws_security_group_rule" "nginx_to_frontend" {
  type                     = "egress"
  from_port                = 80
  to_port                  = 80
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.frontend.id
  description              = "Allow traffic to frontend service"
  security_group_id        = aws_security_group.nginx.id
}

# ============================================================================
# Main Backend Security Group
# ============================================================================
resource "aws_security_group" "main_backend" {
  name_prefix = "${var.project_name}-main-backend-"
  description = "Security group for main backend API - accepts traffic from Nginx only"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name        = "${var.project_name}-main-backend-sg"
    Component   = "MainBackend"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Allow inbound from Nginx only
resource "aws_security_group_rule" "main_backend_from_nginx" {
  type                     = "ingress"
  from_port                = 8000
  to_port                  = 8000
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.nginx.id
  description              = "Allow traffic from Nginx reverse proxy"
  security_group_id        = aws_security_group.main_backend.id
}

# Allow outbound to GGUF model server
resource "aws_security_group_rule" "main_backend_to_gguf" {
  type                     = "egress"
  from_port                = 8001
  to_port                  = 8001
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.gguf_model_server.id
  description              = "Allow traffic to GGUF model server"
  security_group_id        = aws_security_group.main_backend.id
}

# Allow outbound to ASR/OCR server
resource "aws_security_group_rule" "main_backend_to_asr_ocr" {
  type                     = "egress"
  from_port                = 8002
  to_port                  = 8002
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.asr_ocr_server.id
  description              = "Allow traffic to ASR/OCR model server"
  security_group_id        = aws_security_group.main_backend.id
}

# Allow outbound to RDS MySQL
resource "aws_security_group_rule" "main_backend_to_rds" {
  type                     = "egress"
  from_port                = 3306
  to_port                  = 3306
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.rds.id
  description              = "Allow traffic to RDS MySQL database"
  security_group_id        = aws_security_group.main_backend.id
}

# Allow outbound to EFS (ChromaDB)
resource "aws_security_group_rule" "main_backend_to_efs" {
  type                     = "egress"
  from_port                = 2049
  to_port                  = 2049
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.efs.id
  description              = "Allow NFS traffic to EFS for ChromaDB"
  security_group_id        = aws_security_group.main_backend.id
}

# Allow outbound HTTPS for AWS Secrets Manager and S3
resource "aws_security_group_rule" "main_backend_to_aws_services" {
  type              = "egress"
  from_port         = 443
  to_port           = 443
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  description       = "Allow HTTPS to AWS services (Secrets Manager, S3) via VPC endpoints"
  security_group_id = aws_security_group.main_backend.id
}

# ============================================================================
# GGUF Model Server Security Group
# ============================================================================
resource "aws_security_group" "gguf_model_server" {
  name_prefix = "${var.project_name}-gguf-"
  description = "Security group for GGUF model server - accepts traffic from main backend only"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name        = "${var.project_name}-gguf-model-server-sg"
    Component   = "GGUFModelServer"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Allow inbound from main backend only
resource "aws_security_group_rule" "gguf_from_main_backend" {
  type                     = "ingress"
  from_port                = 8001
  to_port                  = 8001
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.main_backend.id
  description              = "Allow traffic from main backend"
  security_group_id        = aws_security_group.gguf_model_server.id
}

# Allow outbound HTTPS for model downloads from S3
resource "aws_security_group_rule" "gguf_to_s3" {
  type              = "egress"
  from_port         = 443
  to_port           = 443
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  description       = "Allow HTTPS to S3 for model downloads via VPC endpoint"
  security_group_id = aws_security_group.gguf_model_server.id
}

# ============================================================================
# ASR/OCR Model Server Security Group
# ============================================================================
resource "aws_security_group" "asr_ocr_server" {
  name_prefix = "${var.project_name}-asr-ocr-"
  description = "Security group for ASR/OCR server - accepts traffic from main backend only"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name        = "${var.project_name}-asr-ocr-server-sg"
    Component   = "ASROCRServer"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Allow inbound from main backend only
resource "aws_security_group_rule" "asr_ocr_from_main_backend" {
  type                     = "ingress"
  from_port                = 8002
  to_port                  = 8002
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.main_backend.id
  description              = "Allow traffic from main backend"
  security_group_id        = aws_security_group.asr_ocr_server.id
}

# Allow outbound HTTPS for model downloads from S3
resource "aws_security_group_rule" "asr_ocr_to_s3" {
  type              = "egress"
  from_port         = 443
  to_port           = 443
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  description       = "Allow HTTPS to S3 for model downloads via VPC endpoint"
  security_group_id = aws_security_group.asr_ocr_server.id
}

# ============================================================================
# Frontend Security Group
# ============================================================================
resource "aws_security_group" "frontend" {
  name_prefix = "${var.project_name}-frontend-"
  description = "Security group for frontend service - accepts traffic from Nginx only"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name        = "${var.project_name}-frontend-sg"
    Component   = "Frontend"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Allow inbound from Nginx only
resource "aws_security_group_rule" "frontend_from_nginx" {
  type                     = "ingress"
  from_port                = 80
  to_port                  = 80
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.nginx.id
  description              = "Allow traffic from Nginx reverse proxy"
  security_group_id        = aws_security_group.frontend.id
}

# No outbound rules needed - frontend is static content only

# ============================================================================
# RDS MySQL Security Group
# ============================================================================
resource "aws_security_group" "rds" {
  name_prefix = "${var.project_name}-rds-"
  description = "Security group for RDS MySQL - accepts traffic from main backend and backup service only"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name        = "${var.project_name}-rds-sg"
    Component   = "Database"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Allow MySQL from main backend only
resource "aws_security_group_rule" "rds_from_main_backend" {
  type                     = "ingress"
  from_port                = 3306
  to_port                  = 3306
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.main_backend.id
  description              = "Allow MySQL traffic from main backend"
  security_group_id        = aws_security_group.rds.id
}

# Allow MySQL from backup service
resource "aws_security_group_rule" "rds_from_backup" {
  type                     = "ingress"
  from_port                = 3306
  to_port                  = 3306
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.backup.id
  description              = "Allow MySQL traffic from backup service"
  security_group_id        = aws_security_group.rds.id
}

# No outbound rules needed - RDS doesn't initiate connections

# ============================================================================
# EFS Security Group (for ChromaDB)
# ============================================================================
resource "aws_security_group" "efs" {
  name_prefix = "${var.project_name}-efs-"
  description = "Security group for EFS - accepts NFS traffic from main backend only"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name        = "${var.project_name}-efs-sg"
    Component   = "Storage"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Allow NFS from main backend only
resource "aws_security_group_rule" "efs_from_main_backend" {
  type                     = "ingress"
  from_port                = 2049
  to_port                  = 2049
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.main_backend.id
  description              = "Allow NFS traffic from main backend for ChromaDB"
  security_group_id        = aws_security_group.efs.id
}

# No outbound rules needed - EFS doesn't initiate connections

# ============================================================================
# Backup Service Security Group
# ============================================================================
resource "aws_security_group" "backup" {
  name_prefix = "${var.project_name}-backup-"
  description = "Security group for backup service - connects to RDS and S3 only"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name        = "${var.project_name}-backup-sg"
    Component   = "Backup"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Allow outbound to RDS MySQL
resource "aws_security_group_rule" "backup_to_rds" {
  type                     = "egress"
  from_port                = 3306
  to_port                  = 3306
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.rds.id
  description              = "Allow MySQL traffic to RDS for backups"
  security_group_id        = aws_security_group.backup.id
}

# Allow outbound HTTPS to S3 for backup uploads
resource "aws_security_group_rule" "backup_to_s3" {
  type              = "egress"
  from_port         = 443
  to_port           = 443
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  description       = "Allow HTTPS to S3 for backup uploads via VPC endpoint"
  security_group_id = aws_security_group.backup.id
}

# Allow outbound HTTPS to Secrets Manager
resource "aws_security_group_rule" "backup_to_secrets_manager" {
  type              = "egress"
  from_port         = 443
  to_port           = 443
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  description       = "Allow HTTPS to Secrets Manager via VPC endpoint"
  security_group_id = aws_security_group.backup.id
}

# ============================================================================
# VPC Endpoints Security Group
# ============================================================================
resource "aws_security_group" "vpc_endpoints" {
  name_prefix = "${var.project_name}-vpc-endpoints-"
  description = "Security group for VPC endpoints - accepts HTTPS from ECS services"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name        = "${var.project_name}-vpc-endpoints-sg"
    Component   = "VPCEndpoints"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Allow HTTPS from main backend
resource "aws_security_group_rule" "vpc_endpoints_from_main_backend" {
  type                     = "ingress"
  from_port                = 443
  to_port                  = 443
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.main_backend.id
  description              = "Allow HTTPS from main backend"
  security_group_id        = aws_security_group.vpc_endpoints.id
}

# Allow HTTPS from GGUF model server
resource "aws_security_group_rule" "vpc_endpoints_from_gguf" {
  type                     = "ingress"
  from_port                = 443
  to_port                  = 443
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.gguf_model_server.id
  description              = "Allow HTTPS from GGUF model server"
  security_group_id        = aws_security_group.vpc_endpoints.id
}

# Allow HTTPS from ASR/OCR server
resource "aws_security_group_rule" "vpc_endpoints_from_asr_ocr" {
  type                     = "ingress"
  from_port                = 443
  to_port                  = 443
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.asr_ocr_server.id
  description              = "Allow HTTPS from ASR/OCR server"
  security_group_id        = aws_security_group.vpc_endpoints.id
}

# Allow HTTPS from backup service
resource "aws_security_group_rule" "vpc_endpoints_from_backup" {
  type                     = "ingress"
  from_port                = 443
  to_port                  = 443
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.backup.id
  description              = "Allow HTTPS from backup service"
  security_group_id        = aws_security_group.vpc_endpoints.id
}

# ============================================================================
# Outputs
# ============================================================================
output "security_group_ids" {
  description = "Map of security group IDs for all components"
  value = {
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
}

output "security_group_names" {
  description = "Map of security group names for all components"
  value = {
    alb                = aws_security_group.alb.name
    nginx              = aws_security_group.nginx.name
    main_backend       = aws_security_group.main_backend.name
    gguf_model_server  = aws_security_group.gguf_model_server.name
    asr_ocr_server     = aws_security_group.asr_ocr_server.name
    frontend           = aws_security_group.frontend.name
    rds                = aws_security_group.rds.name
    efs                = aws_security_group.efs.id
    backup             = aws_security_group.backup.name
    vpc_endpoints      = aws_security_group.vpc_endpoints.name
  }
}
