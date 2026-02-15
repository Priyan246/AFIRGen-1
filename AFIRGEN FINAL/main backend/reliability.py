# reliability.py
# -------------------------------------------------------------
# Reliability Components for 99.9% Uptime SLA
# -------------------------------------------------------------

import asyncio
import logging
import time
from typing import Callable, Any, Optional
from enum import Enum
from datetime import datetime, timedelta
from collections import deque

# Note: Logger will be configured by json_logging module when imported by main application
log = logging.getLogger("reliability")


class CircuitState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker pattern implementation to prevent cascading failures.
    
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, reject requests immediately
    - HALF_OPEN: After timeout, allow test requests to check if service recovered
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception,
        name: str = "circuit_breaker"
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.name = name
        
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = CircuitState.CLOSED
        
        log.info(f"Circuit breaker '{name}' initialized: threshold={failure_threshold}, timeout={recovery_timeout}s")
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        
        # Check if circuit is open
        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if self.last_failure_time and (time.time() - self.last_failure_time) > self.recovery_timeout:
                log.info(f"Circuit breaker '{self.name}': Transitioning to HALF_OPEN")
                self.state = CircuitState.HALF_OPEN
            else:
                raise RuntimeError(f"Circuit breaker '{self.name}' is OPEN - service unavailable")
        
        try:
            # Execute the function
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            
            # Success - reset failure count
            if self.state == CircuitState.HALF_OPEN:
                log.info(f"Circuit breaker '{self.name}': Service recovered, transitioning to CLOSED")
                self.state = CircuitState.CLOSED
                self.failure_count = 0
            elif self.failure_count > 0:
                self.failure_count = 0
                log.debug(f"Circuit breaker '{self.name}': Reset failure count")
            
            return result
            
        except self.expected_exception as e:
            # Failure - increment counter
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            log.warning(
                f"Circuit breaker '{self.name}': Failure {self.failure_count}/{self.failure_threshold} - {e}"
            )
            
            # Check if threshold exceeded
            if self.failure_count >= self.failure_threshold:
                log.error(f"Circuit breaker '{self.name}': Threshold exceeded, transitioning to OPEN")
                self.state = CircuitState.OPEN
            
            raise
    
    def reset(self):
        """Manually reset circuit breaker"""
        log.info(f"Circuit breaker '{self.name}': Manual reset")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
    
    def get_status(self) -> dict:
        """Get current circuit breaker status"""
        return {
            "name": self.name,
            "state": self.state,
            "failure_count": self.failure_count,
            "last_failure_time": datetime.fromtimestamp(self.last_failure_time).isoformat() if self.last_failure_time else None,
            "threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout
        }


