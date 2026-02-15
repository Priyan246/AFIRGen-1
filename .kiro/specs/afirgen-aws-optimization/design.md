# AFIRGen AWS Optimization & Bug Fixes - Design Document

## 1. Overview

This design document outlines the architecture, components, and implementation strategy for deploying AFIRGen to AWS with production-grade reliability, security, and performance. AFIRGen is an AI-powered FIR (First Information Report) generation system that processes audio, images, and text to automatically generate legal documents.

### 1.1 Current State Assessment

Based on code review, the following features have been **successfully implemented**:
- ✅ HTTPS/TLS with Nginx reverse proxy
- ✅ API authentication with X-API-Key and Bearer token support
- ✅ Rate limiting (sliding window algorithm)
- ✅ Input validation and sanitization (XSS, SQL injection, DoS prevention)
- ✅ AWS Secrets Manager integration
- ✅ Structured JSON logging (CloudWatch-compatible)
- ✅ CloudWatch metrics and dashboards
- ✅ Database backups (automated with retention policies)
- ✅ Zero data loss mechanisms (WAL mode, transaction management)
- ✅ Auto-recovery and circuit breakers
- ✅ Performance optimizations (caching, parallel processing)
- ✅ Security groups (Terraform configurations)
- ✅ Docker configuration fixes (paths, volumes, health checks)
- ✅ CORS configuration
- ✅ Graceful shutdown handling

### 1.2 Remaining Work

The following areas require implementation or completion:
- ⚠️ Complete AWS infrastructure deployment (ECS, RDS, S3, ALB)
- ⚠️ ECS task definitions and service configurations
- ⚠️ RDS MySQL setup with Multi-AZ
- ⚠️ S3 bucket configuration for models and temp files
- ⚠️ EFS setup for ChromaDB persistence
- ⚠️ Application Load Balancer with ACM certificates
- ⚠️ Auto-scaling policies
- ⚠️ AWS X-Ray distributed tracing integration
- ⚠️ CI/CD pipeline configuration
- ⚠️ Cost monitoring and optimization
- ⚠️ Model management strategy (S3 download on startup)
- ⚠️ Database migration scripts (Alembic)

### 1.3 Design Goals

1. **Production-Ready**: 99.9% uptime SLA with automated recovery
2. **Cost-Optimized**: Total AWS cost <$500/month for moderate usage
3. **Performant**: <30s FIR generation, <200ms API response time
4. **Secure**: HTTPS, authentication, rate limiting, least privilege access
5. **Observable**: Comprehensive logging, metrics, and tracing
6. **Scalable**: Auto-scaling based on load
7. **Maintainable**: Infrastructure as Code, clear documentation



## 2. Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Internet                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Route 53 (DNS)                                  │
│              afirgen.example.com                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│         Application Load Balancer (ALB)                          │
│         - SSL/TLS Termination (ACM Certificate)                  │
│         - Health Checks                                          │
│         - Target Groups for ECS Services                         │
└────────────────────────┬────────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
┌────────────────┐ ┌────────────┐ ┌────────────────┐
│  Nginx Proxy   │ │  Frontend  │ │  Main Backend  │
│  ECS Service   │ │ ECS Service│ │  ECS Service   │
│  (Port 443)    │ │ (Port 80)  │ │  (Port 8000)   │
└────────┬───────┘ └────────────┘ └────────┬───────┘
         │                                  │
         │         ┌────────────────────────┼────────────────┐
         │         │                        │                │
         │         ▼                        ▼                ▼
         │  ┌──────────────┐      ┌─────────────────┐ ┌──────────────┐
         │  │ GGUF Model   │      │  ASR/OCR Model  │ │  RDS MySQL   │
         │  │ ECS Service  │      │  ECS Service    │ │  Multi-AZ    │
         │  │ (Port 8001)  │      │  (Port 8002)    │ │  (Port 3306) │
         │  └──────┬───────┘      └────────┬────────┘ └──────────────┘
         │         │                       │
         │         └───────────┬───────────┘
         │                     │
         │                     ▼
         │            ┌─────────────────┐
         │            │  EFS (ChromaDB) │
         │            │  Shared Storage │
         │            └─────────────────┘
         │
         └──────────────────────────────────────────┐
                                                    │
                                                    ▼
                                          ┌──────────────────┐
                                          │  S3 Buckets      │
                                          │  - Models        │
                                          │  - Temp Files    │
                                          │  - Backups       │
                                          │  - Logs          │
                                          └──────────────────┘
