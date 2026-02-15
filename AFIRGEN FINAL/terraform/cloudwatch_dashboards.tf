/**
 * CloudWatch Dashboards for AFIRGen
 * Provides comprehensive monitoring and visualization of key metrics
 */

# Main Application Dashboard
resource "aws_cloudwatch_dashboard" "afirgen_main" {
  dashboard_name = "${var.environment}-afirgen-main-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      # API Performance Section
      {
        type = "metric"
        properties = {
          metrics = [
            ["AFIRGen", "APIRequests", { stat = "Sum", label = "Total Requests" }],
            [".", "APIErrors", { stat = "Sum", label = "Errors" }]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "API Requests & Errors"
          yAxis = {
            left = {
              min = 0
            }
          }
        }
        width  = 12
        height = 6
        x      = 0
        y      = 0
      },
      {
        type = "metric"
        properties = {
          metrics = [
            ["AFIRGen", "APILatency", { stat = "Average", label = "Avg Latency" }],
            ["...", { stat = "p95", label = "P95 Latency" }],
            ["...", { stat = "p99", label = "P99 Latency" }]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "API Latency (ms)"
          yAxis = {
            left = {
              min = 0
            }
          }
        }
        width  = 12
        height = 6
        x      = 12
        y      = 0
      },
      
      # FIR Generation Metrics
      {
        type = "metric"
        properties = {
          metrics = [
            ["AFIRGen", "FIRGenerations", "Status", "Success", { stat = "Sum", label = "Successful" }],
            ["...", "Failure", { stat = "Sum", label = "Failed" }]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "FIR Generations"
          yAxis = {
            left = {
              min = 0
            }
          }
        }
        width  = 12
        height = 6
        x      = 0
        y      = 6
      },
      {
        type = "metric"
        properties = {
          metrics = [
            ["AFIRGen", "FIRGenerationDuration", { stat = "Average", label = "Avg Duration" }],
            ["...", { stat = "p95", label = "P95 Duration" }],
            ["...", { stat = "Maximum", label = "Max Duration" }]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "FIR Generation Duration (ms)"
          yAxis = {
            left = {
              min = 0
            }
          }
        }
        width  = 12
        height = 6
        x      = 12
        y      = 6
      },
      
      # Model Inference Metrics
      {
        type = "metric"
        properties = {
          metrics = [
            ["AFIRGen", "ModelInferences", { stat = "Sum", label = "Total Inferences" }],
            [".", "TokensGenerated", { stat = "Sum", label = "Tokens Generated" }]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "Model Inference Activity"
          yAxis = {
            left = {
              min = 0
            }
          }
        }
        width  = 12
        height = 6
        x      = 0
        y      = 12
      },
      {
        type = "metric"
        properties = {
          metrics = [
            ["AFIRGen", "ModelInferenceDuration", { stat = "Average", label = "Avg Duration" }],
            ["...", { stat = "p95", label = "P95 Duration" }]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "Model Inference Duration (ms)"
          yAxis = {
            left = {
              min = 0
            }
          }
        }
        width  = 12
        height = 6
        x      = 12
        y      = 12
      },
      
      # Database Performance
      {
        type = "metric"
        properties = {
          metrics = [
            ["AFIRGen", "DatabaseOperations", "Status", "Success", { stat = "Sum", label = "Successful" }],
            ["...", "Failure", { stat = "Sum", label = "Failed" }]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "Database Operations"
          yAxis = {
            left = {
              min = 0
            }
          }
        }
        width  = 12
        height = 6
        x      = 0
        y      = 18
      },
      {
        type = "metric"
        properties = {
          metrics = [
            ["AFIRGen", "DatabaseLatency", { stat = "Average", label = "Avg Latency" }],
            ["...", { stat = "p95", label = "P95 Latency" }]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "Database Latency (ms)"
          yAxis = {
            left = {
              min = 0
            }
          }
        }
        width  = 12
        height = 6
        x      = 12
        y      = 18
      },
      
      # Cache Performance
      {
        type = "metric"
        properties = {
          metrics = [
            ["AFIRGen", "CacheOperations", "Result", "Hit", { stat = "Sum", label = "Cache Hits" }],
            ["...", "Miss", { stat = "Sum", label = "Cache Misses" }]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "Cache Performance"
          yAxis = {
            left = {
              min = 0
            }
          }
        }
        width  = 12
        height = 6
        x      = 0
        y      = 24
      },
      
      # Security Metrics
      {
        type = "metric"
        properties = {
          metrics = [
            ["AFIRGen", "RateLimitEvents", "Result", "Blocked", { stat = "Sum", label = "Blocked" }],
            ["...", "Allowed", { stat = "Sum", label = "Allowed" }]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "Rate Limiting Events"
          yAxis = {
            left = {
              min = 0
            }
          }
        }
        width  = 12
        height = 6
        x      = 12
        y      = 24
      },
      {
        type = "metric"
        properties = {
          metrics = [
            ["AFIRGen", "AuthenticationEvents", "Status", "Success", { stat = "Sum", label = "Successful" }],
            ["...", "Failure", { stat = "Sum", label = "Failed" }]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "Authentication Events"
          yAxis = {
            left = {
              min = 0
            }
          }
        }
        width  = 12
        height = 6
        x      = 0
        y      = 30
      },
      
      # Health Check Status
      {
        type = "metric"
        properties = {
          metrics = [
            ["AFIRGen", "HealthChecks", "Status", "Healthy", { stat = "Sum", label = "Healthy" }],
            ["...", "Unhealthy", { stat = "Sum", label = "Unhealthy" }]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "Health Check Status"
          yAxis = {
            left = {
              min = 0
            }
          }
        }
        width  = 12
        height = 6
        x      = 12
        y      = 30
      }
    ]
  })
}

# Error Rate Dashboard
resource "aws_cloudwatch_dashboard" "afirgen_errors" {
  dashboard_name = "${var.environment}-afirgen-errors-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric"
        properties = {
          metrics = [
            ["AFIRGen", "APIErrors", { stat = "Sum" }]
          ]
          period = 60
          stat   = "Sum"
          region = var.aws_region
          title  = "API Error Rate (1 min)"
          yAxis = {
            left = {
              min = 0
            }
          }
        }
        width  = 24
        height = 6
        x      = 0
        y      = 0
      },
      {
        type = "metric"
        properties = {
          metrics = [
            ["AFIRGen", "APIErrors", "StatusCode", "400", { stat = "Sum", label = "400 Bad Request" }],
            ["...", "401", { stat = "Sum", label = "401 Unauthorized" }],
            ["...", "403", { stat = "Sum", label = "403 Forbidden" }],
            ["...", "404", { stat = "Sum", label = "404 Not Found" }],
            ["...", "429", { stat = "Sum", label = "429 Rate Limited" }],
            ["...", "500", { stat = "Sum", label = "500 Internal Error" }],
            ["...", "503", { stat = "Sum", label = "503 Service Unavailable" }]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "Errors by Status Code"
          yAxis = {
            left = {
              min = 0
            }
          }
        }
        width  = 24
        height = 6
        x      = 0
        y      = 6
      },
      {
        type = "log"
        properties = {
          query   = <<-EOT
            SOURCE '/aws/ecs/${var.environment}-afirgen-main-backend'
            | fields @timestamp, level, message, exception.type, exception.message
            | filter level = "ERROR"
            | sort @timestamp desc
            | limit 100
          EOT
          region  = var.aws_region
          title   = "Recent Error Logs"
        }
        width  = 24
        height = 8
        x      = 0
        y      = 12
      }
    ]
  })
}

# Performance Dashboard
resource "aws_cloudwatch_dashboard" "afirgen_performance" {
  dashboard_name = "${var.environment}-afirgen-performance-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      # API Latency Breakdown
      {
        type = "metric"
        properties = {
          metrics = [
            ["AFIRGen", "APILatency", "Endpoint", "/process", { stat = "Average", label = "/process" }],
            ["...", "/validate_step", { stat = "Average", label = "/validate_step" }],
            ["...", "/regenerate_step", { stat = "Average", label = "/regenerate_step" }],
            ["...", "/authenticate_fir", { stat = "Average", label = "/authenticate_fir" }],
            ["...", "/get_session_status", { stat = "Average", label = "/get_session_status" }]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "API Latency by Endpoint (ms)"
          yAxis = {
            left = {
              min = 0
            }
          }
        }
        width  = 24
        height = 6
        x      = 0
        y      = 0
      },
      
      # FIR Generation Steps
      {
        type = "metric"
        properties = {
          metrics = [
            ["AFIRGen", "FIRGenerationDuration", "Step", "summary", { stat = "Average", label = "Summary" }],
            ["...", "violations", { stat = "Average", label = "Violations" }],
            ["...", "narrative", { stat = "Average", label = "Narrative" }]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "FIR Generation Duration by Step (ms)"
          yAxis = {
            left = {
              min = 0
            }
          }
        }
        width  = 24
        height = 6
        x      = 0
        y      = 6
      },
      
      # Model Performance by Type
      {
        type = "metric"
        properties = {
          metrics = [
            ["AFIRGen", "ModelInferenceDuration", "Model", "llama", { stat = "Average", label = "LLaMA" }],
            ["...", "whisper", { stat = "Average", label = "Whisper" }],
            ["...", "ocr", { stat = "Average", label = "OCR" }]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "Model Inference Duration by Type (ms)"
          yAxis = {
            left = {
              min = 0
            }
          }
        }
        width  = 24
        height = 6
        x      = 0
        y      = 12
      },
      
      # Cache Hit Rate
      {
        type = "metric"
        properties = {
          metrics = [
            [{ expression = "100 * hits / (hits + misses)", label = "Cache Hit Rate %" }],
            ["AFIRGen", "CacheOperations", "Result", "Hit", { id = "hits", visible = false }],
            ["...", "Miss", { id = "misses", visible = false }]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "Cache Hit Rate"
          yAxis = {
            left = {
              min = 0
              max = 100
            }
          }
        }
        width  = 12
        height = 6
        x      = 0
        y      = 18
      },
      
      # Database Query Performance
      {
        type = "metric"
        properties = {
          metrics = [
            ["AFIRGen", "DatabaseLatency", "Operation", "save", { stat = "Average", label = "Save" }],
            ["...", "get", { stat = "Average", label = "Get" }],
            ["...", "update", { stat = "Average", label = "Update" }],
            ["...", "list", { stat = "Average", label = "List" }]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "Database Latency by Operation (ms)"
          yAxis = {
            left = {
              min = 0
            }
          }
        }
        width  = 12
        height = 6
        x      = 12
        y      = 18
      }
    ]
  })
}
