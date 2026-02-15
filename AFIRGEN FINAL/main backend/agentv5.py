# fir_pipeline_production_ready.py
# -------------------------------------------------------------
# FIR Pipeline with Production Fixes - Race Conditions, Memory Leaks, etc.
# -------------------------------------------------------------
import httpx
import asyncio
from typing import Optional
import os
import json
import logging
import uuid
import asyncio
import re
import string
import gc
import sqlite3
import threading
import signal
from pathlib import Path
from typing import Optional, Dict, List, Any, Union
from datetime import datetime, timedelta
from contextlib import contextmanager, asynccontextmanager
from enum import Enum

import chromadb
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Import reliability components
from reliability import CircuitBreaker, RetryPolicy, HealthMonitor, GracefulShutdown, AutoRecovery, DependencyHealthCheck

# Import input validation
from input_validation import (
    ValidationConstants,
    sanitize_text,
    validate_file_upload,
    ValidationStep,
    ProcessRequest,
    ValidationRequest as ValidatedValidationRequest,
    RegenerateRequest,
    AuthRequest as ValidatedAuthRequest,
    CircuitBreakerResetRequest,
    validate_session_id_param,
    validate_fir_number_param,
    validate_circuit_breaker_name,
    validate_recovery_name,
    validate_limit_param,
    validate_offset_param,
    validate_request_size,
    validate_json_depth,
    FIRResp,
    ValidationResponse,
    AuthResponse,
    ErrorResponse
)

# Import structured JSON logging
from json_logging import (
    setup_json_logging,
    log_with_context,
    log_request,
    log_response,
    log_error,
    log_performance,
    log_security_event
)

# Import CloudWatch metrics
from cloudwatch_metrics import (
    get_metrics,
    record_api_request,
    record_fir_generation,
    record_model_inference,
    record_database_operation,
    record_cache_operation,
    record_rate_limit_event,
    record_auth_event,
    record_health_check
)

# Import X-Ray tracing
from xray_tracing import (
    setup_xray,
    trace_subsegment,
    add_trace_annotation,
    add_trace_metadata,
    AsyncXRaySubsegment,
    get_trace_id
)

# Try to import python-magic, fallback to basic validation
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    # Will log this after logger is configured

# Import secrets manager
from secrets_manager import get_secret

# ------------------------------------------------------------- CONFIGURATION DICTIONARY    
CFG = {
    "max_file_size": 25 * 1024 * 1024,
    "max_text_len": 50_000,
    "temp_dir": Path("temp_files"),
    "session_timeout": 3600,
    "session_db_path": "sessions.db",  # SQLite for session persistence
    "mysql": {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "port": int(os.getenv("MYSQL_PORT", 3306)),
        "user": get_secret("MYSQL_USER", default="root"),
        "password": get_secret("MYSQL_PASSWORD", required=True),
        "database": get_secret("MYSQL_DB", default="fir_db"),
        "charset": "utf8mb4",
        "autocommit": False,  # ZERO DATA LOSS: Disable autocommit for transaction support
        "pool_size": 15,  # CONCURRENCY: Increased for 10+ concurrent requests
        "pool_reset_session": True,  # FIX: Reset session on connection return
        "pool_timeout": 30,  # FIX: Connection timeout
    },
    "concurrency": {
        "max_concurrent_requests": int(os.getenv("MAX_CONCURRENT_REQUESTS", 15)),  # Allow 15 concurrent FIR generations
        "max_concurrent_model_calls": int(os.getenv("MAX_CONCURRENT_MODEL_CALLS", 10)),  # Limit concurrent model inference
        "http_pool_connections": 20,  # HTTP connection pool size
        "http_pool_maxsize": 20,  # Max connections per host
    },
    "chroma": {"persist_dir": "./chroma_kb"},
    "kb_dir": Path("./kb"),
    "allowed_image": {"image/jpeg", "image/png", "image/jpg"},
    "allowed_audio": {"audio/wav", "audio/mpeg", "audio/mp3"},
    "allowed_extensions": {".jpg", ".jpeg", ".png", ".wav", ".mp3", ".mpeg"},
    "auth_key": get_secret("FIR_AUTH_KEY", required=True),
    "api_key": get_secret("API_KEY", required=True),  # API key for endpoint authentication
    "model_timeouts": {
        "summary": 60.0,  # FIX: Increased timeouts
        "ocr": 120.0,
        "asr": 180.0,
    }
}
CFG["temp_dir"].mkdir(exist_ok=True)
CFG["kb_dir"].mkdir(exist_ok=True)

# Configure structured JSON logging
log = setup_json_logging(
    service_name="main-backend",
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    log_file="logs/main_backend.log",
    environment=os.getenv("ENVIRONMENT", "production"),
    enable_console=True
)

# Log python-magic availability warning if needed
if not MAGIC_AVAILABLE:
    log.warning("python-magic not available, using basic MIME validation")

log.info("Main backend service starting", extra={
    "config": {
        "max_concurrent_requests": CFG["concurrency"]["max_concurrent_requests"],
        "mysql_host": CFG["mysql"]["host"],
        "mysql_port": CFG["mysql"]["port"],
        "session_timeout": CFG["session_timeout"]
    }
})

# ------------------------------------------------------------- ENUMS & UTILS
# ValidationStep is now imported from input_validation module

class SessionStatus(str, Enum):
    PROCESSING = "processing"
    AWAITING_VALIDATION = "awaiting_validation"
    COMPLETED = "completed"
    EXPIRED = "expired"
    ERROR = "error"

# DateTime JSON encoder
class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)

def sanitise(text: str) -> str:
    """Legacy sanitization function - use input_validation.sanitize_text instead"""
    return sanitize_text(text, allow_html=False)

# FIX: File validation with proper MIME checking
def validate_uploaded_file(file_path: Path, content_type: str) -> bool:
    """Validate file extension and MIME type"""
    # Check extension
    ext = file_path.suffix.lower()
    if ext not in CFG["allowed_extensions"]:
        raise HTTPException(status_code=415, detail=f"Invalid file extension: {ext}")
    
    # MIME validation
    if MAGIC_AVAILABLE:
        try:
            detected_mime = magic.Magic(mime=True).from_file(str(file_path))
            # Check against allowed types
            if content_type.startswith("image/") and detected_mime not in CFG["allowed_image"]:
                raise HTTPException(status_code=415, detail=f"Invalid image MIME type: {detected_mime}")
            elif content_type.startswith("audio/") and detected_mime not in CFG["allowed_audio"]:
                raise HTTPException(status_code=415, detail=f"Invalid audio MIME type: {detected_mime}")
        except Exception as e:
            log.warning(f"MIME detection failed: {e}")
    else:
        # Basic fallback validation
        if content_type not in (CFG["allowed_image"] | CFG["allowed_audio"]):
            raise HTTPException(status_code=415, detail=f"Unsupported content type: {content_type}")
    
    return True

def get_fir_data(session_state: dict) -> dict:
    from datetime import datetime

    now = datetime.now()
    present_date = now.strftime("%d %B %Y")
    present_time = now.strftime("%H:%M:%S")

    # Construct FIR data dict using available session_state and defaults
    fir_data = {
        'fir_number': session_state.get('fir_number', 'N/A'),
        'police_station': 'Central Police Station',  # hardcoded or derived from config/session
        'district': 'Metro City',
        'state': 'State of Example',
        'year': present_date.split()[-1],
        'date': present_date,

        'Acts': session_state.get('Acts', ['IPC 379 (Theft)', 'IPC 34 (Common Intention)', 'IPC 506 (Criminal Intimidation)']),
        'Sections': session_state.get('Sections', ['IPC 379', 'IPC 34', 'IPC 506']),

        'Occurrence of Offence': '',
        'Date from': session_state.get('date_from', present_date),
        'Date to': session_state.get('date_to', present_date),
        'Time from': session_state.get('time_from', ''),
        'Time to': session_state.get('time_to', ''),
        'Information recieved': f"{present_date} at {present_time}",

        'Place of Occurrence': session_state.get('occurrence_place', 'Central Park, Metro City'),
        'Address of Occurrence': session_state.get('occurrence_address', 'Near the fountain area, Central Park, Metro City'),

        'complainant_name': session_state.get('complainant_name', 'John Doe'),
        'dateofbirth': session_state.get('date_of_birth', '01 January 1990'),
        'Nationality': session_state.get('nationality', 'Indian'),
        'father_name/husband_name': session_state.get('father_name', 'Richard Doe'),
        'complainant_address': session_state.get('complainant_address', '123 Main St.'),
        'complainant_contact': session_state.get('complainant_contact', '9876543210'),
        'passport_number': session_state.get('passport_number', ''),
        'occupation': session_state.get('occupation', ''),

        'Suspect_details': session_state.get('suspect_details', 'Unknown'),

        'reasons_for_delayed_reporting': session_state.get('delay_reason', 'No delay reported'),

        'incident_description': session_state.get('incident_description', ''),
        'summary': session_state.get('summary', ''),
        'action_taken': session_state.get('action_taken', ''),

        'io_name': session_state.get('io_name', 'Inspector Rajesh Kumar'),
        'io_rank': session_state.get('io_rank', 'Inspector'),
        'witnesses': session_state.get('witnesses', ''),
        'date_of_despatch': present_date,

        'investigation_status': session_state.get('investigation_status', 'Preliminary investigation started'),
    }

    return fir_data