```

### 2.2 Network Architecture

**VPC Configuration:**
- CIDR: 10.0.0.0/16
- 2 Availability Zones for high availability
- Public Subnets (10.0.1.0/24, 10.0.2.0/24): ALB, NAT Gateways
- Private Subnets (10.0.11.0/24, 10.0.12.0/24): ECS Services, RDS, EFS
- Database Subnets (10.0.21.0/24, 10.0.22.0/24): RDS instances

**VPC Endpoints (Cost Optimization):**
- S3 Gateway Endpoint (no cost)
- Secrets Manager Interface Endpoint
- CloudWatch Logs Interface Endpoint
- ECR API/DKR Interface Endpoints
- ECS Interface Endpoints

**Security Groups:**
Already implemented in Terraform (see `terraform/security_groups.tf`):
- ALB: Allows 80/443 from internet
- Nginx: Allows traffic from ALB
- Main Backend: Allows traffic from Nginx and ALB
- GGUF/ASR-OCR Servers: Allow traffic from Main Backend only
- Frontend: Allows traffic from Nginx
- RDS: Allows 3306 from ECS services only
- EFS: Allows 2049 from ECS services only
- VPC Endpoints: Allow 443 from private subnets



## 3. Components and Interfaces

### 3.1 Compute Layer (ECS Fargate)

#### 3.1.1 Main Backend Service
**Purpose:** Orchestrates FIR generation workflow, handles API requests, manages sessions

**Container Specifications:**
- CPU: 2 vCPU (2048 CPU units)
- Memory: 4 GB
- Port: 8000
- Health Check: GET /health (30s interval, 3 retries)

**Environment Variables:**
- `MYSQL_HOST`: RDS endpoint
- `MYSQL_PORT`: 3306
- `MYSQL_USER`: From Secrets Manager
- `MYSQL_PASSWORD`: From Secrets Manager
- `MYSQL_DB`: fir_db
- `API_KEY`: From Secrets Manager
- `FIR_AUTH_KEY`: From Secrets Manager
- `CORS_ORIGINS`: ALB DNS name
- `RATE_LIMIT_REQUESTS`: 100
- `RATE_LIMIT_WINDOW`: 60
- `AWS_REGION`: us-east-1
- `ENVIRONMENT`: production
- `LOG_LEVEL`: INFO

**Volumes:**
- EFS mount for ChromaDB: `/app/chroma_kb`
- EFS mount for knowledge base: `/app/kb` (read-only)
- EFS mount for sessions: `/app/sessions.db`

**Auto-Scaling:**
- Min: 2 tasks
- Max: 10 tasks
- Target CPU: 70%
- Target Memory: 80%
- Scale-in cooldown: 300s
- Scale-out cooldown: 60s

#### 3.1.2 GGUF Model Server
**Purpose:** LLM inference for summarization and legal analysis

**Container Specifications:**
- CPU: 4 vCPU (4096 CPU units)
- Memory: 8 GB
- Port: 8001
- Health Check: GET /health (30s interval, 3 retries, 180s start period)

**Environment Variables:**
- `MODEL_SERVER_PORT`: 8001
- `MODEL_DIR`: /app/models
- `CORS_ORIGINS`: Main Backend service discovery name

**Volumes:**
- EFS mount for models: `/app/models` (read-only)

**Auto-Scaling:**
- Min: 1 task
- Max: 5 tasks
- Target CPU: 75%
- Scale-in cooldown: 600s (models are expensive to load)
- Scale-out cooldown: 120s

**Model Loading Strategy:**
1. On container startup, check if models exist in EFS
2. If not, download from S3 bucket to EFS
3. Load models into memory with mlock/mmap optimization
4. Cache models in EFS for subsequent container starts

#### 3.1.3 ASR/OCR Server
**Purpose:** Speech-to-text (Whisper) and OCR (dots_ocr) processing

**Container Specifications:**
- CPU: 4 vCPU (4096 CPU units)
- Memory: 8 GB
- Port: 8002
- Health Check: GET /health (30s interval, 3 retries, 180s start period)

**Environment Variables:**
- `ASR_OCR_PORT`: 8002
- `MODEL_DIR`: /app/models
- `CORS_ORIGINS`: Main Backend service discovery name

**Volumes:**
- EFS mount for models: `/app/models` (read-only)
- EFS mount for temp files: `/app/temp_asr_ocr`

**Auto-Scaling:**
- Min: 1 task
- Max: 5 tasks
- Target CPU: 75%
- Scale-in cooldown: 600s
- Scale-out cooldown: 120s

#### 3.1.4 Frontend Service
**Purpose:** Serves static HTML/CSS/JS interface

**Container Specifications:**
- CPU: 0.5 vCPU (512 CPU units)
- Memory: 512 MB
- Port: 80
- Health Check: GET / (30s interval, 3 retries)

**Environment Variables:**
- `API_BASE_URL`: ALB DNS name
- `API_KEY`: From Secrets Manager
- `ENVIRONMENT`: production

**Auto-Scaling:**
- Min: 2 tasks
- Max: 4 tasks
- Target CPU: 70%

#### 3.1.5 Nginx Reverse Proxy
**Purpose:** TLS termination, request routing, security headers

**Container Specifications:**
- CPU: 0.5 vCPU (512 CPU units)
- Memory: 256 MB
- Ports: 80, 443
- Health Check: GET /health (30s interval, 3 retries)

**Volumes:**
- EFS mount for TLS certificates: `/etc/nginx/ssl` (read-only)

**Auto-Scaling:**
- Min: 2 tasks
- Max: 4 tasks
- Target CPU: 70%

**Note:** In AWS, ALB handles TLS termination, so Nginx may be optional. However, keeping it provides:
- Additional security headers
- Request filtering
- Custom routing logic
- Compatibility with existing configuration

#### 3.1.6 Backup Service
**Purpose:** Automated database backups

**Container Specifications:**
- CPU: 0.5 vCPU (512 CPU units)
- Memory: 512 MB
- Schedule: EventBridge rule (every 6 hours)

**Environment Variables:**
- `MYSQL_HOST`: RDS endpoint
- `MYSQL_USER`: From Secrets Manager
- `MYSQL_PASSWORD`: From Secrets Manager
- `BACKUP_DIR`: /app/backups
- `BACKUP_RETENTION_DAYS`: 7

**Volumes:**
- S3 mount (via EFS or direct S3 upload): `/app/backups`

**Note:** RDS automated backups are preferred. This service provides additional application-level backups.



### 3.2 Data Layer

#### 3.2.1 RDS MySQL 8.0
**Purpose:** Primary database for FIR records

**Configuration:**
- Instance Class: db.t3.medium (2 vCPU, 4 GB RAM)
- Storage: 100 GB GP3 (3000 IOPS, 125 MB/s throughput)
- Multi-AZ: Enabled (for 99.9% availability)
- Automated Backups: Enabled (7-day retention)
- Backup Window: 03:00-04:00 UTC
- Maintenance Window: Sun 04:00-05:00 UTC
- Encryption: Enabled (KMS)
- Performance Insights: Enabled (7-day retention)

**Parameters:**
- `innodb_flush_log_at_trx_commit`: 1 (durability)
- `sync_binlog`: 1 (durability)
- `innodb_doublewrite`: 1 (crash recovery)
- `max_connections`: 150
- `innodb_buffer_pool_size`: 2.5 GB (60% of RAM)

**Security:**
- Security Group: Only allows 3306 from ECS services
- Subnet Group: Private database subnets
- Public Access: Disabled
- IAM Authentication: Enabled

**Cost Estimate:** ~$80-100/month

#### 3.2.2 EFS (Elastic File System)
**Purpose:** Shared storage for ChromaDB, models, and session database

**Configuration:**
- Performance Mode: General Purpose
- Throughput Mode: Bursting
- Encryption: Enabled (at rest and in transit)
- Lifecycle Policy: Transition to IA after 30 days
- Backup: AWS Backup enabled (daily, 7-day retention)

**Mount Targets:**
- One per private subnet (2 total)
- Security Group: Allows 2049 from ECS services

**Directory Structure:**
```
/efs
├── chroma_kb/          # ChromaDB vector database
├── kb/                 # Knowledge base files (BNS sections)
├── models/             # GGUF, Whisper, dots_ocr models
├── sessions/           # sessions.db SQLite file
└── nginx/ssl/          # TLS certificates
```

**Cost Estimate:** ~$30-50/month (depends on usage)

#### 3.2.3 S3 Buckets

**Models Bucket (`afirgen-models-{account-id}`):**
- Purpose: Store large model files
- Versioning: Enabled
- Lifecycle: Transition to Glacier after 90 days
- Encryption: SSE-S3
- Access: Private (ECS tasks via IAM role)
- Cost: ~$20-30/month

**Temp Files Bucket (`afirgen-temp-{account-id}`):**
- Purpose: Temporary audio/image uploads
- Lifecycle: Delete after 1 day
- Encryption: SSE-S3
- Access: Private (ECS tasks via IAM role)
- Cost: ~$5-10/month

**Backups Bucket (`afirgen-backups-{account-id}`):**
- Purpose: Application-level database backups
- Versioning: Enabled
- Lifecycle: Transition to IA after 30 days, Glacier after 90 days
- Encryption: SSE-KMS
- Access: Private (backup service via IAM role)
- Cost: ~$10-15/month

**Logs Bucket (`afirgen-logs-{account-id}`):**
- Purpose: ALB access logs, VPC flow logs
- Lifecycle: Transition to IA after 30 days, delete after 90 days
- Encryption: SSE-S3
- Access: Private (AWS services)
- Cost: ~$5-10/month

### 3.3 Networking Layer

#### 3.3.1 Application Load Balancer
**Purpose:** Distribute traffic, SSL termination, health checks

**Configuration:**
- Scheme: Internet-facing
- IP Address Type: IPv4
- Subnets: Public subnets in 2 AZs
- Security Group: Allows 80/443 from internet
- Deletion Protection: Enabled
- Access Logs: Enabled (S3 bucket)

**Listeners:**
1. HTTP (80): Redirect to HTTPS
2. HTTPS (443): Forward to target groups
   - SSL Policy: ELBSecurityPolicy-TLS-1-2-2017-01
   - Certificate: ACM certificate for afirgen.example.com

**Target Groups:**
- `afirgen-nginx`: Port 443, health check /health
- `afirgen-frontend`: Port 80, health check /
- `afirgen-backend`: Port 8000, health check /health

**Health Check Configuration:**
- Interval: 30s
- Timeout: 5s
- Healthy Threshold: 2
- Unhealthy Threshold: 3

**Cost Estimate:** ~$20-25/month + data transfer

#### 3.3.2 NAT Gateways
**Purpose:** Allow private subnets to access internet (for model downloads, AWS APIs)

**Configuration:**
- One per AZ (2 total)
- Elastic IPs: 2
- Placement: Public subnets

**Cost Estimate:** ~$70-80/month (expensive, consider alternatives)

**Cost Optimization Alternative:**
- Use VPC endpoints for AWS services (S3, Secrets Manager, CloudWatch)
- Only use NAT for external model downloads
- Consider S3 Gateway Endpoint (free) for model storage



### 3.4 Security Layer

#### 3.4.1 AWS Secrets Manager
**Purpose:** Secure storage for sensitive credentials

**Secrets:**
- `afirgen/mysql/credentials`: MySQL username and password
- `afirgen/api/keys`: API_KEY and FIR_AUTH_KEY
- `afirgen/tls/certificates`: TLS private keys (if not using ACM)

**Configuration:**
- Encryption: KMS (customer-managed key)
- Rotation: Enabled (30 days for database credentials)
- Access: IAM roles for ECS tasks

**Cost:** ~$2-3/month

**Implementation:** Already integrated in `main backend/secrets_manager.py`

#### 3.4.2 IAM Roles and Policies

**ECS Task Execution Role:**
- Permissions:
  - Pull images from ECR
  - Write logs to CloudWatch
  - Read secrets from Secrets Manager
  - Access EFS mount targets

**ECS Task Role (Main Backend):**
- Permissions:
  - Read/write S3 (temp files, models)
  - Read Secrets Manager
  - Write CloudWatch metrics
  - X-Ray tracing

**ECS Task Role (Model Servers):**
- Permissions:
  - Read S3 (models)
  - Write CloudWatch metrics
  - X-Ray tracing

**ECS Task Role (Backup Service):**
- Permissions:
  - Read RDS (via network)
  - Write S3 (backups)
  - Read Secrets Manager

**RDS Enhanced Monitoring Role:**
- Permissions:
  - Write CloudWatch metrics

#### 3.4.3 KMS Keys

**RDS Encryption Key:**
- Purpose: Encrypt RDS database
- Rotation: Enabled (annual)
- Alias: `alias/afirgen-rds`

**EFS Encryption Key:**
- Purpose: Encrypt EFS file system
- Rotation: Enabled (annual)
- Alias: `alias/afirgen-efs`

**Secrets Manager Key:**
- Purpose: Encrypt secrets
- Rotation: Enabled (annual)
- Alias: `alias/afirgen-secrets`

**Cost:** ~$3-4/month per key

### 3.5 Observability Layer

#### 3.5.1 CloudWatch Logs
**Purpose:** Centralized logging for all services

**Log Groups:**
- `/ecs/afirgen/main-backend`: Main backend logs
- `/ecs/afirgen/gguf-model-server`: GGUF server logs
- `/ecs/afirgen/asr-ocr-server`: ASR/OCR server logs
- `/ecs/afirgen/frontend`: Frontend logs
- `/ecs/afirgen/nginx`: Nginx logs
- `/ecs/afirgen/backup`: Backup service logs
- `/aws/rds/instance/afirgen-mysql/error`: RDS error logs
- `/aws/rds/instance/afirgen-mysql/slowquery`: RDS slow query logs

**Configuration:**
- Retention: 7 days (cost optimization)
- Encryption: Enabled
- Metric Filters: Error rate, latency, custom metrics

**Cost:** ~$10-15/month

**Implementation:** Already integrated via `json_logging.py`

#### 3.5.2 CloudWatch Metrics
**Purpose:** Performance monitoring and alerting

**Custom Metrics (Already Implemented):**
- `AFIRGen/API/RequestCount`: API request count
- `AFIRGen/API/ResponseTime`: API response time
- `AFIRGen/API/ErrorRate`: API error rate
- `AFIRGen/FIR/GenerationTime`: FIR generation time
- `AFIRGen/FIR/GenerationCount`: FIR generation count
- `AFIRGen/Model/InferenceTime`: Model inference time
- `AFIRGen/Database/QueryTime`: Database query time
- `AFIRGen/Cache/HitRate`: Cache hit rate
- `AFIRGen/RateLimit/Violations`: Rate limit violations
- `AFIRGen/Auth/Failures`: Authentication failures

**AWS Metrics:**
- ECS: CPU, Memory, Network
- RDS: CPU, Connections, IOPS, Latency
- ALB: Request Count, Target Response Time, HTTP Errors
- EFS: Data Read/Write, Throughput

**Cost:** ~$10-15/month

**Implementation:** Already integrated via `cloudwatch_metrics.py`

#### 3.5.3 CloudWatch Dashboards
**Purpose:** Real-time visibility into system health

**Dashboards (Already Implemented):**
1. **Main Dashboard:** Overview of all services
2. **Errors Dashboard:** Error rates and failure analysis
3. **Performance Dashboard:** Latency and throughput metrics

**Cost:** $3/month per dashboard

**Implementation:** Already configured in `terraform/cloudwatch_dashboards.tf`

#### 3.5.4 CloudWatch Alarms
**Purpose:** Proactive alerting for issues

**Alarms (Already Implemented):**
- High error rate (>5%)
- High API response time (>2s)
- High FIR generation time (>35s)
- High database query time (>1s)
- Low cache hit rate (<50%)
- High rate limit violations (>10/min)
- High auth failures (>5/min)
- ECS service unhealthy
- RDS high CPU (>80%)
- RDS low storage (<10%)

**Notification:** SNS topic → Email

**Cost:** $0.10 per alarm per month

**Implementation:** Already configured in `terraform/cloudwatch_alarms.tf`

#### 3.5.5 AWS X-Ray (To Be Implemented)
**Purpose:** Distributed tracing for request flow analysis

**Integration Points:**
- FastAPI middleware
- HTTP client (httpx)
- Database queries (MySQL)
- Model inference calls

**Configuration:**
- Sampling Rate: 10% (cost optimization)
- Trace Retention: 7 days

**Cost:** ~$5-10/month



## 4. Data Models

### 4.1 MySQL Database Schema

#### 4.1.1 FIR Records Table
```sql
CREATE TABLE fir_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fir_number VARCHAR(50) UNIQUE NOT NULL,
    session_id VARCHAR(100) NOT NULL,
    status ENUM('draft', 'validated', 'completed', 'archived') DEFAULT 'draft',
    
    -- Complainant Information
    complainant_name VARCHAR(255),
    date_of_birth DATE,
    nationality VARCHAR(100),
    father_name VARCHAR(255),
    complainant_address TEXT,
    complainant_contact VARCHAR(20),
    passport_number VARCHAR(50),
    occupation VARCHAR(100),
    
    -- Incident Information
    date_from DATE,
    date_to DATE,
    time_from TIME,
    time_to TIME,
    occurrence_place VARCHAR(255),
    occurrence_address TEXT,
    incident_description TEXT,
    delay_reason TEXT,
    summary TEXT,
    
    -- Legal Information
    acts JSON,  -- Array of applicable acts
    sections JSON,  -- Array of applicable sections
    suspect_details TEXT,
    
    -- Investigation Information
    io_name VARCHAR(255),
    io_rank VARCHAR(100),
    witnesses TEXT,
    action_taken TEXT,
    investigation_status VARCHAR(100),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    
    -- Indexes for performance
    INDEX idx_fir_number (fir_number),
    INDEX idx_session_id (session_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### 4.1.2 Validation History Table
```sql
CREATE TABLE validation_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fir_id INT NOT NULL,
    step ENUM('initial', 'user_validation', 'regeneration', 'final') NOT NULL,
    content JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (fir_id) REFERENCES fir_records(id) ON DELETE CASCADE,
    INDEX idx_fir_id (fir_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### 4.2 SQLite Session Database Schema

**File:** `sessions.db` (stored on EFS)

```sql
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    state TEXT NOT NULL,  -- JSON serialized state
    status TEXT NOT NULL,  -- processing, awaiting_validation, completed, expired, error
    created_at TEXT NOT NULL,
    last_activity TEXT NOT NULL,
    validation_history TEXT NOT NULL  -- JSON array
);