class RetryPolicy:
    """
    Retry policy with exponential backoff for transient failures.
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        name: str = "retry_policy"
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.name = name
        
        log.info(f"Retry policy '{name}' initialized: max_retries={max_retries}, initial_delay={initial_delay}s")
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and optional jitter"""
        delay = min(self.initial_delay * (self.exponential_base ** attempt), self.max_delay)
        
        if self.jitter:
            import random
            delay = delay * (0.5 + random.random() * 0.5)  # Add 0-50% jitter
        
        return delay
    
    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry logic"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                
                if attempt > 0:
                    log.info(f"Retry policy '{self.name}': Success on attempt {attempt + 1}")
                
                return result
                
            except Exception as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    delay = self._calculate_delay(attempt)
                    log.warning(
                        f"Retry policy '{self.name}': Attempt {attempt + 1} failed - {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    log.error(f"Retry policy '{self.name}': All {self.max_retries + 1} attempts failed")
        
        raise last_exception


class HealthMonitor:
    """
    Continuous health monitoring for critical dependencies.
    Tracks health status and provides metrics.
    """
    
    def __init__(self, check_interval: float = 30.0, history_size: int = 100):
        self.check_interval = check_interval
        self.history_size = history_size
        
        self.health_checks: dict[str, Callable] = {}
        self.health_status: dict[str, bool] = {}
        self.health_history: dict[str, deque] = {}
        self.last_check_time: dict[str, float] = {}
        
        self._monitoring_task: Optional[asyncio.Task] = None
        self._running = False
        
        log.info(f"Health monitor initialized: check_interval={check_interval}s, history_size={history_size}")
    
    def register_check(self, name: str, check_func: Callable):
        """Register a health check function"""
        self.health_checks[name] = check_func
        self.health_status[name] = False
        self.health_history[name] = deque(maxlen=self.history_size)
        self.last_check_time[name] = 0
        
        log.info(f"Health check registered: {name}")
    
    async def _run_check(self, name: str) -> bool:
        """Run a single health check"""
        try:
            check_func = self.health_checks[name]
            result = await check_func() if asyncio.iscoroutinefunction(check_func) else check_func()
            return bool(result)
        except Exception as e:
            log.error(f"Health check '{name}' failed: {e}")
            return False
    
    async def _monitoring_loop(self):
        """Continuous monitoring loop"""
        log.info("Health monitoring started")
        
        while self._running:
            try:
                for name in self.health_checks:
                    is_healthy = await self._run_check(name)
                    
                    # Update status
                    previous_status = self.health_status.get(name, False)
                    self.health_status[name] = is_healthy
                    self.last_check_time[name] = time.time()
                    
                    # Record in history
                    self.health_history[name].append({
                        "timestamp": time.time(),
                        "healthy": is_healthy
                    })
                    
                    # Log status changes
                    if previous_status != is_healthy:
                        if is_healthy:
                            log.info(f"Health check '{name}': RECOVERED")
                        else:
                            log.error(f"Health check '{name}': FAILED")
                
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                log.error(f"Health monitoring error: {e}")
                await asyncio.sleep(self.check_interval)
    
    def start(self):
        """Start health monitoring"""
        if not self._running:
            self._running = True
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())
            log.info("Health monitoring task started")
    
    async def stop(self):
        """Stop health monitoring"""
        if self._running:
            self._running = False
            if self._monitoring_task:
                self._monitoring_task.cancel()
                try:
                    await self._monitoring_task
                except asyncio.CancelledError:
                    pass
            log.info("Health monitoring stopped")
    
    def get_status(self, name: Optional[str] = None) -> dict:
        """Get health status for specific check or all checks"""
        if name:
            if name not in self.health_checks:
                raise ValueError(f"Unknown health check: {name}")
            
            history = list(self.health_history[name])
            uptime_percentage = (sum(1 for h in history if h["healthy"]) / len(history) * 100) if history else 0
            
            return {
                "name": name,
                "healthy": self.health_status[name],
                "last_check": datetime.fromtimestamp(self.last_check_time[name]).isoformat() if self.last_check_time[name] else None,
                "uptime_percentage": round(uptime_percentage, 2),
                "history_size": len(history)
            }
        else:
            return {
                "checks": {
                    name: self.get_status(name)
                    for name in self.health_checks
                },
                "overall_healthy": all(self.health_status.values())
            }