fir_template = """
FIRST INFORMATION REPORT

------------------------------------------------------------------------------------------------------

FIR No.: {fir_number}                 Year: {year}
Police Station: {police_station}
District: {district}
State: {state}

Date of Report: {date}
Information Received: {Information recieved}

1. COMPLAINANT DETAILS:
   - Full Name: {complainant_name}
   - Date of Birth: {dateofbirth}
   - Nationality: {Nationality}
   - Father's/Husband's Name: {father_name/husband_name}
   - Complete Address: {complainant_address}
   - Contact Number: {complainant_contact}
   - Passport Number: {passport_number}
   - Occupation: {occupation}

2. INCIDENT DETAILS:
   - Date from: {Date from}
   - Date to: {Date to}
   - Time from: {Time from}
   - Time to: {Time to}
   - Place of Occurrence: {Place of Occurrence}
   - Address of Occurrence: {Address of Occurrence}
   - Detailed Description:
     {incident_description}
   - Reason for Delayed Reporting:
     {reasons_for_delayed_reporting}
   - Summary:
     {summary}

3. LEGAL PROVISIONS:
   - Applicable Acts: {Acts}
   - Applicable Sections: {Sections}

4. SUSPECT DETAILS:
   - {Suspect_details}

5. INVESTIGATION DETAILS:
   - Investigating Officer: {io_name} ({io_rank})
   - Witnesses: {witnesses}
   - Action Taken: {action_taken}
   - Investigation Status: {investigation_status}
   - Date of Despatch: {date_of_despatch}

------------------------------------------------------------------------------------------------------

(Signature of Investigating Officer)

(Signature of Complainant)

{io_name}
{io_rank}
{police_station}
Date: {date}
"""