-- Enable WAL mode for crash recovery
PRAGMA journal_mode=WAL;
PRAGMA synchronous=FULL;
```

### 4.3 ChromaDB Collections

**Collection:** `bns_knowledge_base`
- Documents: BNS sections and legal clauses
- Metadata: Section number, act name, category
- Embeddings: Generated from document text

**Collection:** `special_acts`
- Documents: Special acts and provisions
- Metadata: Act name, year, category
- Embeddings: Generated from document text

### 4.4 S3 Object Structure

**Models Bucket:**
```
s3://afirgen-models-{account-id}/
├── gguf/
│   ├── summariser.gguf
│   ├── bns_check.gguf
│   └── fir_summariser.gguf
├── whisper/
│   └── whisper-base.pt
└── dots_ocr/
    └── dots_ocr_model.pth
```

**Temp Files Bucket:**
```
s3://afirgen-temp-{account-id}/
├── audio/
│   └── {session_id}_{uuid}.wav
└── images/
    └── {session_id}_{uuid}.jpg
```

**Backups Bucket:**
```
s3://afirgen-backups-{account-id}/
├── mysql/
│   └── {date}/
│       └── fir_db_backup_{timestamp}.sql.gz
└── sessions/
    └── {date}/
        └── sessions_db_backup_{timestamp}.db.gz
