# AFIRGen Setup Guide

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- At least 8GB RAM available
- 10GB free disk space for models

### 1. Environment Configuration

Copy the example environment file and configure it:

```bash
cd "AFIRGEN FINAL"
cp .env.example .env
```

Edit `.env` and set your values:

```bash
# MySQL Database Configuration
MYSQL_HOST=mysql
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your-secure-password-here
MYSQL_DB=fir_db

# Application Configuration
PORT=8000
FIR_AUTH_KEY=your-secure-auth-key-here

# Model Server Configuration
MODEL_SERVER_PORT=8001
ASR_OCR_PORT=8002
```

**Important:** Change the default passwords before deploying!

### 2. Database Setup

The MySQL database will be automatically initialized when you start the services. The application will:
- Create the `fir_records` table automatically
- Set up connection pooling
- Configure character encoding (utf8mb4)

No manual database setup is required!

### 3. Model Files

Download the required model files and place them in the `models/` directory:

- GGUF models for LLM inference
- Whisper model for ASR
- Donut OCR model

See `models/MODELS.MD` for download links and instructions.

### 4. Knowledge Base Setup

Ensure the following files are in the correct locations:

**RAG Database** (`rag db/`):
- `BNS_basic_chroma.jsonl`
- `BNS_details_chroma.jsonl`
- `BNS_spacts_chroma.jsonl`

**General Retrieval** (`general retrieval db/`):
- `BNS_basic.jsonl`
- `BNS_indepth.jsonl`
- `spacts.jsonl`

### 5. Frontend Configuration

The frontend API URL is configurable for different environments:

**For Development (default):**
No configuration needed - uses `http://localhost:8000`

**For Production:**
Set the API URL in `.env`:
```bash
API_BASE_URL=https://api.afirgen.com
ENVIRONMENT=production
ENABLE_DEBUG=false
FRONTEND_PORT=80
```

**Alternative Methods:**
- Use deployment script: `./frontend/deploy-config.sh production`
- Edit `frontend/config.js` directly
- See `FRONTEND-DEPLOYMENT-GUIDE.md` for detailed instructions

### 6. Start Services

Start all services using Docker Compose:

```bash
docker-compose up -d
```

This will start:
- MySQL database (port 3306)
- Main backend (port 8000)
- GGUF model server (port 8001)
- ASR/OCR server (port 8002)
- Frontend (port 80)

### 6. Verify Installation

Check service health:

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "model_server": {"status": "healthy"},
  "asr_ocr_server": {"status": "healthy"},
  "database": "connected",
  "kb_collections": 3,
  "session_persistence": "sqlite"
}
```

### 7. Access the Application

Open your browser and navigate to:
- **Frontend:** http://localhost (or the port specified in FRONTEND_PORT)
- **Configuration Test:** http://localhost/test-config.html
- **API Documentation:** http://localhost:8000/docs
- **View FIR Records:** http://localhost:8000/view_fir_records

**Note:** The frontend automatically connects to the API URL configured in `config.js`

## Database Management

### View Database

Connect to MySQL:

```bash
docker exec -it <mysql-container-id> mysql -u root -p
```

View FIR records:

```sql
USE fir_db;
SELECT * FROM fir_records;
```

### Backup Database

```bash
docker exec <mysql-container-id> mysqldump -u root -p fir_db > backup.sql
```

### Restore Database

```bash
docker exec -i <mysql-container-id> mysql -u root -p fir_db < backup.sql
```

## Troubleshooting

### MySQL Connection Issues

**Problem:** Application can't connect to MySQL

**Solution:**
1. Check MySQL container is running: `docker ps`
2. View MySQL logs: `docker logs <mysql-container-id>`
3. Verify environment variables in `.env`
4. Wait for MySQL health check to pass (may take 30-60 seconds on first start)

### Port Conflicts

**Problem:** Port already in use

**Solution:**
1. Check what's using the port: `netstat -ano | findstr :8000` (Windows)
2. Stop the conflicting service or change the port in `.env`
3. Restart Docker Compose

### Model Loading Errors

**Problem:** Models not found

**Solution:**
1. Verify model files are in the correct directories
2. Check file permissions
3. Ensure sufficient disk space
4. Review model server logs: `docker logs <model-server-container-id>`

### Memory Issues

**Problem:** Out of memory errors

**Solution:**
1. Increase Docker memory limit (Docker Desktop settings)
2. Close other applications
3. Use smaller model variants
4. Reduce connection pool size in configuration

## Development Mode

For local development without Docker:

1. Install MySQL 8.0 locally
2. Create database: `CREATE DATABASE fir_db;`
3. Update `.env` with `MYSQL_HOST=localhost`
4. Install Python dependencies: `pip install -r requirements.txt`
5. Run services individually:
   ```bash
   # Terminal 1 - Main backend
   cd "main backend"
   python agentv5.py
   
   # Terminal 2 - GGUF server
   cd "gguf model server"
   python llm_server.py
   
   # Terminal 3 - ASR/OCR server
   cd "asr ocr model server"
   python asr_ocr.py
   ```

## Production Deployment

For production deployment to AWS, see:
- `.kiro/specs/afirgen-aws-optimization/requirements.md`
- `.kiro/specs/afirgen-aws-optimization/design.md`

Key considerations:
- Use AWS RDS for MySQL instead of Docker container
- Store models in S3
- Use ECS/EKS for container orchestration
- Enable CloudWatch logging and monitoring
- Configure auto-scaling
- Use AWS Secrets Manager for credentials

## Support

For issues and questions:
1. Check the logs: `docker-compose logs`
2. Review `DATABASE.md` for database-specific issues
3. Consult the design documents in the repository