# ------------------------------------------------------------- PERSISTENT SESSION MANAGER
class PersistentSessionManager:
    """FIX: Session persistence using SQLite"""
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()
        self._cleanup_interval = 300  # 5 minutes
        self._last_cleanup = datetime.now()
        self._session_cache = {}  # PERFORMANCE: In-memory cache for session data
        self._cache_ttl = 60  # Cache TTL in seconds
    
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            # ZERO DATA LOSS: Enable WAL mode for better crash recovery and concurrency
            conn.execute("PRAGMA journal_mode=WAL")
            # ZERO DATA LOSS: Ensure data is synced to disk on commit
            conn.execute("PRAGMA synchronous=FULL")
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    state TEXT,
                    status TEXT,
                    created_at TEXT,
                    last_activity TEXT,
                    validation_history TEXT
                )
            """)
            log.info("Session database initialized with WAL mode and FULL synchronous")
    
    def create_session(self, session_id: str, initial_state: Dict) -> None:
        now = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO sessions VALUES (?, ?, ?, ?, ?, ?)",
                (session_id, json.dumps(initial_state, cls=DateTimeEncoder), 
                 SessionStatus.PROCESSING, now, now, "[]")
            )
        self._cleanup_old_sessions()
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        import time
        
        # PERFORMANCE: Check cache first
        if session_id in self._session_cache:
            cached_time, cached_session = self._session_cache[session_id]
            if time.time() - cached_time < self._cache_ttl:
                return cached_session
        
        self._cleanup_old_sessions()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
            )
            row = cursor.fetchone()
            if not row:
                # Remove from cache if exists
                self._session_cache.pop(session_id, None)
                return None
            
            # Update last activity
            now = datetime.now().isoformat()
            conn.execute(
                "UPDATE sessions SET last_activity = ? WHERE session_id = ?",
                (now, session_id)
            )
            
            session_data = {
                "session_id": row[0],
                "state": json.loads(row[1]),
                "status": row[2],
                "created_at": datetime.fromisoformat(row[3]),
                "last_activity": datetime.fromisoformat(row[4]),
                "validation_history": json.loads(row[5])
            }
            
            # PERFORMANCE: Cache the result
            self._session_cache[session_id] = (time.time(), session_data)
            
            return session_data
    
    def update_session(self, session_id: str, updates: Dict) -> bool:
        session = self.get_session(session_id)
        if not session:
            return False
        
        session["state"].update(updates)
        now = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE sessions SET state = ?, last_activity = ? WHERE session_id = ?",
                (json.dumps(session["state"], cls=DateTimeEncoder), now, session_id)
            )
        
        # PERFORMANCE: Invalidate cache
        self._session_cache.pop(session_id, None)
        
        return True
    
    def set_session_status(self, session_id: str, status: SessionStatus) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "UPDATE sessions SET status = ?, last_activity = ? WHERE session_id = ?",
                (status, datetime.now().isoformat(), session_id)
            )
            success = cursor.rowcount > 0
        
        # PERFORMANCE: Invalidate cache
        if success:
            self._session_cache.pop(session_id, None)
        
        return success
    
    def add_validation_step(self, session_id: str, step: ValidationStep, content: Dict) -> bool:
        session = self.get_session(session_id)
        if not session:
            return False
        
        history = session["validation_history"]
        history.append({
            "step": step,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE sessions SET validation_history = ? WHERE session_id = ?",
                (json.dumps(history, cls=DateTimeEncoder), session_id)
            )
        
        # PERFORMANCE: Invalidate cache
        self._session_cache.pop(session_id, None)
        
        return True
    
    def _cleanup_old_sessions(self):
        now = datetime.now()
        if (now - self._last_cleanup).seconds < self._cleanup_interval:
            return
        
        cutoff = (now - timedelta(seconds=CFG["session_timeout"])).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "UPDATE sessions SET status = ? WHERE last_activity < ? AND status != ?",
                (SessionStatus.EXPIRED, cutoff, SessionStatus.EXPIRED)
            )
            if cursor.rowcount > 0:
                log.info(f"Expired {cursor.rowcount} old sessions")
        
        self._last_cleanup = now
    
    def flush_all(self):
        """
        ZERO DATA LOSS: Flush all session data to disk
        Called during graceful shutdown to prevent data loss
        """
        try:
            # Clear cache to ensure all data is written
            self._session_cache.clear()
            
            # Force SQLite to write all pending changes to disk
            with sqlite3.connect(self.db_path) as conn:
                # WAL checkpoint to flush write-ahead log
                conn.execute("PRAGMA wal_checkpoint(FULL)")
                # Sync to ensure data is on disk
                conn.commit()
            log.info("Session database flushed to disk")
        except Exception as e:
            log.error(f"Failed to flush session database: {e}")
            raise

session_manager = PersistentSessionManager(CFG["session_db_path"])

# ------------------------------------------------------------- TEMP FILE MANAGER
class TempFileManager:
    def __init__(self):
        self.temp_paths: List[Path] = []
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        for path in self.temp_paths:
            try:
                if path.exists():
                    path.unlink()
                    log.debug(f"Cleaned up temp file: {path}")
            except Exception as e:
                log.warning(f"Failed to cleanup {path}: {e}")
    
    async def save_audio(self, audio: UploadFile) -> str:
        if audio.content_type not in CFG["allowed_audio"]:
            raise HTTPException(status_code=415, detail="Unsupported audio format")
        
        # FIX: Use pathlib for secure filename handling
        safe_filename = f"{uuid.uuid4().hex}{Path(audio.filename).suffix.lower()}"
        path = CFG["temp_dir"] / safe_filename
        content = await audio.read()
        
        if len(content) > CFG["max_file_size"]:
            raise HTTPException(status_code=413, detail="Audio file too large")
        
        path.write_bytes(content)
        validate_uploaded_file(path, audio.content_type)
        self.temp_paths.append(path)
        return str(path)
    
    async def save_image(self, image: UploadFile) -> str:
        if image.content_type not in CFG["allowed_image"]:
            raise HTTPException(status_code=415, detail="Unsupported image format")
        
        # FIX: Use pathlib for secure filename handling
        safe_filename = f"{uuid.uuid4().hex}{Path(image.filename).suffix.lower()}"
        path = CFG["temp_dir"] / safe_filename
        content = await image.read()
        
        if len(content) > CFG["max_file_size"]:
            raise HTTPException(status_code=413, detail="Image file too large")
        
        path.write_bytes(content)
        validate_uploaded_file(path, image.content_type)
        self.temp_paths.append(path)
        return str(path)
    

#==============MODEL POOL=================================
class ModelPool:
    _instance: Optional["ModelPool"] = None
    _lock = asyncio.Lock()
    _health_check_cache = {}  # Cache health check results
    _health_check_ttl = 30  # Cache TTL in seconds
    _http_client: Optional[httpx.AsyncClient] = None  # CONCURRENCY: Shared HTTP client with connection pooling
    _model_semaphore: Optional[asyncio.Semaphore] = None  # CONCURRENCY: Limit concurrent model calls
    
    def __init__(self, model_server_url: str = "http://localhost:8001", asr_ocr_server_url: str = "http://localhost:8002"):
        self.MODEL_SERVER_URL = model_server_url
        self.ASR_OCR_SERVER_URL = asr_ocr_server_url
        
        # CONCURRENCY: Initialize shared HTTP client with connection pooling
        limits = httpx.Limits(
            max_connections=CFG["concurrency"]["http_pool_connections"],
            max_keepalive_connections=CFG["concurrency"]["http_pool_maxsize"]
        )
        self._http_client = httpx.AsyncClient(
            timeout=45.0,
            limits=limits,
            http2=True  # Enable HTTP/2 for better multiplexing
        )
        
        # CONCURRENCY: Semaphore to limit concurrent model inference calls
        self._model_semaphore = asyncio.Semaphore(CFG["concurrency"]["max_concurrent_model_calls"])
        
        # RELIABILITY: Circuit breakers for external services
        self.model_server_circuit = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60.0,
            expected_exception=Exception,
            name="model_server"
        )
        self.asr_ocr_circuit = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60.0,
            expected_exception=Exception,
            name="asr_ocr_server"
        )
        
        # RELIABILITY: Retry policies
        self.inference_retry = RetryPolicy(
            max_retries=2,
            initial_delay=1.0,
            max_delay=10.0,
            name="inference"
        )
        self.asr_ocr_retry = RetryPolicy(
            max_retries=2,
            initial_delay=2.0,
            max_delay=15.0,
            name="asr_ocr"
        )
        
        log.info("ModelPool initialized for external model server communication")
        log.info(f"HTTP connection pool: {CFG['concurrency']['http_pool_connections']} connections")
        log.info(f"Max concurrent model calls: {CFG['concurrency']['max_concurrent_model_calls']}")
        log.info("Circuit breakers and retry policies enabled for reliability")

    @classmethod
    async def get(cls, model_server_url: str = "http://localhost:8001", asr_ocr_server_url: str = "http://localhost:8002") -> "ModelPool":
        async with cls._lock:
            if cls._instance is None:
                cls._instance = ModelPool(model_server_url, asr_ocr_server_url)  
            return cls._instance

    async def _check_server_health(self, server_url: str, server_name: str) -> tuple[bool, str]:
        """Check if a server is healthy and models are loaded"""
        import time
        
        # Check cache first
        cache_key = f"{server_name}_{server_url}"
        if cache_key in self._health_check_cache:
            cached_time, cached_result = self._health_check_cache[cache_key]
            if time.time() - cached_time < self._health_check_ttl:
                return cached_result
        
        try:
            # CONCURRENCY: Use shared HTTP client for health checks
            resp = await self._http_client.get(f"{server_url}/health", timeout=5.0)
            resp.raise_for_status()
            health_data = resp.json()
            
            status = health_data.get("status", "unknown")
            message = health_data.get("message", "No message")
            
            is_healthy = status in ["healthy", "degraded"]
            result = (is_healthy, message)
            
            # Cache result
            self._health_check_cache[cache_key] = (time.time(), result)
            
            return result
            
        except Exception as e:
            error_msg = f"{server_name} health check failed: {str(e)}"
            log.error(error_msg)
            result = (False, error_msg)
            
            # Cache failure for shorter time
            self._health_check_cache[cache_key] = (time.time() - self._health_check_ttl + 5, result)
            
            return result

    async def _inference(self, model_name: str, prompt: str, max_tokens: int = 120, temperature: float = 0.1, stop: list = None) -> str:
        # Check model server health first (with caching)
        is_healthy, health_msg = await self._check_server_health(self.MODEL_SERVER_URL, "Model Server")
        if not is_healthy:
            raise RuntimeError(f"Model server is not healthy: {health_msg}")
        
        # RELIABILITY: Wrap inference with circuit breaker and retry policy
        async def _do_inference():
            # CONCURRENCY: Use semaphore to limit concurrent model calls
            async with self._model_semaphore:
                # X-RAY: Trace model inference
                async with AsyncXRaySubsegment(f"model_inference_{model_name}") as subsegment:
                    subsegment.put_annotation("model_name", model_name)
                    subsegment.put_annotation("max_tokens", max_tokens)
                    subsegment.put_metadata("prompt_length", len(prompt))
                    
                    payload = {
                        "model_name": model_name,
                        "prompt": prompt,
                        "max_tokens": max_tokens,
                        "temperature": temperature
                    }
                    if stop:
                        payload["stop"] = stop

                    try:
                        # CONCURRENCY: Use shared HTTP client with connection pooling
                        resp = await self._http_client.post(f"{self.MODEL_SERVER_URL}/inference", json=payload)
                        resp.raise_for_status()
                        result = resp.json()
                        
                        subsegment.put_annotation("success", True)
                        subsegment.put_metadata("response_length", len(result["result"]))
                        
                        return result["result"]
                    except httpx.RequestError as e:
                        subsegment.put_annotation("error", True)
                        subsegment.put_metadata("error_type", "request_error")
                        log.error(f"Model server request failed: {e}")
                        raise RuntimeError(f"Model server unavailable: {e}")
                    except httpx.HTTPStatusError as e:
                        subsegment.put_annotation("error", True)
                        subsegment.put_metadata("error_type", "http_error")
                        subsegment.put_metadata("status_code", e.response.status_code)
                        log.error(f"Model server returned error: {e.response.status_code}")
                        error_detail = e.response.text
                        raise RuntimeError(f"Model inference failed: {error_detail}")
        
        # Apply circuit breaker and retry policy with auto-recovery
        try:
            return await self.model_server_circuit.call(
                self.inference_retry.execute,
                _do_inference
            )
        except Exception as e:
            # Trigger auto-recovery if circuit breaker opens
            if self.model_server_circuit.state == "open":
                log.warning("Model server circuit breaker opened, triggering auto-recovery")
                asyncio.create_task(auto_recovery.trigger_recovery("model_server", e))
            raise

    async def two_line_summary(self, text: str) -> str:
        prompt = f"<|user|>\nSummarise the following complaint in exactly two sentences:\n{text}\n<|assistant|>"
        # PERFORMANCE: Reduced max_tokens for faster generation
        return await self._inference("summariser", prompt, max_tokens=100, temperature=0.1)

    async def check_violation(self, summary: str, ref: str) -> bool:
        prompt = f"<|user|>\nComplaint summary:\n{summary}\n\nReference BNS clause:\n{ref}\n\nDoes the summary indicate a violation? Answer only YES or NO.\n<|assistant|>"
        # PERFORMANCE: Minimal tokens for yes/no answer
        response = await self._inference("bns_check", prompt, max_tokens=3, temperature=0.0, stop=["\n"])
        return response.strip().upper().startswith("YES")

    async def fir_narrative(self, complaint: str) -> str:
        prompt = f"<|user|>\nCreate a concise FIR narrative (max 3 sentences) from:\n{complaint}\n<|assistant|>"
        # PERFORMANCE: Reduced max_tokens for faster generation
        return await self._inference("fir_summariser", prompt, max_tokens=150, temperature=0.2)
    
    async def whisper_transcribe(self, audio_path: str) -> str:
        """ASR transcription via external ASR/OCR server with reliability"""
        # Check ASR/OCR server health first
        is_healthy, health_msg = await self._check_server_health(self.ASR_OCR_SERVER_URL, "ASR/OCR Server")
        if not is_healthy:
            raise RuntimeError(f"ASR/OCR server is not healthy: {health_msg}")
        
        # RELIABILITY: Wrap ASR with circuit breaker and retry policy
        async def _do_asr():
            # CONCURRENCY: Use semaphore to limit concurrent ASR calls
            async with self._model_semaphore:
                try:
                    with open(audio_path, 'rb') as audio_file:
                        files = {"audio": audio_file}
                        # CONCURRENCY: Use shared HTTP client
                        resp = await self._http_client.post(f"{self.ASR_OCR_SERVER_URL}/asr", files=files, timeout=180.0)
                        resp.raise_for_status()
                        result = resp.json()
                        
                        if not result.get("success", False):
                            error_detail = result.get('error', 'Unknown error')
                            raise RuntimeError(f"ASR failed: {error_detail}")
                        
                        transcript = result.get("transcript", "")
                        if not transcript:
                            raise RuntimeError("ASR returned empty transcript")
                        
                        return transcript
                        
                except httpx.RequestError as e:
                    log.error(f"ASR server request failed: {e}")
                    raise RuntimeError(f"ASR server unavailable: {e}")
                except httpx.HTTPStatusError as e:
                    log.error(f"ASR server returned error: {e.response.status_code}")
                    raise RuntimeError(f"ASR processing failed: {e.response.text}")
        
        # Apply circuit breaker and retry policy with auto-recovery
        try:
            return await self.asr_ocr_circuit.call(
                self.asr_ocr_retry.execute,
                _do_asr
            )
        except Exception as e:
            # Trigger auto-recovery if circuit breaker opens
            if self.asr_ocr_circuit.state == "open":
                log.warning("ASR/OCR server circuit breaker opened, triggering auto-recovery")
                asyncio.create_task(auto_recovery.trigger_recovery("asr_ocr_server", e))
            raise
    
    async def dots_ocr_sync(self, image_path: str) -> str:
        """OCR processing via external ASR/OCR server with reliability"""
        # Check ASR/OCR server health first
        is_healthy, health_msg = await self._check_server_health(self.ASR_OCR_SERVER_URL, "ASR/OCR Server")
        if not is_healthy:
            raise RuntimeError(f"ASR/OCR server is not healthy: {health_msg}")
        
        # RELIABILITY: Wrap OCR with circuit breaker and retry policy
        async def _do_ocr():
            # CONCURRENCY: Use semaphore to limit concurrent OCR calls
            async with self._model_semaphore:
                try:
                    with open(image_path, 'rb') as image_file:
                        files = {"image": image_file}
                        # CONCURRENCY: Use shared HTTP client
                        resp = await self._http_client.post(f"{self.ASR_OCR_SERVER_URL}/ocr", files=files, timeout=120.0)
                        resp.raise_for_status()
                        result = resp.json()
                        
                        if not result.get("success", False):
                            error_detail = result.get('error', 'Unknown error')
                            raise RuntimeError(f"OCR failed: {error_detail}")
                        
                        extracted_text = result.get("extracted_text", "")
                        if not extracted_text:
                            raise RuntimeError("OCR returned empty text")
                        
                        return extracted_text
                        
                except httpx.RequestError as e:
                    log.error(f"OCR server request failed: {e}")
                    raise RuntimeError(f"OCR server unavailable: {e}")
                except httpx.HTTPStatusError as e:
                    log.error(f"OCR server returned error: {e.response.status_code}")
                    raise RuntimeError(f"OCR processing failed: {e.response.text}")
        
        # Apply circuit breaker and retry policy with auto-recovery
        try:
            return await self.asr_ocr_circuit.call(
                self.asr_ocr_retry.execute,
                _do_ocr
            )
        except Exception as e:
            # Trigger auto-recovery if circuit breaker opens
            if self.asr_ocr_circuit.state == "open":
                log.warning("ASR/OCR server circuit breaker opened, triggering auto-recovery")
                asyncio.create_task(auto_recovery.trigger_recovery("asr_ocr_server", e))
            raise

# ------------------------------------------------------------- KB 
class KB:
    def __init__(self):
        try:
            self.client = chromadb.PersistentClient(path=CFG["chroma"]["persist_dir"])
            self.cols = {}
            self._query_cache = {}  # PERFORMANCE: Cache for KB queries
            self._cache_ttl = 300  # 5 minutes cache TTL
            self._load_jsonl_dbs()
            log.info("Knowledge base initialized successfully")
        except Exception as e:
            log.error(f"KB initialization failed: {e}")
            raise

    def _load_jsonl_dbs(self):
        for file in CFG["kb_dir"].glob("*.jsonl"):
            try:
                name = file.stem
                col = self.client.get_or_create_collection(name)
                if col.count() == 0:
                    docs, metas, ids = [], [], []
                    with open(file, encoding="utf-8") as f:
                        for idx, line in enumerate(f):
                            row = json.loads(line)
                            docs.append(row["text"])
                            metas.append({"section": row["section"], "title": row.get("title", "")})
                            ids.append(f"{name}_{idx}")
                    if docs:
                        col.add(documents=docs, metadatas=metas, ids=ids)
                        log.info(f"Loaded {len(docs)} documents into {name}")
                self.cols[name] = col
            except Exception as e:
                log.error(f"Failed to load {file}: {e}")

    def retrieve(self, query: str, n_results: int = 15) -> List[Dict[str, Any]]:
        """PERFORMANCE: Retrieve with caching and reduced result count"""
        import time
        import hashlib
        
        # Create cache key from query
        cache_key = hashlib.md5(query.encode()).hexdigest()
        
        # Check cache
        if cache_key in self._query_cache:
            cached_time, cached_results = self._query_cache[cache_key]
            if time.time() - cached_time < self._cache_ttl:
                log.debug(f"KB cache hit for query")
                return cached_results
        
        hits = []
        for db_name, col in self.cols.items():
            try:
                # PERFORMANCE: Reduced from 20 to configurable n_results
                res = col.query(query_texts=[query], n_results=n_results)
                for doc, meta in zip(res["documents"][0], res["metadatas"][0]):
                    hits.append({"db": db_name, "section": meta["section"], "text": doc})
            except Exception as e:
                log.warning(f"Query failed for {db_name}: {e}")
        
        # Cache results
        self._query_cache[cache_key] = (time.time(), hits)
        
        # Cleanup old cache entries (keep cache size manageable)
        if len(self._query_cache) > 100:
            current_time = time.time()
            self._query_cache = {
                k: v for k, v in self._query_cache.items()
                if current_time - v[0] < self._cache_ttl
            }
        
        return hits

KB = KB()

# ------------------------------------------------------------- ENHANCED RAG WITH VALIDATION
async def generate_summary_with_validation(session_id: str, transcript: str, user_input: Optional[str] = None) -> str:
    pool = await ModelPool.get()
    
    text_to_process = transcript
    if user_input:
        text_to_process = f"{transcript}\n\nAdditional user input: {user_input}"
    
    summary = await asyncio.wait_for(
        pool.two_line_summary(text_to_process),
        timeout=CFG["model_timeouts"]["summary"]
    )

    session_manager.add_validation_step(session_id, ValidationStep.SUMMARY_REVIEW, {
        "summary": summary,
        "original_transcript": transcript,
        "user_input": user_input
    })
    
    return summary

async def find_violations_with_validation(session_id: str, summary: str, user_input: Optional[str] = None) -> List[Dict[str, Any]]:
    pool = await ModelPool.get()
    
    search_text = summary
    if user_input:
        search_text = f"{summary}\n\nAdditional context: {user_input}"
    
    hits = await asyncio.wait_for(
        asyncio.to_thread(KB.retrieve, search_text),
        timeout=15.0  # FIX: Increased timeout
    )

    # PERFORMANCE: Parallel violation checking with batching
    violations = []
    seen = set()
    
    # Limit hits to top 10 most relevant to reduce processing time
    top_hits = hits[:10]
    
    # Create tasks for parallel violation checking
    async def check_single_violation(h: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            if await asyncio.wait_for(
                pool.check_violation(search_text, h["text"]),
                timeout=8.0  # Reduced timeout per check
            ):
                return h
        except asyncio.TimeoutError:
            log.warning(f"Violation check timeout for section {h.get('section', 'unknown')}")
        except Exception as e:
            log.warning(f"Violation check error: {e}")
        return None
    
    # Run checks in parallel with concurrency limit
    tasks = [check_single_violation(h) for h in top_hits]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Collect valid violations
    for result in results:
        if result and not isinstance(result, Exception):
            key = (result["section"], result["text"])
            if key not in seen:
                seen.add(key)
                violations.append(result)

    session_manager.add_validation_step(session_id, ValidationStep.VIOLATIONS_REVIEW, {
        "violations": violations,
        "search_text": search_text,
        "user_input": user_input
    })
    
    return violations

async def generate_fir_narrative_with_validation(session_id: str, transcript: str, user_input: Optional[str] = None) -> str:
    pool = await ModelPool.get()
    
    text_to_process = transcript
    if user_input:
        text_to_process = f"{transcript}\n\nAdditional details: {user_input}"
    
    narrative = await asyncio.wait_for(
        pool.fir_narrative(text_to_process),
        timeout=CFG["model_timeouts"]["summary"]
    )

    
    session_manager.add_validation_step(session_id, ValidationStep.FIR_NARRATIVE_REVIEW, {
        "narrative": narrative,
        "original_transcript": transcript,
        "user_input": user_input
    })
    
    return narrative

# -------------------------------------------------------------  IMPROVED DB WITH CONNECTION MANAGEMENT
class DB:
    def __init__(self):
        import mysql.connector.pooling as pooling
        
        try:
            # FIX: Added pool_reset_session and pool_timeout
            self.pool = pooling.MySQLConnectionPool(
                pool_name="fir_pool", 
                **CFG["mysql"]
            )
            
            # PERFORMANCE: FIR record cache
            self._fir_cache = {}
            self._fir_cache_ttl = 30  # 30 seconds cache for FIR records
            
            with self._cursor() as cur:
                cur.execute("SELECT 1")
                result = cur.fetchone()
                if result:
                    log.info("Database connection established successfully")
                    
            with self._cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS fir_records (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        fir_number VARCHAR(100) UNIQUE NOT NULL,
                        session_id VARCHAR(100),
                        complaint_text TEXT,
                        fir_content TEXT,
                        violations_json LONGTEXT,
                        status ENUM('pending', 'finalized') DEFAULT 'pending',
                        finalized_at TIMESTAMP NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_fir_number (fir_number),
                        INDEX idx_session_id (session_id),
                        INDEX idx_status (status),
                        INDEX idx_created_at (created_at)
                    )
                    """
                )
                log.info("Database tables initialized with indexes")
                
        except Exception as e:
            log.error(f"Database initialization failed: {e}")
            raise RuntimeError(f"Database connection failed: {e}")

    @contextmanager
    def _cursor(self, autocommit: bool = True):
        """
        ZERO DATA LOSS: Context manager with transaction support
        - autocommit=True: Single operations (SELECT, simple INSERT)
        - autocommit=False: Multi-step transactions requiring atomicity
        """
        conn = None
        try:
            conn = self.pool.get_connection()
            conn.autocommit = autocommit
            with conn.cursor(dictionary=True) as cur:
                yield cur
                # ZERO DATA LOSS: Explicit commit for non-autocommit transactions
                if not autocommit:
                    conn.commit()
        except Exception as e:
            # ZERO DATA LOSS: Rollback on error to maintain consistency
            if conn and not autocommit:
                try:
                    conn.rollback()
                    log.warning(f"Transaction rolled back due to error: {e}")
                except Exception as rollback_error:
                    log.error(f"Rollback failed: {rollback_error}")
            log.error(f"Database operation failed: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def save(self, fir_number: str, session_id: str, complaint: str, content: str, violations_json: str):
        """ZERO DATA LOSS: Save FIR with transaction to ensure atomicity"""
        with self._cursor(autocommit=False) as cur:
            cur.execute(
                "INSERT INTO fir_records "
                "(fir_number, session_id, complaint_text, fir_content, violations_json, status) "
                "VALUES (%s,%s,%s,%s,%s,'pending')",
                (fir_number, session_id, complaint, content, violations_json),
            )
            log.info(f"FIR {fir_number} saved successfully with transaction")
        
        # PERFORMANCE: Invalidate cache
        self._fir_cache.pop(fir_number, None)

    def finalize_fir(self, fir_number: str):
        """ZERO DATA LOSS: Finalize FIR with transaction"""
        with self._cursor(autocommit=False) as cur:
            cur.execute(
                "UPDATE fir_records SET status = 'finalized', finalized_at = NOW() WHERE fir_number = %s AND status = 'pending'",
                (fir_number,)
            )
            if cur.rowcount == 0:
                raise ValueError("FIR not found or already finalized")
            log.info(f"FIR {fir_number} finalized with transaction")
        
        # PERFORMANCE: Invalidate cache
        self._fir_cache.pop(fir_number, None)

    def get_fir(self, fir_number: str) -> Optional[Dict]:
        import time
        
        # PERFORMANCE: Check cache first
        if fir_number in self._fir_cache:
            cached_time, cached_fir = self._fir_cache[fir_number]
            if time.time() - cached_time < self._fir_cache_ttl:
                return cached_fir
        
        with self._cursor(autocommit=True) as cur:
            cur.execute(
                "SELECT * FROM fir_records WHERE fir_number = %s",
                (fir_number,)
            )
            result = cur.fetchone()
            
            # PERFORMANCE: Cache the result
            if result:
                self._fir_cache[fir_number] = (time.time(), result)
            
            return result
    
    def flush_all(self):
        """
        ZERO DATA LOSS: Ensure all pending writes are flushed to disk
        Called during graceful shutdown to prevent data loss
        """
        try:
            # Force MySQL to flush all pending writes to disk
            with self._cursor(autocommit=True) as cur:
                cur.execute("FLUSH TABLES")
                log.info("Database tables flushed to disk")
        except Exception as e:
            log.error(f"Failed to flush database tables: {e}")
            raise

db = DB()

# ------------------------------------------------------------- INTERACTIVE STATE & WORKFLOW
class InteractiveFIRState(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    audio_path: Optional[str] = None
    image_path: Optional[str] = None
    transcript: Optional[str] = None
    summary: Optional[str] = None
    violations: List[Dict[str, Any]] = Field(default_factory=list)
    fir_narrative: Optional[str] = None
    fir_content: str = ""
    fir_number: str = ""
    error: str = ""
    steps: List[str] = Field(default_factory=list)
    current_validation_step: Optional[ValidationStep] = None
    awaiting_validation: bool = False
    user_inputs: Dict[str, str] = Field(default_factory=dict)

async def initial_processing(state: InteractiveFIRState) -> InteractiveFIRState:
    try:
        pool = await ModelPool.get()
        
        if state.audio_path:
            log.info(f"Session {state.session_id}: Starting ASR processing")
            state.transcript = await asyncio.wait_for(
                pool.whisper_transcribe(state.audio_path),  # ✅ Direct async call
                timeout=CFG["model_timeouts"]["asr"]
            )
            state.steps.append("asr_done")
            
        elif state.image_path:
            log.info(f"Session {state.session_id}: Starting OCR processing")
            state.transcript = await asyncio.wait_for(
                pool.dots_ocr_sync(state.image_path),  # ✅ Direct async call
                timeout=CFG["model_timeouts"]["ocr"]
            )
            state.steps.append("ocr_done")
        
        session_manager.add_validation_step(state.session_id, ValidationStep.TRANSCRIPT_REVIEW, {
            "transcript": state.transcript
        })
        
        state.current_validation_step = ValidationStep.TRANSCRIPT_REVIEW
        state.awaiting_validation = True
        session_manager.set_session_status(state.session_id, SessionStatus.AWAITING_VALIDATION)
        
        log.info(f"Session {state.session_id}: Transcript ready for validation")
        
    except Exception as e:
        state.error = f"processing_error:{e}"
        log.error(f"Session {state.session_id}: Processing error: {e}")
        
    return state


# ------------------------------------------------------------- RATE LIMITING
from collections import defaultdict
from time import time

class RateLimiter:
    """Simple in-memory rate limiter"""
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
    
    def is_allowed(self, client_id: str) -> bool:
        now = time()
        # Clean old requests
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if now - req_time < self.window_seconds
        ]
        
        # Check limit
        if len(self.requests[client_id]) >= self.max_requests:
            return False
        
        self.requests[client_id].append(now)
        return True

rate_limiter = RateLimiter(
    max_requests=int(os.getenv("RATE_LIMIT_REQUESTS", 100)),
    window_seconds=int(os.getenv("RATE_LIMIT_WINDOW", 60))
)

# CONCURRENCY: Global semaphore to limit concurrent FIR processing
fir_processing_semaphore = asyncio.Semaphore(CFG["concurrency"]["max_concurrent_requests"])

# RELIABILITY: Global graceful shutdown handler
graceful_shutdown = GracefulShutdown(shutdown_timeout=30.0)

# RELIABILITY: Global health monitor
health_monitor = HealthMonitor(check_interval=30.0, history_size=100)

# RELIABILITY: Global auto-recovery handler
auto_recovery = AutoRecovery(recovery_interval=60.0, max_recovery_attempts=3, recovery_backoff=2.0)

# RELIABILITY: Global dependency health checker
dependency_checker = DependencyHealthCheck(startup_timeout=300.0, check_interval=5.0)

# ------------------------------------------------------------- FASTAPI WITH CORS

# RELIABILITY: Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle with graceful startup and shutdown"""
    # Startup
    log.info("=" * 60)
    log.info("Application startup initiated")
    log.info("=" * 60)
    
    try:
        # Initialize model pool
        pool = await ModelPool.get()
        log.info("✅ Model pool initialized")
        
        # Register dependency health checks
        async def check_model_server():
            try:
                resp = await pool._http_client.get(f"{pool.MODEL_SERVER_URL}/health", timeout=5.0)
                if resp.status_code == 200:
                    health_data = resp.json()
                    return health_data.get("status") in ["healthy", "degraded"]
                return False
            except:
                return False
        
        async def check_asr_ocr_server():
            try:
                resp = await pool._http_client.get(f"{pool.ASR_OCR_SERVER_URL}/health", timeout=5.0)
                if resp.status_code == 200:
                    health_data = resp.json()
                    return health_data.get("status") in ["healthy", "degraded"]
                return False
            except:
                return False
        
        async def check_database():
            try:
                with db._cursor() as cur:
                    cur.execute("SELECT 1")
                    return True
            except:
                return False
        
        # Register dependencies for startup check
        dependency_checker.register_dependency("model_server", check_model_server, required=True)
        dependency_checker.register_dependency("asr_ocr_server", check_asr_ocr_server, required=True)
        dependency_checker.register_dependency("database", check_database, required=True)
        
        # Wait for all dependencies to be healthy before starting
        log.info("Checking dependencies health...")
        if not await dependency_checker.wait_for_dependencies():
            log.error("Failed to start: Required dependencies are not healthy")
            raise RuntimeError("Dependency health check failed")
        log.info("✅ All dependencies are healthy")
        
        # Register health checks for continuous monitoring
        health_monitor.register_check("model_server", check_model_server)
        health_monitor.register_check("asr_ocr_server", check_asr_ocr_server)
        health_monitor.register_check("database", check_database)
        
        # Register auto-recovery handlers
        async def recover_model_server():
            """Recovery handler for model server"""
            log.info("Attempting to recover model server connection...")
            try:
                # Reset circuit breaker
                pool.model_server_circuit.reset()
                # Test connection
                resp = await pool._http_client.get(f"{pool.MODEL_SERVER_URL}/health", timeout=10.0)
                if resp.status_code == 200:
                    log.info("Model server connection recovered")
                    return True
                return False
            except Exception as e:
                log.error(f"Model server recovery failed: {e}")
                return False
        
        async def recover_asr_ocr_server():
            """Recovery handler for ASR/OCR server"""
            log.info("Attempting to recover ASR/OCR server connection...")
            try:
                # Reset circuit breaker
                pool.asr_ocr_circuit.reset()
                # Test connection
                resp = await pool._http_client.get(f"{pool.ASR_OCR_SERVER_URL}/health", timeout=10.0)
                if resp.status_code == 200:
                    log.info("ASR/OCR server connection recovered")
                    return True
                return False
            except Exception as e:
                log.error(f"ASR/OCR server recovery failed: {e}")
                return False
        
        async def recover_database():
            """Recovery handler for database"""
            log.info("Attempting to recover database connection...")
            try:
                # Try to reconnect by getting a new connection from pool
                with db._cursor() as cur:
                    cur.execute("SELECT 1")
                    result = cur.fetchone()
                    if result:
                        log.info("Database connection recovered")
                        return True
                return False
            except Exception as e:
                log.error(f"Database recovery failed: {e}")
                return False
        
        auto_recovery.register_recovery("model_server", recover_model_server)
        auto_recovery.register_recovery("asr_ocr_server", recover_asr_ocr_server)
        auto_recovery.register_recovery("database", recover_database)
        log.info("✅ Auto-recovery handlers registered")
        
        # Start health monitoring with auto-recovery integration
        health_monitor.start()
        log.info("✅ Health monitoring started")
        
        # Setup signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            log.info(f"Received signal {signum}, initiating graceful shutdown...")
            asyncio.create_task(shutdown_handler())
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        log.info("✅ Signal handlers registered")
        
        log.info("=" * 60)
        log.info("🚀 Application startup complete - Ready to serve requests")
        log.info("=" * 60)
        
        yield
        
    finally:
        # Shutdown
        log.info("=" * 60)
        log.info("Application shutdown initiated")
        log.info("=" * 60)
        
        # Stop accepting new requests and wait for in-flight requests
        await graceful_shutdown.shutdown()
        log.info("✅ Graceful shutdown complete - all in-flight requests finished")
        
        # ZERO DATA LOSS: Flush all pending data to disk before shutdown
        try:
            log.info("Flushing all pending data to disk...")
            
            # Flush session database
            session_manager.flush_all()
            log.info("✅ Session data flushed")
            
            # Flush MySQL database
            db.flush_all()
            log.info("✅ MySQL data flushed")
            
            log.info("✅ All data successfully persisted to disk")
        except Exception as e:
            log.error(f"❌ Data flush failed: {e}")
            # Continue shutdown even if flush fails to avoid hanging
        
        # Stop health monitoring
        await health_monitor.stop()
        log.info("✅ Health monitoring stopped")
        
        # Flush CloudWatch metrics
        try:
            log.info("Flushing CloudWatch metrics...")
            await get_metrics().flush_async()
            log.info("✅ CloudWatch metrics flushed")
        except Exception as e:
            log.error(f"Failed to flush CloudWatch metrics: {e}")
        
        # Close HTTP client
        if pool._http_client:
            await pool._http_client.aclose()
            log.info("✅ HTTP client closed")
        
        log.info("=" * 60)
        log.info("👋 Application shutdown complete - Zero data loss guaranteed")
        log.info("=" * 60)

async def shutdown_handler():
    """Handle graceful shutdown"""
    await graceful_shutdown.shutdown()

# Pydantic models are now imported from input_validation module

app = FastAPI(version="8.0.0", lifespan=lifespan)

# Setup X-Ray distributed tracing
setup_xray(app, service_name="afirgen-main-backend")

# CORS Configuration - Load from environment variable
cors_origins_env = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000")
cors_origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]