class GracefulShutdown:
    """
    Graceful shutdown handler to ensure in-flight requests complete.
    """
    
    def __init__(self, shutdown_timeout: float = 30.0):
        self.shutdown_timeout = shutdown_timeout
        self.is_shutting_down = False
        self.active_requests = 0
        self._shutdown_event = asyncio.Event()
        
        log.info(f"Graceful shutdown handler initialized: timeout={shutdown_timeout}s")
    
    def request_started(self):
        """Mark request as started"""
        if self.is_shutting_down:
            raise RuntimeError("Server is shutting down")
        self.active_requests += 1
    
    def request_completed(self):
        """Mark request as completed"""
        self.active_requests -= 1
        if self.is_shutting_down and self.active_requests == 0:
            self._shutdown_event.set()
    
    async def shutdown(self):
        """Initiate graceful shutdown"""
        log.info(f"Graceful shutdown initiated. Active requests: {self.active_requests}")
        self.is_shutting_down = True
        
        if self.active_requests == 0:
            log.info("No active requests, shutting down immediately")
            return
        
        log.info(f"Waiting for {self.active_requests} active requests to complete...")
        
        try:
            await asyncio.wait_for(self._shutdown_event.wait(), timeout=self.shutdown_timeout)
            log.info("All requests completed, shutting down")
        except asyncio.TimeoutError:
            log.warning(
                f"Shutdown timeout reached with {self.active_requests} requests still active. "
                "Forcing shutdown."
            )
    
    def get_status(self) -> dict:
        """Get shutdown handler status"""
        return {
            "is_shutting_down": self.is_shutting_down,
            "active_requests": self.active_requests,
            "shutdown_timeout": self.shutdown_timeout
        }


class AutoRecovery:
    """
    Automatic service recovery handler for critical dependencies.
    Monitors service health and triggers recovery actions on failure.
    """
    
    def __init__(
        self,
        recovery_interval: float = 60.0,
        max_recovery_attempts: int = 3,
        recovery_backoff: float = 2.0
    ):
        self.recovery_interval = recovery_interval
        self.max_recovery_attempts = max_recovery_attempts
        self.recovery_backoff = recovery_backoff
        
        self.recovery_handlers: dict[str, Callable] = {}
        self.recovery_attempts: dict[str, int] = {}
        self.last_recovery_time: dict[str, float] = {}
        self.recovery_in_progress: dict[str, bool] = {}
        
        self._monitoring_task: Optional[asyncio.Task] = None
        self._running = False
        
        log.info(
            f"Auto-recovery initialized: interval={recovery_interval}s, "
            f"max_attempts={max_recovery_attempts}, backoff={recovery_backoff}x"
        )
    
    def register_recovery(self, name: str, recovery_func: Callable):
        """Register a recovery handler for a service"""
        self.recovery_handlers[name] = recovery_func
        self.recovery_attempts[name] = 0
        self.last_recovery_time[name] = 0
        self.recovery_in_progress[name] = False
        
        log.info(f"Recovery handler registered: {name}")
    
    async def trigger_recovery(self, name: str, error: Optional[Exception] = None) -> bool:
        """Trigger recovery for a specific service"""
        if name not in self.recovery_handlers:
            log.error(f"No recovery handler registered for: {name}")
            return False
        
        # Check if recovery is already in progress
        if self.recovery_in_progress[name]:
            log.warning(f"Recovery already in progress for: {name}")
            return False
        
        # Check if we've exceeded max attempts
        if self.recovery_attempts[name] >= self.max_recovery_attempts:
            time_since_last = time.time() - self.last_recovery_time[name]
            if time_since_last < self.recovery_interval:
                log.error(
                    f"Max recovery attempts ({self.max_recovery_attempts}) reached for: {name}. "
                    f"Waiting {self.recovery_interval - time_since_last:.0f}s before retry."
                )
                return False
            else:
                # Reset attempts after cooldown period
                log.info(f"Recovery cooldown period elapsed for: {name}. Resetting attempts.")
                self.recovery_attempts[name] = 0
        
        # Mark recovery in progress
        self.recovery_in_progress[name] = True
        self.recovery_attempts[name] += 1
        self.last_recovery_time[name] = time.time()
        
        log.info(
            f"Triggering recovery for: {name} (attempt {self.recovery_attempts[name]}/{self.max_recovery_attempts})"
        )
        if error:
            log.info(f"Recovery triggered by error: {error}")
        
        try:
            # Calculate backoff delay
            backoff_delay = self.recovery_backoff ** (self.recovery_attempts[name] - 1)
            if backoff_delay > 1:
                log.info(f"Applying backoff delay: {backoff_delay:.1f}s")
                await asyncio.sleep(backoff_delay)
            
            # Execute recovery handler
            recovery_func = self.recovery_handlers[name]
            result = await recovery_func() if asyncio.iscoroutinefunction(recovery_func) else recovery_func()
            
            if result:
                log.info(f"Recovery successful for: {name}")
                self.recovery_attempts[name] = 0  # Reset on success
                return True
            else:
                log.error(f"Recovery failed for: {name}")
                return False
                
        except Exception as e:
            log.error(f"Recovery exception for {name}: {e}")
            return False
        finally:
            self.recovery_in_progress[name] = False
    
    def reset_recovery(self, name: str):
        """Manually reset recovery state for a service"""
        if name in self.recovery_attempts:
            self.recovery_attempts[name] = 0
            self.last_recovery_time[name] = 0
            self.recovery_in_progress[name] = False
            log.info(f"Recovery state reset for: {name}")
    
    def get_status(self, name: Optional[str] = None) -> dict:
        """Get recovery status"""
        if name:
            if name not in self.recovery_handlers:
                raise ValueError(f"Unknown recovery handler: {name}")
            
            return {
                "name": name,
                "attempts": self.recovery_attempts[name],
                "max_attempts": self.max_recovery_attempts,
                "last_recovery": datetime.fromtimestamp(self.last_recovery_time[name]).isoformat() if self.last_recovery_time[name] else None,
                "in_progress": self.recovery_in_progress[name]
            }
        else:
            return {
                "handlers": {
                    name: self.get_status(name)
                    for name in self.recovery_handlers
                },
                "recovery_interval": self.recovery_interval,
                "max_attempts": self.max_recovery_attempts
            }