```



## 5. Correctness Properties

### 5.1 What Are Correctness Properties?

A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

In this design, we define properties that can be validated through property-based testing, where each property is tested across many randomly generated inputs to ensure it holds universally.

### 5.2 Properties

#### Property 1: Model Loading Error Handling
*For any* model file that is missing, corrupted, or invalid, the system SHALL return a descriptive error message and fail gracefully without crashing, allowing other services to continue operating.

**Validates: Requirements 4.1.4**

**Test Strategy:** Generate various failure scenarios (missing files, corrupted data, invalid formats) and verify that each results in a proper error response rather than a crash.

#### Property 2: CORS Origin Validation
*For any* HTTP request with an Origin header, if the origin is not in the configured allowlist, the system SHALL reject the request with appropriate CORS headers, and if the origin is in the allowlist, the system SHALL accept the request.

**Validates: Requirements 4.1.5**

**Test Strategy:** Generate random origin headers (both valid and invalid) and verify that only configured origins are accepted.


#### Property 3: FIR Generation Performance
*For any* valid FIR generation request with audio, image, or text input, the complete FIR generation process SHALL complete within 30 seconds, including all model inference, database operations, and validation steps.

**Validates: Requirements 4.3.1**

**Test Strategy:** Generate random valid inputs of varying sizes and complexities, measure end-to-end generation time, and verify all complete within 30 seconds.

#### Property 4: Concurrent Request Handling
*For any* set of 10 concurrent valid API requests, the system SHALL successfully process all requests without errors, timeouts, or resource exhaustion, maintaining response time SLAs.

**Validates: Requirements 4.3.2**

**Test Strategy:** Generate 10 concurrent requests with random valid payloads and verify all complete successfully with acceptable response times.

#### Property 5: API Response Time
*For any* non-inference API endpoint (health checks, session management, FIR retrieval), the response time SHALL be under 200ms for the 95th percentile of requests.

**Validates: Requirements 4.3.4**

**Test Strategy:** Generate random requests to various non-inference endpoints, measure response times, and verify P95 is under 200ms.


#### Property 6: Automatic Service Recovery
*For any* service that crashes or becomes unhealthy (failing health checks), the orchestration system (ECS) SHALL automatically restart the service and restore it to a healthy state within 2 minutes.

**Validates: Requirements 4.4.2**

**Test Strategy:** Simulate various failure scenarios (process crashes, health check failures, resource exhaustion) and verify automatic recovery occurs within the time limit.

#### Property 7: Zero Data Loss on Restart
*For any* in-flight database transaction when a service restart occurs, the data SHALL either be fully committed to the database or fully rolled back, with no partial writes or data corruption.

**Validates: Requirements 4.4.4**

**Test Strategy:** Generate random transactions, trigger service restarts at various points during transaction execution, and verify data integrity (no partial writes, no corruption).

#### Property 8: API Authentication Enforcement
*For any* protected API endpoint, requests without valid authentication credentials (API key or bearer token) SHALL be rejected with a 401 Unauthorized response, and requests with valid credentials SHALL be accepted.

**Validates: Requirements 4.5.2**

**Test Strategy:** Generate random requests with and without valid credentials to all protected endpoints and verify authentication is enforced consistently.


#### Property 9: Rate Limiting Enforcement
*For any* IP address making more than 100 requests within a 60-second window, subsequent requests SHALL be rejected with a 429 Too Many Requests response until the window resets.

**Validates: Requirements 4.5.3**

**Test Strategy:** Generate request bursts from random IP addresses exceeding the rate limit and verify 429 responses are returned appropriately.

#### Property 10: Input Validation
*For any* API endpoint, malicious or invalid inputs (XSS payloads, SQL injection attempts, oversized payloads, invalid data types) SHALL be rejected with a 400 Bad Request response before reaching business logic.

**Validates: Requirements 4.5.4**

**Test Strategy:** Generate various malicious and invalid inputs for all endpoints and verify they are rejected with appropriate error messages.

#### Property 11: Structured JSON Logging
*For any* log entry generated by the system, the log SHALL be valid JSON containing required fields (timestamp, level, message, service, request_id) and SHALL be parseable by CloudWatch Logs Insights.

**Validates: Requirements 4.6.1**

**Test Strategy:** Capture log entries from various operations, parse them as JSON, and verify all required fields are present and valid.



## 6. Error Handling

### 6.1 Error Handling Strategy

AFIRGen implements a comprehensive error handling strategy with multiple layers of defense:

1. **Input Validation Layer:** Reject invalid inputs before they reach business logic
2. **Business Logic Layer:** Handle expected errors gracefully with meaningful messages
3. **Infrastructure Layer:** Automatic recovery from transient failures
4. **Monitoring Layer:** Alert on unexpected errors for investigation

### 6.2 Error Categories and Responses

#### 6.2.1 Client Errors (4xx)

**400 Bad Request:**
- Invalid input format
- Missing required fields
- Validation failures (XSS, SQL injection, size limits)
- Response includes specific validation error details

**401 Unauthorized:**
- Missing authentication credentials
- Invalid API key or bearer token
- Expired tokens
- Response includes WWW-Authenticate header

**403 Forbidden:**
- Valid authentication but insufficient permissions
- Access to archived or deleted resources
- Response includes reason for denial


**404 Not Found:**
- Resource does not exist (FIR, session)
- Invalid endpoint
- Response includes resource type and identifier

**429 Too Many Requests:**
- Rate limit exceeded
- Response includes Retry-After header
- Response includes current rate limit status

#### 6.2.2 Server Errors (5xx)

**500 Internal Server Error:**
- Unexpected application errors
- Unhandled exceptions
- Response includes error ID for tracking
- Detailed error logged but not exposed to client

**502 Bad Gateway:**
- Downstream service (GGUF, ASR/OCR) unavailable
- Model inference timeout
- Response includes which service failed

**503 Service Unavailable:**
- Service starting up (models loading)
- Service shutting down gracefully
- Database connection pool exhausted
- Response includes Retry-After header

**504 Gateway Timeout:**
- Request exceeded 30-second timeout
- Model inference taking too long
- Response includes timeout duration


### 6.3 Retry and Circuit Breaker Patterns

#### 6.3.1 Retry Policy
**Applies to:** Calls to downstream services (GGUF, ASR/OCR), database queries, S3 operations

**Configuration:**
- Max retries: 3
- Backoff strategy: Exponential (1s, 2s, 4s)
- Retry on: Connection errors, timeouts, 502/503 responses
- Do not retry on: 4xx errors (except 429), 500 errors

**Implementation:**
```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=4),
    retry=retry_if_exception_type((ConnectionError, TimeoutError))
)
async def call_model_service(payload):
    # Service call implementation
    pass