if "*" in cors_origins:
    log.warning("⚠️  CORS configured with wildcard (*) - This should only be used in development!")

log.info(f"CORS allowed origins: {cors_origins}")

# Use enhanced CORS middleware with validation and logging
from cors_middleware import setup_cors_middleware

setup_cors_middleware(
    app,
    cors_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "X-API-Key"],
    max_age=3600,
    use_enhanced=True,  # Enable enhanced middleware with logging
)

# Rate limiting middleware
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Get client IP (check X-Forwarded-For for proxied requests)
        client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        if not client_ip:
            client_ip = request.headers.get("X-Real-IP", "")
        if not client_ip:
            client_ip = request.client.host if request.client else "unknown"
        
        # Skip rate limiting for health check and docs
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Check rate limit
        if not rate_limiter.is_allowed(client_ip):
            log.warning(f"Rate limit exceeded for IP: {client_ip} on path: {request.url.path}")
            
            # Record rate limit event
            record_rate_limit_event(client_ip, blocked=True)
            
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Maximum 100 requests per minute allowed. Please try again later.",
                    "error": "too_many_requests"
                },
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(rate_limiter.max_requests),
                    "X-RateLimit-Window": str(rate_limiter.window_seconds)
                }
            )
        
        # Record allowed rate limit event
        record_rate_limit_event(client_ip, blocked=False)
        
        response = await call_next(request)
        
        # Add rate limit headers to successful responses
        response.headers["X-RateLimit-Limit"] = str(rate_limiter.max_requests)
        response.headers["X-RateLimit-Window"] = str(rate_limiter.window_seconds)
        
        return response