class DependencyHealthCheck:
    """
    Startup dependency health checker.
    Ensures all critical dependencies are healthy before service starts.
    """
    
    def __init__(self, startup_timeout: float = 300.0, check_interval: float = 5.0):
        self.startup_timeout = startup_timeout
        self.check_interval = check_interval
        self.dependencies: dict[str, Callable] = {}
        
        log.info(
            f"Dependency health check initialized: timeout={startup_timeout}s, "
            f"check_interval={check_interval}s"
        )
    
    def register_dependency(self, name: str, check_func: Callable, required: bool = True):
        """Register a dependency health check"""
        self.dependencies[name] = {
            "check_func": check_func,
            "required": required
        }
        log.info(f"Dependency registered: {name} (required={required})")
    
    async def wait_for_dependencies(self) -> bool:
        """Wait for all required dependencies to be healthy"""
        log.info("Waiting for dependencies to be healthy...")
        start_time = time.time()
        
        while True:
            elapsed = time.time() - start_time
            if elapsed > self.startup_timeout:
                log.error(f"Dependency health check timeout after {self.startup_timeout}s")
                return False
            
            all_healthy = True
            failed_required = []
            
            for name, dep_info in self.dependencies.items():
                try:
                    check_func = dep_info["check_func"]
                    is_healthy = await check_func() if asyncio.iscoroutinefunction(check_func) else check_func()
                    
                    if not is_healthy:
                        if dep_info["required"]:
                            all_healthy = False
                            failed_required.append(name)
                            log.warning(f"Required dependency not healthy: {name}")
                        else:
                            log.info(f"Optional dependency not healthy: {name}")
                    else:
                        log.debug(f"Dependency healthy: {name}")
                        
                except Exception as e:
                    if dep_info["required"]:
                        all_healthy = False
                        failed_required.append(name)
                        log.error(f"Required dependency check failed: {name} - {e}")
                    else:
                        log.warning(f"Optional dependency check failed: {name} - {e}")
            
            if all_healthy:
                log.info("All required dependencies are healthy")
                return True
            
            log.info(
                f"Waiting for dependencies: {', '.join(failed_required)} "
                f"(elapsed: {elapsed:.0f}s/{self.startup_timeout:.0f}s)"
            )
            await asyncio.sleep(self.check_interval)
        
        return False