```

#### 6.3.2 Circuit Breaker Pattern
**Applies to:** Calls to model inference services (GGUF, ASR/OCR)

**Configuration:**
- Failure threshold: 5 consecutive failures
- Timeout: 30 seconds
- Recovery timeout: 60 seconds (half-open state)
- Success threshold to close: 2 consecutive successes

**States:**
- **Closed:** Normal operation, requests pass through
- **Open:** Service is failing, requests fail fast without calling service
- **Half-Open:** Testing if service recovered, limited requests pass through


**Implementation:**
```python
from pybreaker import CircuitBreaker

model_service_breaker = CircuitBreaker(
    fail_max=5,
    timeout_duration=60,
    expected_exception=ServiceUnavailableError
)

@model_service_breaker
async def call_gguf_service(payload):
    # GGUF service call implementation
    pass
```

### 6.4 Graceful Degradation

When downstream services are unavailable, the system provides degraded functionality:

**GGUF Model Server Unavailable:**
- Return cached summaries if available
- Provide basic text extraction without summarization
- Inform user that advanced features are temporarily unavailable

**ASR/OCR Server Unavailable:**
- Accept text-only input
- Queue audio/image processing for later
- Inform user of processing delay

**ChromaDB Unavailable:**
- Use fallback rule-based section matching
- Reduced accuracy but functional
- Log degraded mode for monitoring

**MySQL Database Unavailable:**
- Return 503 Service Unavailable
- Do not accept new FIR submissions
- Health check reports unhealthy
- ECS will restart the service


### 6.5 Error Logging and Monitoring

**Structured Error Logging:**
All errors are logged in JSON format with:
- `timestamp`: ISO 8601 format
- `level`: ERROR or CRITICAL
- `message`: Human-readable error description
- `error_type`: Exception class name
- `error_id`: Unique identifier for tracking
- `request_id`: Correlation ID for request tracing
- `service`: Service name (main-backend, gguf-server, etc.)
- `stack_trace`: Full stack trace (for 500 errors)
- `context`: Additional context (user_id, session_id, etc.)

**Error Metrics:**
- `AFIRGen/Errors/Count`: Total error count by service and error type
- `AFIRGen/Errors/Rate`: Error rate as percentage of total requests
- `AFIRGen/Errors/4xx`: Client error count by endpoint
- `AFIRGen/Errors/5xx`: Server error count by endpoint

**Error Alerts:**
- Error rate >5%: Page on-call engineer
- Critical errors (data loss, security): Immediate alert
- Service unavailable >5 minutes: Alert DevOps team
- Database connection failures: Immediate alert

### 6.6 Error Recovery Procedures

**Automatic Recovery:**
- ECS health checks detect unhealthy containers
- Unhealthy containers are stopped and replaced
- New containers start with fresh state
- Load balancer routes traffic only to healthy containers

**Manual Recovery:**
- CloudWatch alarms notify on-call engineer
- Runbooks provide step-by-step recovery procedures
- Rollback capability via ECS task definition versions
- Database backups available for data recovery



## 7. Testing Strategy

### 7.1 Testing Philosophy

AFIRGen employs a comprehensive testing strategy with two complementary approaches:

1. **Unit Tests:** Verify specific examples, edge cases, and error conditions
2. **Property-Based Tests:** Verify universal properties across many randomly generated inputs

Both approaches are necessary for comprehensive coverage. Unit tests catch concrete bugs and document expected behavior, while property-based tests discover edge cases that humans might miss.

### 7.2 Property-Based Testing

#### 7.2.1 Framework Selection
**Python:** Hypothesis (https://hypothesis.readthedocs.io/)
- Mature, well-maintained library
- Excellent integration with pytest
- Smart test case generation and shrinking
- Built-in strategies for common data types

#### 7.2.2 Configuration
Each property-based test MUST:
- Run minimum 100 iterations (configured via `@settings(max_examples=100)`)
- Include a comment tag referencing the design property
- Tag format: `# Feature: afirgen-aws-optimization, Property N: [property text]`
- Use appropriate Hypothesis strategies for input generation


#### 7.2.3 Property Test Examples

**Property 1: Model Loading Error Handling**
```python
from hypothesis import given, strategies as st, settings

# Feature: afirgen-aws-optimization, Property 1: Model Loading Error Handling
@settings(max_examples=100)
@given(
    model_path=st.one_of(
        st.just("nonexistent.gguf"),  # Missing file
        st.just("corrupted.gguf"),     # Corrupted file
        st.just("invalid.txt")          # Invalid format
    )
)
def test_model_loading_error_handling(model_path):
    """For any invalid model file, system returns error without crashing"""
    result = load_model(model_path)
    assert result.is_error()
    assert result.error_message is not None
    assert "model" in result.error_message.lower()
```

**Property 8: API Authentication Enforcement**
```python
# Feature: afirgen-aws-optimization, Property 8: API Authentication Enforcement
@settings(max_examples=100)
@given(
    endpoint=st.sampled_from([
        "/generate_fir", "/validate_fir", "/get_fir", 
        "/update_fir", "/delete_fir", "/list_firs"
    ]),
    has_auth=st.booleans(),
    auth_value=st.text(min_size=10, max_size=50)
)
async def test_api_authentication_enforcement(endpoint, has_auth, auth_value):
    """For any protected endpoint, authentication is enforced"""
    headers = {"X-API-Key": auth_value} if has_auth else {}
    response = await client.get(endpoint, headers=headers)
    
    if has_auth and auth_value == VALID_API_KEY:
        assert response.status_code != 401
    else:
        assert response.status_code == 401
```