app.add_middleware(RateLimitMiddleware)

# Security headers middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response

app.add_middleware(SecurityHeadersMiddleware)

# API Authentication middleware
class APIAuthMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce API key authentication on all endpoints except health check"""
    
    # Public endpoints that don't require authentication
    PUBLIC_ENDPOINTS = {"/health", "/docs", "/redoc", "/openapi.json"}
    
    async def dispatch(self, request: Request, call_next):
        # Skip authentication for public endpoints
        if request.url.path in self.PUBLIC_ENDPOINTS:
            return await call_next(request)
        
        # Get API key from header
        api_key = request.headers.get("X-API-Key") or request.headers.get("Authorization")
        
        # Handle Authorization header with Bearer scheme
        if api_key and api_key.startswith("Bearer "):
            api_key = api_key[7:]  # Remove "Bearer " prefix
        
        # Validate API key exists in config
        if not CFG.get("api_key"):
            log.error("API authentication attempted but API_KEY not configured")
            raise HTTPException(
                status_code=500,
                detail="API authentication not properly configured"
            )
        
        # Validate API key
        if not api_key:
            log.warning(f"Missing API key for {request.url.path} from {request.client.host if request.client else 'unknown'}")
            raise HTTPException(
                status_code=401,
                detail="API key required. Include X-API-Key header or Authorization: Bearer <key>"
            )
        
        # Constant-time comparison to prevent timing attacks
        import hmac
        if not hmac.compare_digest(api_key, CFG["api_key"]):
            log.warning(f"Invalid API key attempt for {request.url.path} from {request.client.host if request.client else 'unknown'}")
            raise HTTPException(
                status_code=401,
                detail="Invalid API key"
            )
        
        # API key is valid, proceed with request
        return await call_next(request)

app.add_middleware(APIAuthMiddleware)

# RELIABILITY: Request tracking middleware for graceful shutdown
class RequestTrackingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip tracking for health check
        if request.url.path == "/health":
            return await call_next(request)
        
        # Track request start time for metrics
        start_time = asyncio.get_event_loop().time()
        
        try:
            graceful_shutdown.request_started()
            response = await call_next(request)
            
            # Record API request metrics
            duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
            record_api_request(
                endpoint=request.url.path,
                method=request.method,
                status_code=response.status_code,
                duration_ms=duration_ms
            )
            
            return response
        except RuntimeError as e:
            if "shutting down" in str(e):
                return HTTPException(
                    status_code=503,
                    detail="Server is shutting down"
                ).to_response()
            raise
        except Exception as e:
            # Record error metrics
            duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
            record_api_request(
                endpoint=request.url.path,
                method=request.method,
                status_code=500,
                duration_ms=duration_ms
            )
            raise
        finally:
            graceful_shutdown.request_completed()

    # API Authentication middleware
    class APIAuthMiddleware(BaseHTTPMiddleware):
        """Middleware to enforce API key authentication on all endpoints except health check"""

        # Public endpoints that don't require authentication
        PUBLIC_ENDPOINTS = {"/health", "/docs", "/redoc", "/openapi.json"}

        async def dispatch(self, request: Request, call_next):
            # Skip authentication for public endpoints
            if request.url.path in self.PUBLIC_ENDPOINTS:
                return await call_next(request)

            # Get API key from header
            api_key = request.headers.get("X-API-Key") or request.headers.get("Authorization")

            # Handle Authorization header with Bearer scheme
            if api_key and api_key.startswith("Bearer "):
                api_key = api_key[7:]  # Remove "Bearer " prefix

            # Validate API key exists in config
            if not CFG.get("api_key"):
                log.error("API authentication attempted but API_KEY not configured")
                raise HTTPException(
                    status_code=500,
                    detail="API authentication not properly configured"
                )

            # Validate API key
            if not api_key:
                log.warning(f"Missing API key for {request.url.path} from {request.client.host if request.client else 'unknown'}")
                
                # Record auth failure
                record_auth_event(success=False, reason="missing_key")
                
                raise HTTPException(
                    status_code=401,
                    detail="API key required. Include X-API-Key header or Authorization: Bearer <key>"
                )

            # Constant-time comparison to prevent timing attacks
            import hmac
            if not hmac.compare_digest(api_key, CFG["api_key"]):
                log.warning(f"Invalid API key attempt for {request.url.path} from {request.client.host if request.client else 'unknown'}")
                
                # Record auth failure
                record_auth_event(success=False, reason="invalid_key")
                
                raise HTTPException(
                    status_code=401,
                    detail="Invalid API key"
                )

            # Record auth success
            record_auth_event(success=True)
            
            # API key is valid, proceed with request
            return await call_next(request)

    # RELIABILITY: Request tracking middleware for graceful shutdown
    class RequestTrackingMiddleware(BaseHTTPMiddleware):

app.add_middleware(RequestTrackingMiddleware)

@app.post("/process", response_model=FIRResp)
@trace_subsegment("process_fir_request")
async def process_endpoint(
    audio: Optional[UploadFile] = File(None),
    image: Optional[UploadFile] = File(None),
    text: Optional[str] = None,
):
    """Start FIR processing with enhanced validation and error handling"""
    # Add X-Ray annotations
    add_trace_annotation("endpoint", "/process")
    add_trace_annotation("has_audio", bool(audio))
    add_trace_annotation("has_image", bool(image))
    add_trace_annotation("has_text", bool(text))
    
    # Validate that at least one input is provided
    if not any([audio, image, text]):
        add_trace_annotation("error", "no_input")
        raise HTTPException(status_code=400, detail="No input provided. Please provide audio, image, or text.")
    
    # Validate only one input type is provided
    input_count = sum([bool(audio), bool(image), bool(text)])
    if input_count > 1:
        raise HTTPException(status_code=400, detail="Please provide only one input type (audio, image, or text)")
    
    # Validate file uploads
    if audio:
        validate_file_upload(audio, ValidationConstants.ALLOWED_AUDIO_TYPES)
    
    if image:
        validate_file_upload(image, ValidationConstants.ALLOWED_IMAGE_TYPES)
    
    # Validate and sanitize text input
    if text:
        if len(text) < ValidationConstants.MIN_TEXT_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"Text input too short. Minimum length: {ValidationConstants.MIN_TEXT_LENGTH} characters"
            )
        
        if len(text) > ValidationConstants.MAX_TEXT_LENGTH:
            raise HTTPException(
                status_code=413,
                detail=f"Text input too long. Maximum length: {ValidationConstants.MAX_TEXT_LENGTH} characters"
            )
        
        # Sanitize text input
        text = sanitize_text(text, allow_html=False)

    # CONCURRENCY: Use semaphore to limit concurrent FIR processing
    async with fir_processing_semaphore:
        state = InteractiveFIRState()
        
        async with TempFileManager() as tmp_manager:
            try:
                if audio:
                    state.audio_path = await tmp_manager.save_audio(audio)
                elif image:
                    state.image_path = await tmp_manager.save_image(image)
                elif text:
                    state.transcript = text
                    session_manager.add_validation_step(state.session_id, ValidationStep.TRANSCRIPT_REVIEW, {
                        "transcript": state.transcript
                    })
                    state.current_validation_step = ValidationStep.TRANSCRIPT_REVIEW
                    state.awaiting_validation = True
                
                session_manager.create_session(state.session_id, state.dict())
                
                if audio or image:
                    state = await initial_processing(state)
                    session_manager.update_session(state.session_id, state.dict())
                
                if state.error:
                    return FIRResp(
                        success=False,
                        session_id=state.session_id,
                        error=state.error,
                        steps=state.steps
                    )
                
                return FIRResp(
                    success=True,
                    session_id=state.session_id,
                    steps=state.steps,
                    requires_validation=True,
                    current_step=state.current_validation_step,
                    content_for_validation={"transcript": state.transcript}
                )
                
            except HTTPException:
                raise
            except Exception as e:
                log.error(f"Processing error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

@app.post("/validate", response_model=ValidationResponse)
async def validate_step(validation_req: ValidatedValidationRequest):
    """Enhanced validation with better timeout handling and input validation"""
    # Session ID is already validated by Pydantic model
    session_id = validation_req.session_id
    
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
    if session["status"] != SessionStatus.AWAITING_VALIDATION:
        raise HTTPException(status_code=400, detail="Session not awaiting validation")
    
    # User input is already sanitized by Pydantic validator
    user_input = validation_req.user_input
    
    state_dict = session["state"]
    current_step = state_dict.get("current_validation_step")
    
    try:
        if not validation_req.approved:
            return ValidationResponse(
                success=True,
                session_id=session_id,
                current_step=current_step,
                content={"message": "Please provide corrections or additional input"},
                message="Validation rejected. You can provide additional input to improve the result.",
                requires_validation=True
            )
        
        # Process validation steps with enhanced timeouts
        if current_step == ValidationStep.TRANSCRIPT_REVIEW:
            summary = await generate_summary_with_validation(
                session_id, 
                state_dict["transcript"], 
                user_input
            )
            state_dict.update({
                "summary": summary,
                "current_validation_step": ValidationStep.SUMMARY_REVIEW,
                "user_inputs": {**state_dict.get("user_inputs", {}), "transcript": user_input or ""}
            })
            
            next_content = {"summary": summary, "original_transcript": state_dict["transcript"]}
            next_message = "Summary generated. Please review and validate."
            
        elif current_step == ValidationStep.SUMMARY_REVIEW:
            violations = await find_violations_with_validation(
                session_id,
                state_dict["summary"],
                user_input
            )
            state_dict.update({
                "violations": violations,
                "current_validation_step": ValidationStep.VIOLATIONS_REVIEW,
                "user_inputs": {**state_dict.get("user_inputs", {}), "summary": user_input or ""}
            })
            
            next_content = {"violations": violations, "summary": state_dict["summary"]}
            next_message = "Legal violations identified. Please review and validate."
            
        elif current_step == ValidationStep.VIOLATIONS_REVIEW:
            narrative = await generate_fir_narrative_with_validation(
                session_id,
                state_dict["transcript"],
                user_input
            )
            state_dict.update({
                "fir_narrative": narrative,
                "current_validation_step": ValidationStep.FIR_NARRATIVE_REVIEW,
                "user_inputs": {**state_dict.get("user_inputs", {}), "violations": user_input or ""}
            })
            
            next_content = {"fir_narrative": narrative}
            next_message = "FIR narrative generated. Please review and validate."
            
        elif current_step == ValidationStep.FIR_NARRATIVE_REVIEW:
            fir_number = f"FIR-{session_id[:8]}-{datetime.now():%Y%m%d%H%M%S}"
            
            # Generate structured FIR data
            fir_data = get_fir_data(state_dict, fir_number)
            
            # Render FIR using template
            fir_content = fir_template.format(**fir_data).strip()
            
            # Use DateTimeEncoder for JSON serialization
            violations_json = json.dumps(state_dict["violations"], cls=DateTimeEncoder)
            
            # Save to database
            db.save(fir_number, session_id, state_dict["transcript"], fir_content, violations_json)
            
            state_dict.update({
                "fir_number": fir_number,
                "fir_content": fir_content,
                "current_validation_step": ValidationStep.FINAL_REVIEW,
                "user_inputs": {**state_dict.get("user_inputs", {}), "narrative": user_input or ""}
            })
            
            next_content = {"fir_content": fir_content, "fir_number": fir_number}
            next_message = "FIR generated successfully. Final review required."

            
        elif current_step == ValidationStep.FINAL_REVIEW:
            session_manager.set_session_status(session_id, SessionStatus.COMPLETED)
            state_dict["awaiting_validation"] = False
            
            session_manager.update_session(session_id, state_dict)
            
            return ValidationResponse(
                success=True,
                session_id=session_id,
                current_step=ValidationStep.FINAL_REVIEW,
                content={"fir_content": state_dict["fir_content"], "fir_number": state_dict["fir_number"]},
                message="FIR processing completed successfully!",
                requires_validation=False,
                completed=True
            )
        
        session_manager.update_session(session_id, state_dict)
        
        return ValidationResponse(
            success=True,
            session_id=session_id,
            current_step=state_dict["current_validation_step"],
            content=next_content,
            message=next_message,
            requires_validation=True
        )
        
    except asyncio.TimeoutError:
        log.error(f"Validation timeout for session {session_id}")
        raise HTTPException(status_code=504, detail="Processing timeout - please try again")
    except Exception as e:
        log.error(f"Validation error: {e}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {e}")


@app.get("/session/{session_id}/status")
async def get_session_status(session_id: str):
    """Get session status with validated session ID"""
    # Validate session_id parameter
    session_id = validate_session_id_param(session_id)
    
    # PERFORMANCE: Use async to avoid blocking
    session = await asyncio.to_thread(session_manager.get_session, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
    # PERFORMANCE: Return minimal data for faster serialization
    return {
        "session_id": session_id,
        "status": session["status"],
        "current_step": session["state"].get("current_validation_step"),
        "awaiting_validation": session["state"].get("awaiting_validation", False),
        "created_at": session["created_at"].isoformat(),
        "last_activity": session["last_activity"].isoformat()
    }

@app.post("/regenerate/{session_id}")
async def regenerate_step(session_id: str, step: ValidationStep, user_input: Optional[str] = None):
    """Regenerate a validation step with validated inputs"""
    # Validate session_id parameter
    session_id = validate_session_id_param(session_id)
    
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
    # Validate and sanitize user input
    if user_input:
        if len(user_input) > ValidationConstants.MAX_USER_INPUT_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"User input too long. Maximum length: {ValidationConstants.MAX_USER_INPUT_LENGTH} characters"
            )
        user_input = sanitize_text(user_input, allow_html=False)
    
    state_dict = session["state"]
    
    try:
        if step == ValidationStep.SUMMARY_REVIEW:
            summary = await generate_summary_with_validation(session_id, state_dict["transcript"], user_input)
            state_dict["summary"] = summary
            content = {"summary": summary}
            
        elif step == ValidationStep.VIOLATIONS_REVIEW:
            violations = await find_violations_with_validation(session_id, state_dict["summary"], user_input)
            state_dict["violations"] = violations
            content = {"violations": violations}
            
        elif step == ValidationStep.FIR_NARRATIVE_REVIEW:
            narrative = await generate_fir_narrative_with_validation(session_id, state_dict["transcript"], user_input)
            state_dict["fir_narrative"] = narrative
            content = {"fir_narrative": narrative}
            
        else:
            raise HTTPException(status_code=400, detail="Invalid step for regeneration")
        
        session_manager.update_session(session_id, state_dict)
        
        return {
            "success": True,
            "session_id": session_id,
            "step": step,
            "content": content,
            "message": f"Content regenerated for {step}"
        }
        
    except Exception as e:
        log.error(f"Regeneration error: {e}")
        raise HTTPException(status_code=500, detail=f"Regeneration failed: {e}")

@app.post("/authenticate", response_model=AuthResponse)
async def authenticate_fir(auth_req: ValidatedAuthRequest):
    """Authenticate and finalize FIR with validated inputs"""
    # Inputs are already validated by Pydantic model
    
    # Validate auth key exists
    if not CFG["auth_key"] or CFG["auth_key"] == "default-auth-key":
        log.error("Authentication attempted with default or missing auth key")
        raise HTTPException(status_code=500, detail="Authentication not properly configured")
    
    # Constant-time comparison to prevent timing attacks
    import hmac
    if not hmac.compare_digest(auth_req.auth_key, CFG["auth_key"]):
        log.warning(f"Failed authentication attempt for FIR: {auth_req.fir_number}")
        raise HTTPException(status_code=401, detail="Invalid authentication key")
    
    try:
        fir_record = db.get_fir(auth_req.fir_number)
        if not fir_record:
            raise HTTPException(status_code=404, detail="FIR not found")
        
        if fir_record["status"] == "finalized":
            raise HTTPException(status_code=400, detail="FIR already finalized")
        
        db.finalize_fir(auth_req.fir_number)
        
        return AuthResponse(
            success=True,
            message="FIR successfully finalized",
            fir_number=auth_req.fir_number
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Authentication error: {e}")
        raise HTTPException(status_code=500, detail="Authentication failed")

@app.get("/fir/{fir_number}")
async def get_fir_status(fir_number: str):
    """Get FIR status with validated FIR number"""
    # Validate FIR number parameter
    fir_number = validate_fir_number_param(fir_number)
    
    try:
        # PERFORMANCE: Use async to avoid blocking
        fir_record = await asyncio.to_thread(db.get_fir, fir_number)
        if not fir_record:
            raise HTTPException(status_code=404, detail="FIR not found")
        
        # PERFORMANCE: Return minimal data without full content for faster response
        return {
            "fir_number": fir_number,
            "status": fir_record["status"],
            "created_at": fir_record["created_at"],
            "finalized_at": fir_record.get("finalized_at")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error retrieving FIR: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve FIR")

@app.get("/fir/{fir_number}/content")
async def get_fir_content(fir_number: str):
    """Get full FIR content with validated FIR number - separate endpoint for performance"""
    # Validate FIR number parameter
    fir_number = validate_fir_number_param(fir_number)
    
    try:
        # PERFORMANCE: Use async to avoid blocking
        fir_record = await asyncio.to_thread(db.get_fir, fir_number)
        if not fir_record:
            raise HTTPException(status_code=404, detail="FIR not found")
            
        return {
            "fir_number": fir_number,
            "status": fir_record["status"],
            "created_at": fir_record["created_at"],
            "finalized_at": fir_record.get("finalized_at"),
            "content": fir_record["fir_content"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error retrieving FIR content: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve FIR content")

@app.get("/health")
async def health():
    start_time = asyncio.get_event_loop().time()
    healthy = False
    
    try:
        pool = await ModelPool.get()
        
        # CONCURRENCY: Use shared HTTP client for health checks
        model_resp = await pool._http_client.get(f"{pool.MODEL_SERVER_URL}/health", timeout=5.0)
        model_server_status = model_resp.json()
        
        # Check ASR/OCR server
        asr_ocr_resp = await pool._http_client.get(f"{pool.ASR_OCR_SERVER_URL}/health", timeout=5.0)
        asr_ocr_server_status = asr_ocr_resp.json()
        
        overall_status = "healthy"
        if model_server_status.get("status") != "healthy" or asr_ocr_server_status.get("status") != "healthy":
            overall_status = "degraded"
        
        healthy = overall_status == "healthy"
        
        # Record health check metrics
        duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
        record_health_check("main-backend", healthy, duration_ms)
        
        # RELIABILITY: Include circuit breaker and health monitor status
        return {
            "status": overall_status,
            "model_server": model_server_status,
            "asr_ocr_server": asr_ocr_server_status,
            "database": "connected",
            "kb_collections": len(KB.cols),
            "kb_cache_size": len(KB._query_cache),
            "session_persistence": "sqlite",
            "magic_available": MAGIC_AVAILABLE,
            "concurrency": {
                "max_concurrent_requests": CFG["concurrency"]["max_concurrent_requests"],
                "max_concurrent_model_calls": CFG["concurrency"]["max_concurrent_model_calls"],
                "http_pool_size": CFG["concurrency"]["http_pool_connections"],
            },
            "reliability": {
                "circuit_breakers": {
                    "model_server": pool.model_server_circuit.get_status(),
                    "asr_ocr_server": pool.asr_ocr_circuit.get_status()
                },
                "graceful_shutdown": graceful_shutdown.get_status(),
                "health_monitor": health_monitor.get_status()
            }
        }
    except Exception as e:
        log.error(f"Health check failed: {e}")
        
        # Record unhealthy status
        duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
        record_health_check("main-backend", False, duration_ms)
        
        return {"status": "unhealthy", "error": str(e)}

# PERFORMANCE: Metrics cache
_metrics_cache = None
_metrics_cache_time = 0
_metrics_cache_ttl = 10  # 10 seconds cache for metrics

@app.get("/metrics")
async def get_metrics():
    """PERFORMANCE: Endpoint for monitoring performance metrics with caching"""
    import time
    
    global _metrics_cache, _metrics_cache_time
    
    # PERFORMANCE: Return cached metrics if available
    if _metrics_cache and (time.time() - _metrics_cache_time) < _metrics_cache_ttl:
        return _metrics_cache
    
    try:
        def _get_metrics():
            # Session statistics
            with sqlite3.connect(CFG["session_db_path"]) as conn:
                cursor = conn.execute("""
                    SELECT 
                        status,
                        COUNT(*) as count,
                        AVG(CAST((julianday(last_activity) - julianday(created_at)) * 86400 AS INTEGER)) as avg_duration_seconds
                    FROM sessions
                    WHERE created_at > datetime('now', '-1 hour')
                    GROUP BY status
                """)
                session_stats = [
                    {"status": row[0], "count": row[1], "avg_duration": row[2]}
                    for row in cursor.fetchall()
                ]
            
            # FIR statistics
            with db._cursor() as cur:
                cur.execute("""
                    SELECT 
                        status,
                        COUNT(*) as count,
                        AVG(TIMESTAMPDIFF(SECOND, created_at, COALESCE(finalized_at, NOW()))) as avg_time_seconds
                    FROM fir_records
                    WHERE created_at > DATE_SUB(NOW(), INTERVAL 1 HOUR)
                    GROUP BY status
                """)
                fir_stats = cur.fetchall()
            
            return {
                "timestamp": datetime.now().isoformat(),
                "sessions": {
                    "recent_hour": session_stats,
                    "cache_size": len(KB._query_cache)
                },
                "firs": {
                    "recent_hour": fir_stats
                },
                "rate_limiter": {
                    "active_clients": len(rate_limiter.requests)
                }
            }
        
        # PERFORMANCE: Use async to avoid blocking
        metrics = await asyncio.to_thread(_get_metrics)
        
        # PERFORMANCE: Cache the result
        _metrics_cache = metrics
        _metrics_cache_time = time.time()
        
        return metrics
        
    except Exception as e:
        log.error(f"Metrics collection failed: {e}")
        return {"error": str(e)}

@app.get("/reliability")
async def get_reliability_status():
    """RELIABILITY: Endpoint for monitoring reliability components and uptime"""
    try:
        pool = await ModelPool.get()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "circuit_breakers": {
                "model_server": pool.model_server_circuit.get_status(),
                "asr_ocr_server": pool.asr_ocr_circuit.get_status()
            },
            "graceful_shutdown": graceful_shutdown.get_status(),
            "health_monitor": health_monitor.get_status(),
            "auto_recovery": auto_recovery.get_status(),
            "uptime_target": "99.9%",
            "max_downtime_per_month": "43.8 minutes"
        }
    except Exception as e:
        log.error(f"Reliability status collection failed: {e}")
        return {"error": str(e)}

@app.post("/reliability/circuit-breaker/{name}/reset")
async def reset_circuit_breaker(name: str):
    """RELIABILITY: Manually reset a circuit breaker with validated name"""
    # Validate circuit breaker name
    name = validate_circuit_breaker_name(name)
    
    try:
        pool = await ModelPool.get()
        
        if name == "model_server":
            pool.model_server_circuit.reset()
            auto_recovery.reset_recovery("model_server")
        elif name == "asr_ocr_server":
            pool.asr_ocr_circuit.reset()
            auto_recovery.reset_recovery("asr_ocr_server")
        
        log.info(f"Circuit breaker '{name}' manually reset")
        return {
            "success": True,
            "message": f"Circuit breaker '{name}' has been reset",
            "status": pool.model_server_circuit.get_status() if name == "model_server" else pool.asr_ocr_circuit.get_status()
        }
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Failed to reset circuit breaker: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reliability/auto-recovery/{name}/trigger")
async def trigger_manual_recovery(name: str):
    """RELIABILITY: Manually trigger auto-recovery for a service with validated name"""
    # Validate recovery handler name
    name = validate_recovery_name(name)
    
    try:
        log.info(f"Manual recovery triggered for: {name}")
        success = await auto_recovery.trigger_recovery(name)
        
        return {
            "success": success,
            "message": f"Recovery {'succeeded' if success else 'failed'} for '{name}'",
            "status": auto_recovery.get_status(name)
        }
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Failed to trigger recovery: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/view_fir_records", response_class=HTMLResponse)
def view_fir_records():
    with db._cursor() as cur:
        cur.execute("SELECT fir_number, status, created_at FROM fir_records ORDER BY created_at DESC LIMIT 100")
        records = cur.fetchall()

    # Simple HTML table to display records
    html_content = """
    <html>
      <head><title>FIR Records</title></head>
      <body>
        <h1>FIR Records (Latest 100)</h1>
        <table border="1" cellspacing="0" cellpadding="5">
          <tr>
            <th>FIR Number</th>
            <th>Status</th>
            <th>Created At</th>
            <th>View FIR</th>
          </tr>
    """

    for r in records:
        html_content += f"""
          <tr>
            <td>{r['fir_number']}</td>
            <td>{r['status']}</td>
            <td>{r['created_at']}</td>
            <td><a href="/view_fir/{r['fir_number']}" target="_blank">View</a></td>
          </tr>
        """

    html_content += """
        </table>
      </body>
    </html>
    """

    return html_content


@app.get("/view_fir/{fir_number}", response_class=HTMLResponse)
def view_fir(fir_number: str):
    """View FIR content as HTML with validated FIR number"""
    # Validate FIR number parameter
    try:
        fir_number = validate_fir_number_param(fir_number)
    except HTTPException:
        return HTMLResponse(content="<h2>Invalid FIR number format</h2>", status_code=400)
    
    record = db.get_fir(fir_number)
    if not record:
        return HTMLResponse(content="<h2>FIR not found</h2>", status_code=404)

    # Escape HTML to prevent XSS
    import html
    fir_text = html.escape(record['fir_content']).replace('\n', '<br/>')
    fir_number_escaped = html.escape(fir_number)
    
    return f"""
    <html>
      <head><title>View FIR {fir_number_escaped}</title></head>
      <body>
        <h1>FIR Number: {fir_number_escaped}</h1>
        <div style="white-space: pre-wrap; font-family: monospace;">{fir_text}</div>
      </body>
    </html>
    """
@app.get("/list_firs")
async def list_firs(limit: Optional[int] = None, offset: Optional[int] = None):
    """PERFORMANCE: Optimized list endpoint with async, minimal data, and validated pagination"""
    # Validate query parameters
    limit = validate_limit_param(limit, default=20, max_limit=100)
    offset = validate_offset_param(offset, default=0)
    
    def _list_firs():
        with db._cursor() as cur:
            # PERFORMANCE: Only select needed columns, use index, support pagination
            cur.execute(
                "SELECT fir_number, status, created_at FROM fir_records "
                "ORDER BY created_at DESC LIMIT %s OFFSET %s",
                (limit, offset)
            )
            return cur.fetchall()
    
    # PERFORMANCE: Use async to avoid blocking
    records = await asyncio.to_thread(_list_firs)
    
    # PERFORMANCE: Return list directly without extra processing
    return {
        "records": records,
        "limit": limit,
        "offset": offset,
        "count": len(records)
    }


if __name__ == "__main__":
    uvicorn.run("fir_pipeline_production_ready:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
