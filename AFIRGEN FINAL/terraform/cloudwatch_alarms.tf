/**
 * CloudWatch Alarms for AFIRGen
 * Monitors key metrics and triggers alerts when thresholds are exceeded
 */

# SNS Topic for CloudWatch Alarms
resource "aws_sns_topic" "cloudwatch_alarms" {
  name = "${var.environment}-afirgen-cloudwatch-alarms"
  
  tags = {
    Name        = "${var.environment}-afirgen-alarms"
    Environment = var.environment
    Service     = "AFIRGen"
  }
}

resource "aws_sns_topic_subscription" "alarm_email" {
  count     = var.alarm_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.cloudwatch_alarms.arn
  protocol  = "email"
  endpoint  = var.alarm_email
}

# High Error Rate Alarm (>5% error rate)
resource "aws_cloudwatch_metric_alarm" "high_error_rate" {
  alarm_name          = "${var.environment}-afirgen-high-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  threshold           = 5.0
  alarm_description   = "Alert when API error rate exceeds 5%"
  alarm_actions       = [aws_sns_topic.cloudwatch_alarms.arn]
  treat_missing_data  = "notBreaching"

  metric_query {
    id          = "error_rate"
    expression  = "100 * errors / requests"
    label       = "Error Rate %"
    return_data = true
  }

  metric_query {
    id = "errors"
    metric {
      namespace   = "AFIRGen"
      metric_name = "APIErrors"
      period      = 300
      stat        = "Sum"
    }
  }

  metric_query {
    id = "requests"
    metric {
      namespace   = "AFIRGen"
      metric_name = "APIRequests"
      period      = 300
      stat        = "Sum"
    }
  }

  tags = {
    Name        = "${var.environment}-high-error-rate"
    Environment = var.environment
    Severity    = "High"
  }
}

# High API Latency Alarm (P95 > 30 seconds)
resource "aws_cloudwatch_metric_alarm" "high_api_latency" {
  alarm_name          = "${var.environment}-afirgen-high-api-latency"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "APILatency"
  namespace           = "AFIRGen"
  period              = 300
  statistic           = "p95"
  threshold           = 30000  # 30 seconds in milliseconds
  alarm_description   = "Alert when P95 API latency exceeds 30 seconds"
  alarm_actions       = [aws_sns_topic.cloudwatch_alarms.arn]
  treat_missing_data  = "notBreaching"

  tags = {
    Name        = "${var.environment}-high-api-latency"
    Environment = var.environment
    Severity    = "Medium"
  }
}

# FIR Generation Failures Alarm
resource "aws_cloudwatch_metric_alarm" "fir_generation_failures" {
  alarm_name          = "${var.environment}-afirgen-fir-generation-failures"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "FIRGenerations"
  namespace           = "AFIRGen"
  period              = 300
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "Alert when FIR generation failures exceed 5 in 5 minutes"
  alarm_actions       = [aws_sns_topic.cloudwatch_alarms.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    Status = "Failure"
  }

  tags = {
    Name        = "${var.environment}-fir-failures"
    Environment = var.environment
    Severity    = "High"
  }
}

# Database Connection Failures Alarm
resource "aws_cloudwatch_metric_alarm" "database_failures" {
  alarm_name          = "${var.environment}-afirgen-database-failures"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "DatabaseOperations"
  namespace           = "AFIRGen"
  period              = 300
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "Alert when database operation failures exceed 10 in 5 minutes"
  alarm_actions       = [aws_sns_topic.cloudwatch_alarms.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    Status = "Failure"
  }

  tags = {
    Name        = "${var.environment}-database-failures"
    Environment = var.environment
    Severity    = "Critical"
  }
}

# High Rate Limiting Alarm (many blocked requests)
resource "aws_cloudwatch_metric_alarm" "high_rate_limiting" {
  alarm_name          = "${var.environment}-afirgen-high-rate-limiting"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "RateLimitEvents"
  namespace           = "AFIRGen"
  period              = 300
  statistic           = "Sum"
  threshold           = 100
  alarm_description   = "Alert when rate limit blocks exceed 100 in 5 minutes"
  alarm_actions       = [aws_sns_topic.cloudwatch_alarms.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    Result = "Blocked"
  }

  tags = {
    Name        = "${var.environment}-high-rate-limiting"
    Environment = var.environment
    Severity    = "Medium"
  }
}