**Property 10: Input Validation**
```python
# Feature: afirgen-aws-optimization, Property 10: Input Validation
@settings(max_examples=100)
@given(
    malicious_input=st.one_of(
        st.just("<script>alert('xss')</script>"),  # XSS
        st.just("'; DROP TABLE fir_records; --"),   # SQL injection
        st.text(min_size=10000000),                 # Oversized payload
        st.just("../../../etc/passwd")              # Path traversal
    ),
    endpoint=st.sampled_from([
        "/generate_fir", "/validate_fir", "/update_fir"
    ])
)
async def test_input_validation(malicious_input, endpoint):
    """For any malicious input, system rejects with 400"""
    payload = {"description": malicious_input}
    response = await client.post(endpoint, json=payload, headers=auth_headers)
    assert response.status_code == 400
    assert "validation" in response.json()["detail"].lower()
```

### 7.3 Unit Testing

#### 7.3.1 Test Organization
```
tests/
├── unit/
│   ├── test_api_endpoints.py
│   ├── test_authentication.py
│   ├── test_rate_limiting.py
│   ├── test_input_validation.py
│   ├── test_model_loading.py
│   ├── test_database_operations.py
│   └── test_error_handling.py
├── integration/
│   ├── test_fir_generation_flow.py
│   ├── test_service_communication.py
│   └── test_database_integration.py
├── property/
│   ├── test_properties_security.py
│   ├── test_properties_performance.py
│   └── test_properties_reliability.py
└── infrastructure/
    ├── test_terraform_validation.py
    └── test_docker_configuration.py
```


#### 7.3.2 Unit Test Coverage Requirements

**Minimum Coverage Targets:**
- Overall code coverage: 80%
- Critical paths (FIR generation, authentication): 95%
- Error handling paths: 90%
- Configuration and utilities: 70%

**Key Unit Test Areas:**

1. **API Endpoints:**
   - Test each endpoint with valid inputs
   - Test error responses (400, 401, 404, 500)
   - Test edge cases (empty strings, null values, boundary values)

2. **Authentication:**
   - Valid API key acceptance
   - Invalid API key rejection
   - Missing authentication rejection
   - Bearer token support

3. **Rate Limiting:**
   - Requests within limit accepted
   - Requests exceeding limit rejected with 429
   - Rate limit window reset behavior
   - Per-IP tracking accuracy

4. **Input Validation:**
   - XSS payload rejection
   - SQL injection payload rejection
   - Oversized payload rejection
   - Invalid data type rejection
   - File upload validation (type, size, extension)

5. **Model Loading:**
   - Successful model loading from EFS
   - Model download from S3 on first run
   - Error handling for missing models
   - Error handling for corrupted models


6. **Database Operations:**
   - CRUD operations for FIR records
   - Transaction rollback on errors
   - Connection pool management
   - Query performance (under 200ms)

7. **Error Handling:**
   - Proper error responses for each error type
   - Error logging with correct format
   - Circuit breaker state transitions
   - Retry logic with exponential backoff

### 7.4 Integration Testing

#### 7.4.1 Service Integration Tests

**FIR Generation Flow:**
1. Create session
2. Upload audio file → ASR processing
3. Upload image → OCR processing
4. Generate FIR → GGUF summarization
5. Validate FIR → ChromaDB lookup
6. Retrieve completed FIR

**Test Scenarios:**
- Happy path: All services available
- ASR service unavailable: Fallback to text input
- GGUF service unavailable: Use cached summaries
- Database unavailable: Return 503
- Concurrent requests: 10 simultaneous FIR generations

#### 7.4.2 Database Integration Tests

**MySQL Integration:**
- Connection establishment
- Transaction commit/rollback
- Concurrent access handling
- Backup and restore procedures
- Migration scripts execution

**ChromaDB Integration:**
- Vector search accuracy
- Collection persistence
- Query performance
- Concurrent access handling


### 7.5 Performance Testing

#### 7.5.1 Load Testing

