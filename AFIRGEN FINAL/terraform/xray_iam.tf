# xray_iam.tf
# IAM roles and policies for AWS X-Ray distributed tracing

# X-Ray policy for ECS task roles
resource "aws_iam_policy" "xray_write_policy" {
  name        = "afirgen-xray-write-policy"
  description = "Allow ECS tasks to write traces to AWS X-Ray"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "xray:PutTraceSegments",
          "xray:PutTelemetryRecords",
          "xray:GetSamplingRules",
          "xray:GetSamplingTargets",
          "xray:GetSamplingStatisticSummaries"
        ]
        Resource = "*"
      }
    ]
  })

  tags = {
    Name        = "afirgen-xray-write-policy"
    Environment = var.environment
    Service     = "xray"
  }
}

# Attach X-Ray policy to main backend task role
resource "aws_iam_role_policy_attachment" "main_backend_xray" {
  role       = aws_iam_role.main_backend_task_role.name
  policy_arn = aws_iam_policy.xray_write_policy.arn
}

# Attach X-Ray policy to GGUF model server task role
resource "aws_iam_role_policy_attachment" "gguf_server_xray" {
  role       = aws_iam_role.gguf_server_task_role.name
  policy_arn = aws_iam_policy.xray_write_policy.arn
}

# Attach X-Ray policy to ASR/OCR server task role
resource "aws_iam_role_policy_attachment" "asr_ocr_server_xray" {
  role       = aws_iam_role.asr_ocr_server_task_role.name
  policy_arn = aws_iam_policy.xray_write_policy.arn
}

# CloudWatch log group for X-Ray daemon
resource "aws_cloudwatch_log_group" "xray_daemon" {
  name              = "/ecs/afirgen/xray-daemon"
  retention_in_days = 7

  tags = {
    Name        = "afirgen-xray-daemon-logs"
    Environment = var.environment
    Service     = "xray"
  }
}

# X-Ray sampling rule for cost optimization
resource "aws_xray_sampling_rule" "afirgen_default" {
  rule_name      = "afirgen-default-sampling"
  priority       = 1000
  version        = 1
  reservoir_size = 1
  fixed_rate     = 0.1  # 10% sampling rate
  url_path       = "*"
  host           = "*"
  http_method    = "*"
  service_type   = "*"
  service_name   = "afirgen-*"
  resource_arn   = "*"

  tags = {
    Name        = "afirgen-default-sampling"
    Environment = var.environment
    Service     = "xray"
  }
}

# X-Ray sampling rule for errors (100% sampling)
resource "aws_xray_sampling_rule" "afirgen_errors" {
  rule_name      = "afirgen-error-sampling"
  priority       = 100
  version        = 1
  reservoir_size = 1
  fixed_rate     = 1.0  # 100% sampling for errors
  url_path       = "*"
  host           = "*"
  http_method    = "*"
  service_type   = "*"
  service_name   = "afirgen-*"
  resource_arn   = "*"

  # This rule will be applied when response status is 4xx or 5xx
  # Note: Attribute-based sampling requires additional configuration in application

  tags = {
    Name        = "afirgen-error-sampling"
    Environment = var.environment
    Service     = "xray"
  }
}

# X-Ray group for AFIRGen services
resource "aws_xray_group" "afirgen_services" {
  group_name        = "afirgen-services"
  filter_expression = "service(\"afirgen-*\")"

  insights_configuration {
    insights_enabled      = true
    notifications_enabled = false
  }

  tags = {
    Name        = "afirgen-services"
    Environment = var.environment
    Service     = "xray"
  }
}

# Outputs
output "xray_policy_arn" {
  description = "ARN of the X-Ray write policy"
  value       = aws_iam_policy.xray_write_policy.arn
}

output "xray_log_group_name" {
  description = "Name of the X-Ray daemon CloudWatch log group"
  value       = aws_cloudwatch_log_group.xray_daemon.name
}

output "xray_sampling_rule_name" {
  description = "Name of the X-Ray sampling rule"
  value       = aws_xray_sampling_rule.afirgen_default.rule_name
}

output "xray_group_name" {
  description = "Name of the X-Ray group"
  value       = aws_xray_group.afirgen_services.group_name
}