# Authentication Failures Alarm
resource "aws_cloudwatch_metric_alarm" "auth_failures" {
  alarm_name          = "${var.environment}-afirgen-auth-failures"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "AuthenticationEvents"
  namespace           = "AFIRGen"
  period              = 300
  statistic           = "Sum"
  threshold           = 50
  alarm_description   = "Alert when authentication failures exceed 50 in 5 minutes"
  alarm_actions       = [aws_sns_topic.cloudwatch_alarms.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    Status = "Failure"
  }

  tags = {
    Name        = "${var.environment}-auth-failures"
    Environment = var.environment
    Severity    = "High"
  }
}

# Service Unhealthy Alarm
resource "aws_cloudwatch_metric_alarm" "service_unhealthy" {
  alarm_name          = "${var.environment}-afirgen-service-unhealthy"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "HealthChecks"
  namespace           = "AFIRGen"
  period              = 60
  statistic           = "Sum"
  threshold           = 3
  alarm_description   = "Alert when service health checks fail"
  alarm_actions       = [aws_sns_topic.cloudwatch_alarms.arn]
  treat_missing_data  = "breaching"

  dimensions = {
    Status = "Unhealthy"
  }

  tags = {
    Name        = "${var.environment}-service-unhealthy"
    Environment = var.environment
    Severity    = "Critical"
  }
}

# Model Inference Slow Performance Alarm
resource "aws_cloudwatch_metric_alarm" "slow_model_inference" {
  alarm_name          = "${var.environment}-afirgen-slow-model-inference"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ModelInferenceDuration"
  namespace           = "AFIRGen"
  period              = 300
  statistic           = "Average"
  threshold           = 10000  # 10 seconds in milliseconds
  alarm_description   = "Alert when average model inference time exceeds 10 seconds"
  alarm_actions       = [aws_sns_topic.cloudwatch_alarms.arn]
  treat_missing_data  = "notBreaching"

  tags = {
    Name        = "${var.environment}-slow-model-inference"
    Environment = var.environment
    Severity    = "Medium"
  }
}

# Low Cache Hit Rate Alarm (<50%)
resource "aws_cloudwatch_metric_alarm" "low_cache_hit_rate" {
  alarm_name          = "${var.environment}-afirgen-low-cache-hit-rate"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 3
  threshold           = 50.0
  alarm_description   = "Alert when cache hit rate falls below 50%"
  alarm_actions       = [aws_sns_topic.cloudwatch_alarms.arn]
  treat_missing_data  = "notBreaching"

  metric_query {
    id          = "hit_rate"
    expression  = "100 * hits / (hits + misses)"
    label       = "Cache Hit Rate %"
    return_data = true
  }

  metric_query {
    id = "hits"
    metric {
      namespace   = "AFIRGen"
      metric_name = "CacheOperations"
      period      = 300
      stat        = "Sum"
      dimensions = {
        Result = "Hit"
      }
    }
  }

  metric_query {
    id = "misses"
    metric {
      namespace   = "AFIRGen"
      metric_name = "CacheOperations"
      period      = 300
      stat        = "Sum"
      dimensions = {
        Result = "Miss"
      }
    }
  }

  tags = {
    Name        = "${var.environment}-low-cache-hit-rate"
    Environment = var.environment
    Severity    = "Low"
  }
}

# Composite Alarm - Critical System Health
resource "aws_cloudwatch_composite_alarm" "critical_system_health" {
  alarm_name          = "${var.environment}-afirgen-critical-system-health"
  alarm_description   = "Composite alarm for critical system health issues"
  actions_enabled     = true
  alarm_actions       = [aws_sns_topic.cloudwatch_alarms.arn]

  alarm_rule = join(" OR ", [
    "ALARM(${aws_cloudwatch_metric_alarm.high_error_rate.alarm_name})",
    "ALARM(${aws_cloudwatch_metric_alarm.database_failures.alarm_name})",
    "ALARM(${aws_cloudwatch_metric_alarm.service_unhealthy.alarm_name})"
  ])

  tags = {
    Name        = "${var.environment}-critical-health"
    Environment = var.environment
    Severity    = "Critical"
  }
}