**Tool:** Locust (https://locust.io/)

**Test Scenarios:**
1. **Baseline Load:** 10 concurrent users, 1 hour duration
2. **Peak Load:** 50 concurrent users, 30 minutes duration
3. **Stress Test:** Gradually increase to 100 users, find breaking point
4. **Spike Test:** Sudden increase from 10 to 50 users

**Metrics to Measure:**
- Response time (P50, P95, P99)
- Throughput (requests per second)
- Error rate
- Resource utilization (CPU, memory, network)

**Acceptance Criteria:**
- P95 response time <30s for FIR generation
- P95 response time <200ms for API endpoints
- Error rate <1% under normal load
- System handles 10 concurrent FIR generations

#### 7.5.2 Endurance Testing

**Duration:** 24 hours continuous operation

**Objectives:**
- Detect memory leaks
- Verify log rotation works
- Confirm database connection pool stability
- Validate auto-scaling behavior

**Monitoring:**
- Memory usage over time
- Database connection count
- ECS task count
- Error rate trends


### 7.6 Security Testing

#### 7.6.1 OWASP Top 10 Testing

**Automated Tools:**
- OWASP ZAP for vulnerability scanning
- Bandit for Python code security analysis
- Safety for dependency vulnerability checking

**Manual Testing:**
1. **Injection:** SQL injection, command injection, XSS
2. **Broken Authentication:** Brute force, credential stuffing
3. **Sensitive Data Exposure:** Check for exposed secrets, PII
4. **XML External Entities:** Not applicable (no XML processing)
5. **Broken Access Control:** Test authorization on all endpoints
6. **Security Misconfiguration:** Review security headers, CORS
7. **XSS:** Test all input fields with XSS payloads
8. **Insecure Deserialization:** Test JSON parsing with malicious payloads
9. **Using Components with Known Vulnerabilities:** Dependency scanning
10. **Insufficient Logging & Monitoring:** Verify all security events logged

#### 7.6.2 Penetration Testing

**Scope:**
- External penetration test of production environment
- Internal penetration test of AWS infrastructure
- Social engineering test (phishing simulation)

**Frequency:** Annually or after major changes

### 7.7 Infrastructure Testing

#### 7.7.1 Terraform Validation

**Pre-deployment Checks:**
```bash
terraform fmt -check      # Code formatting
terraform validate        # Syntax validation
tflint                    # Linting
terraform plan           # Preview changes
checkov -d terraform/    # Security scanning
```

**Post-deployment Verification:**
- All resources created successfully
- Security groups configured correctly
- IAM roles have least privilege
- Encryption enabled on all data stores
- Backups configured and tested


#### 7.7.2 Docker Configuration Testing

**Validation:**
- All volume mounts exist and are accessible
- Environment variables properly set
- Health checks return 200 OK
- Resource limits enforced
- Networks configured correctly

**Test Commands:**
```bash
docker-compose config --quiet  # Validate syntax
docker-compose up -d           # Start services
docker-compose ps              # Check status
docker-compose logs            # Check logs
docker-compose exec main-backend curl http://localhost:8000/health
```

### 7.8 Disaster Recovery Testing

#### 7.8.1 Backup and Restore Testing

**Quarterly Tests:**
1. Trigger manual RDS snapshot
2. Restore snapshot to new RDS instance
3. Verify data integrity
4. Test application connectivity to restored database
5. Document restore time

**Application-Level Backups:**
1. Trigger backup service manually
2. Download backup from S3
3. Restore to test database
4. Verify data integrity
5. Document restore procedure

#### 7.8.2 Failover Testing

**Multi-AZ RDS Failover:**
1. Trigger manual failover
2. Monitor application behavior
3. Verify no data loss
4. Measure downtime
5. Document failover time

**ECS Service Failure:**
1. Stop all tasks in a service
2. Verify ECS starts new tasks
3. Verify ALB routes traffic to healthy tasks
4. Measure recovery time
5. Verify no request failures


### 7.9 Continuous Integration Testing

#### 7.9.1 CI Pipeline (GitHub Actions)

**On Pull Request:**
1. Run unit tests (pytest)
2. Run property-based tests (Hypothesis)
3. Check code coverage (>80%)
4. Run linting (flake8, black, mypy)
5. Run security scanning (bandit, safety)
6. Validate Terraform (terraform validate, tflint)
7. Build Docker images
8. Run integration tests

**On Merge to Main:**
1. All PR checks
2. Build and push Docker images to ECR
3. Deploy to staging environment
4. Run smoke tests
5. Run performance tests
6. Generate deployment report

**On Release Tag:**
1. All main branch checks
2. Deploy to production
3. Run smoke tests
4. Monitor for 1 hour
5. Send deployment notification

#### 7.9.2 Test Execution Time Targets

- Unit tests: <2 minutes
- Property-based tests: <5 minutes
- Integration tests: <10 minutes
- Full CI pipeline: <20 minutes

### 7.10 Monitoring and Alerting Validation

**Test Scenarios:**
1. Trigger high error rate → Verify alarm fires
2. Simulate slow response times → Verify alarm fires
3. Stop database → Verify health check fails and alarm fires
4. Exceed rate limit → Verify metric recorded and alarm fires
5. Generate authentication failures → Verify metric recorded

**Validation:**
- All alarms fire within 5 minutes of condition
- SNS notifications delivered successfully
- CloudWatch dashboards display correct data
- Logs are searchable in CloudWatch Logs Insights



## 8. Implementation Approach

### 8.1 Phased Deployment Strategy

#### Phase 1: Bug Fixes and Local Testing (Days 1-3)
**Objective:** Fix all identified bugs and validate locally

**Tasks:**
- Fix Docker path mismatches
- Add missing volume mounts
- Implement model loading error handling
- Configure CORS for specific origins
- Add frontend environment configuration
- Test all fixes locally with docker-compose

**Validation:** All services start successfully, no errors in logs

#### Phase 2: AWS Infrastructure Setup (Days 4-8)
**Objective:** Deploy core AWS infrastructure

**Tasks:**
- Create VPC, subnets, security groups
- Set up RDS MySQL with Multi-AZ
- Create S3 buckets with lifecycle policies
- Set up EFS for shared storage
- Configure ALB with SSL certificate
- Create IAM roles and policies
- Deploy VPC endpoints

**Validation:** Infrastructure deployed, terraform plan shows no changes

#### Phase 3: Application Deployment (Days 9-12)
**Objective:** Deploy application to ECS

**Tasks:**
- Build and push Docker images to ECR
- Create ECS task definitions
- Deploy ECS services
- Configure auto-scaling policies
- Upload models to S3 and EFS
- Run database migrations
- Configure CloudWatch logging

**Validation:** All services healthy, accessible via ALB


#### Phase 4: Observability and Monitoring (Days 13-15)
**Objective:** Implement comprehensive monitoring

**Tasks:**
- Configure CloudWatch dashboards
- Set up CloudWatch alarms
- Implement AWS X-Ray tracing
- Configure SNS notifications
- Set up cost monitoring
- Create runbooks for common issues

**Validation:** All metrics flowing, alarms tested and working

#### Phase 5: Testing and Optimization (Days 16-20)
**Objective:** Validate performance and reliability

**Tasks:**
- Run load tests (10 concurrent users)
- Run stress tests (find breaking point)
- Run endurance tests (24 hours)
- Optimize based on results
- Run security scans
- Fix any issues found

**Validation:** All performance targets met, no security issues

#### Phase 6: Documentation and Handoff (Days 21-23)
**Objective:** Complete documentation

**Tasks:**
- Write deployment guide
- Write operations runbook
- Write troubleshooting guide
- Document architecture decisions
- Create cost optimization guide
- Train team on operations

**Validation:** Team can deploy and operate system independently

### 8.2 Rollback Strategy

**Automated Rollback Triggers:**
- Error rate >10% for 5 minutes
- P95 response time >60s for 5 minutes
- Health check failures >50% for 2 minutes

**Rollback Procedure:**
1. Revert ECS task definitions to previous version
2. Update ECS services to use previous task definition
3. Wait for new tasks to become healthy
4. Verify error rate returns to normal
5. Investigate root cause

**Rollback Time Target:** <5 minutes


### 8.3 Model Management Strategy

#### 8.3.1 Model Storage and Distribution

**S3 Bucket Structure:**
```
s3://afirgen-models-{account-id}/
├── gguf/
│   ├── v1.0/
│   │   ├── summariser.gguf
│   │   ├── bns_check.gguf
│   │   └── fir_summariser.gguf
│   └── latest/  # Symlinks to current version
├── whisper/
│   └── v1.0/
│       └── whisper-base.pt
└── dots_ocr/
    └── v1.0/
        └── dots_ocr_model.pth
```

**Model Loading Process:**
1. Container starts, checks EFS for models
2. If models exist and version matches, load from EFS
3. If models missing or version mismatch, download from S3
4. Copy models to EFS for persistence
5. Load models into memory
6. Mark service as healthy

**Version Management:**
- Models tagged with version numbers
- ECS task definition includes model version as environment variable
- Deployment updates model version, triggers download
- Old model versions retained in S3 for rollback

#### 8.3.2 Model Caching Strategy

**EFS Caching:**
- Models persist on EFS across container restarts
- Reduces cold start time from 2 minutes to 30 seconds
- Shared across all tasks in a service
- Cost: ~$30/month for 50GB of models

**Memory Caching:**
- Models loaded into memory on startup
- Use mlock to prevent swapping
- Use mmap for efficient memory usage
- Models remain in memory for container lifetime


### 8.4 Database Migration Strategy

#### 8.4.1 Migration Tool: Alembic

**Setup:**
```bash
pip install alembic
alembic init alembic
```

**Configuration:**
```python
# alembic/env.py
from main_backend.database import Base
target_metadata = Base.metadata
```

**Migration Workflow:**
1. Create migration: `alembic revision --autogenerate -m "description"`
2. Review migration script
3. Test migration on staging database
4. Apply to production: `alembic upgrade head`
5. Verify data integrity

#### 8.4.2 Zero-Downtime Migration

**Strategy:**
1. Deploy new code that supports both old and new schema
2. Run migration to add new columns/tables
3. Backfill data if needed
4. Deploy code that uses new schema
5. Remove old columns/tables in next migration

**Example: Adding a new column**
```python
# Migration 1: Add column with default value
op.add_column('fir_records', sa.Column('priority', sa.String(20), 
              nullable=False, server_default='normal'))

# Migration 2 (later): Remove default after backfill
op.alter_column('fir_records', 'priority', server_default=None)
```

### 8.5 Cost Optimization Strategy

#### 8.5.1 Compute Optimization

**ECS Fargate Spot:**
- Use Spot instances for non-critical services (backup, batch jobs)
- 70% cost savings compared to on-demand
- Automatic fallback to on-demand if Spot unavailable

**Right-Sizing:**
- Monitor actual CPU/memory usage
- Adjust task definitions based on metrics
- Use smaller instances for low-traffic periods

**Auto-Scaling:**
- Scale down to minimum during off-hours
- Scale up based on actual load
- Use target tracking for automatic adjustment


#### 8.5.2 Storage Optimization

**S3 Lifecycle Policies:**
- Temp files: Delete after 1 day
- Models: Transition to Glacier after 90 days (rarely change)
- Backups: Transition to IA after 30 days, Glacier after 90 days
- Logs: Transition to IA after 30 days, delete after 90 days

**EFS Lifecycle Management:**
- Transition to IA after 30 days of no access
- 90% cost savings for infrequently accessed files
- Models accessed frequently stay in standard storage

**RDS Storage:**
- Use GP3 instead of GP2 (20% cheaper)
- Enable storage auto-scaling (only pay for what you use)
- Regular cleanup of old validation history

#### 8.5.3 Network Optimization

**VPC Endpoints:**
- Use S3 Gateway Endpoint (free) instead of NAT for S3 access
- Use Interface Endpoints for Secrets Manager, CloudWatch
- Saves ~$70/month in NAT Gateway costs

**Data Transfer:**
- Keep traffic within same AZ when possible
- Use CloudFront for static assets (if needed)
- Compress responses to reduce transfer costs

#### 8.5.4 Monitoring Optimization

**CloudWatch Logs:**
- 7-day retention (vs 30 days) saves 75%
- Use metric filters instead of storing all logs
- Export old logs to S3 for long-term storage

**CloudWatch Metrics:**
- Use 1-minute resolution only for critical metrics
- Use 5-minute resolution for others
- Reduces costs by 80%

**Estimated Monthly Costs:**
- ECS Fargate: $150-200
- RDS MySQL: $80-100
- EFS: $30-50
- S3: $40-60
- ALB: $20-25
- CloudWatch: $20-30
- Secrets Manager: $2-3
- VPC Endpoints: $15-20
- Data Transfer: $20-30
- **Total: $377-518/month** ✅ Under $500 target


### 8.6 Security Implementation Details

#### 8.6.1 Secrets Rotation

**Automated Rotation (AWS Secrets Manager):**
- Database credentials: 30-day rotation
- API keys: 90-day rotation
- TLS certificates: Auto-renewal via ACM

**Rotation Process:**
1. Secrets Manager creates new secret version
2. Lambda function updates database password
3. ECS tasks automatically fetch new secret
4. Old secret version retained for 7 days
5. Old version deleted after grace period

#### 8.6.2 Network Security

**Security Group Rules (Least Privilege):**
- ALB: Only 80/443 from internet
- ECS Services: Only from ALB or other services
- RDS: Only 3306 from ECS services
- EFS: Only 2049 from ECS services
- No direct internet access for private resources

**Network ACLs:**
- Default allow for VPC traffic
- Deny known malicious IPs (updated via Lambda)
- Log all denied traffic

**VPC Flow Logs:**
- Capture all network traffic
- Store in S3 for analysis
- Use Athena for querying
- Alert on suspicious patterns

#### 8.6.3 Application Security

**Input Sanitization:**
- HTML escaping for all user inputs
- SQL parameterization (no string concatenation)
- File upload validation (type, size, content)
- JSON schema validation

**Output Encoding:**
- Proper content-type headers
- JSON encoding for API responses
- HTML encoding for web pages
- Prevent MIME sniffing

**Security Headers:**
```
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
```


### 8.7 Operational Procedures

#### 8.7.1 Deployment Procedure

**Pre-Deployment Checklist:**
- [ ] All tests passing in CI
- [ ] Code review approved
- [ ] Terraform plan reviewed
- [ ] Database migrations tested in staging
- [ ] Rollback plan documented
- [ ] On-call engineer notified

**Deployment Steps:**
1. Create deployment tag: `git tag v1.2.3`
2. Push tag: `git push origin v1.2.3`
3. CI builds and pushes Docker images
4. Run database migrations: `alembic upgrade head`
5. Update ECS task definitions with new image tags
6. Update ECS services (rolling deployment)
7. Monitor CloudWatch dashboards for 30 minutes
8. Run smoke tests
9. Announce deployment complete

**Post-Deployment Validation:**
- [ ] All services healthy
- [ ] Error rate <1%
- [ ] Response times within SLA
- [ ] No increase in 5xx errors
- [ ] Database connections stable

#### 8.7.2 Incident Response

**Severity Levels:**
- **P0 (Critical):** Service down, data loss, security breach
- **P1 (High):** Degraded performance, partial outage
- **P2 (Medium):** Non-critical feature broken
- **P3 (Low):** Minor issue, cosmetic bug

**Response Times:**
- P0: Immediate response, 15-minute acknowledgment
- P1: 30-minute response, 1-hour acknowledgment
- P2: 4-hour response, same-day acknowledgment
- P3: Next business day response

**Incident Workflow:**
1. Alert fires → On-call engineer paged
2. Acknowledge alert in PagerDuty
3. Assess severity and impact
4. Follow runbook for known issues
5. Escalate if needed
6. Implement fix or rollback
7. Verify resolution
8. Write post-mortem (P0/P1 only)


#### 8.7.3 Runbooks

**Common Issues and Solutions:**

**Issue: High Error Rate**
1. Check CloudWatch dashboard for error breakdown
2. Check logs for stack traces: `aws logs tail /ecs/afirgen/main-backend --follow`
3. If database connection errors: Check RDS status, connection pool
4. If model service errors: Check GGUF/ASR-OCR service health
5. If rate limiting: Check for DDoS, adjust limits if legitimate traffic
6. Rollback if recent deployment: `aws ecs update-service --task-definition previous-version`

**Issue: Slow Response Times**
1. Check CloudWatch metrics for bottleneck (database, model inference)
2. Check ECS CPU/memory utilization
3. Check RDS performance insights
4. Scale up if resource constrained: Increase task count or instance size
5. Check for slow queries in RDS slow query log
6. Clear caches if stale data causing issues

**Issue: Service Won't Start**
1. Check ECS task logs: `aws ecs describe-tasks --tasks <task-arn>`
2. Common causes: Model download failure, database connection failure, missing secrets
3. Verify secrets exist: `aws secretsmanager get-secret-value --secret-id afirgen/mysql/credentials`
4. Verify EFS mounted: Check ECS task definition volume configuration
5. Verify IAM permissions: Check task execution role and task role

**Issue: Database Connection Failures**
1. Check RDS status: `aws rds describe-db-instances --db-instance-identifier afirgen-mysql`
2. Check security group rules: Verify ECS can reach RDS on port 3306
3. Check connection pool: May be exhausted, restart service or increase max_connections
4. Check credentials: Verify secrets are correct and not rotated without update

### 8.8 Success Criteria

**Technical Success:**
- ✅ All 11 correctness properties pass property-based tests (100+ iterations each)
- ✅ Unit test coverage >80%
- ✅ All security scans pass (no high/critical vulnerabilities)
- ✅ Performance targets met (P95 <30s FIR generation, <200ms API)
- ✅ Infrastructure deployed successfully via Terraform
- ✅ All services healthy and accessible via HTTPS

**Operational Success:**
- ✅ Zero-downtime deployment achieved
- ✅ Rollback tested and working (<5 minutes)
- ✅ Monitoring and alerting functional
- ✅ Team trained on operations
- ✅ Documentation complete and accurate

**Business Success:**
- ✅ AWS costs <$500/month
- ✅ 99.9% uptime achieved in first month
- ✅ No security incidents
- ✅ User satisfaction maintained or improved
