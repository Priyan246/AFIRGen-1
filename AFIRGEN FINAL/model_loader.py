"""
model_loader.py
-----------------------------------------------------------------------------
Reusable Model Loader Module with Validation and Error Handling
-----------------------------------------------------------------------------

This module provides a robust, reusable model loading infrastructure for all
AFIRGen model servers (GGUF, Whisper, dots_ocr). It implements:

- Model file existence checks
- Model file integrity validation (checksum)
- Graceful error handling for missing/corrupted models
- Descriptive error messages
- Retry logic with exponential backoff
- Parallel model loading for faster cold starts
- Comprehensive logging

Requirements Validated: 4.1.4 (Model loading with error handling)
"""

import os
import hashlib
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Callable, Any, Tuple, List
from dataclasses import dataclass
from enum import Enum


class ModelStatus(Enum):
    """Model loading status"""
    NOT_LOADED = "not_loaded"
    LOADING = "loading"
    LOADED = "loaded"
    FAILED = "failed"


@dataclass
class ModelConfig:
    """Configuration for a single model"""
    name: str
    path: Path
    loader_func: Callable
    required: bool = True
    expected_checksum: Optional[str] = None
    checksum_algorithm: str = "sha256"
    retry_count: int = 1
    loader_kwargs: Optional[Dict[str, Any]] = None


@dataclass
class ModelLoadResult:
    """Result of model loading operation"""
    success: bool
    model: Any = None
    error_message: Optional[str] = None
    load_time: float = 0.0
    checksum: Optional[str] = None


class ModelValidationError(Exception):
    """Raised when model validation fails"""
    pass


class ModelLoader:
    """
    Reusable model loader with validation and error handling.
    
    Features:
    - File existence and accessibility checks
    - File integrity validation via checksums
    - Graceful error handling with descriptive messages
    - Retry logic with configurable attempts
    - Parallel loading support
    - Comprehensive logging
    
    Example usage:
        loader = ModelLoader(model_dir=Path("./models"))
        
        # Register models
        loader.register_model(ModelConfig(
            name="summariser",
            path=Path("./models/summariser.gguf"),
            loader_func=load_gguf_model,
            required=True,
            expected_checksum="abc123...",
        ))
        
        # Load all models
        results = loader.load_all_models(parallel=True)
        
        # Get a loaded model
        model = loader.get_model("summariser")
    """
    
    def __init__(
        self,
        model_dir: Path,
        logger: Optional[logging.Logger] = None,
        validate_checksums: bool = True,
    ):
        """
        Initialize model loader.
        
        Args:
            model_dir: Base directory for models
            logger: Logger instance (creates default if None)
            validate_checksums: Whether to validate checksums
        """
        self.model_dir = Path(model_dir)
        self.logger = logger or logging.getLogger(__name__)
        self.validate_checksums = validate_checksums
        
        self.models: Dict[str, Any] = {}
        self.model_configs: Dict[str, ModelConfig] = {}
        self.model_status: Dict[str, ModelStatus] = {}
        self.model_errors: Dict[str, str] = {}
        self.model_checksums: Dict[str, str] = {}
        
        self.logger.info(f"ModelLoader initialized with model_dir: {self.model_dir}")
    
    def register_model(self, config: ModelConfig) -> None:
        """
        Register a model for loading.
        
        Args:
            config: Model configuration
        """
        self.model_configs[config.name] = config
        self.model_status[config.name] = ModelStatus.NOT_LOADED
        self.logger.debug(f"Registered model: {config.name}")
    
    def _validate_file_exists(self, path: Path) -> Tuple[bool, str]:
        """
        Validate that model file exists and is accessible.
        
        Args:
            path: Path to model file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not path.exists():
            return False, f"Model file not found: {path}"
        
        if not path.is_file():
            return False, f"Path is not a file: {path}"
        
        if path.stat().st_size == 0:
            return False, f"Model file is empty (0 bytes): {path}"
        
        if not os.access(path, os.R_OK):
            return False, f"Model file is not readable (permission denied): {path}"
        
        return True, "File validation passed"
    
    def _calculate_checksum(
        self,
        path: Path,
        algorithm: str = "sha256",
        chunk_size: int = 8192
    ) -> str:
        """
        Calculate checksum of model file.
        
        Args:
            path: Path to model file
            algorithm: Hash algorithm (sha256, md5, sha1)
            chunk_size: Bytes to read at a time
            
        Returns:
            Hex digest of checksum
            
        Raises:
            ValueError: If algorithm is not supported
        """
        try:
            hash_func = hashlib.new(algorithm)
        except ValueError:
            raise ValueError(
                f"Unsupported hash algorithm: {algorithm}. "
                f"Supported: {', '.join(hashlib.algorithms_available)}"
            )
        
        try:
            with open(path, 'rb') as f:
                while chunk := f.read(chunk_size):
                    hash_func.update(chunk)
            
            return hash_func.hexdigest()
            
        except Exception as e:
            raise ModelValidationError(f"Failed to calculate checksum: {e}")
    
    def _validate_checksum(
        self,
        path: Path,
        expected: str,
        algorithm: str = "sha256"
    ) -> Tuple[bool, str, str]:
        """
        Validate model file checksum.
        
        Args:
            path: Path to model file
            expected: Expected checksum (hex digest)
            algorithm: Hash algorithm
            
        Returns:
            Tuple of (is_valid, actual_checksum, error_message)
        """
        try:
            actual = self._calculate_checksum(path, algorithm)
            
            if actual.lower() != expected.lower():
                return (
                    False,
                    actual,
                    f"Checksum mismatch! Expected: {expected}, Got: {actual}. "
                    f"File may be corrupted or tampered with."
                )
            
            return True, actual, "Checksum validation passed"
            
        except Exception as e:
            return False, "", f"Checksum validation failed: {e}"
    
    def _validate_model_file(self, config: ModelConfig) -> Tuple[bool, str]:
        """
        Comprehensive validation of model file.
        
        Args:
            config: Model configuration
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check file exists and is accessible
        is_valid, error_msg = self._validate_file_exists(config.path)
        if not is_valid:
            return False, error_msg
        
        # Validate checksum if provided and enabled
        if self.validate_checksums and config.expected_checksum:
            is_valid, actual_checksum, error_msg = self._validate_checksum(
                config.path,
                config.expected_checksum,
                config.checksum_algorithm
            )
            
            if not is_valid:
                return False, error_msg
            
            # Store actual checksum for reference
            self.model_checksums[config.name] = actual_checksum
            self.logger.debug(
                f"{config.name} checksum validated: {actual_checksum[:16]}..."
            )
        
        return True, "Validation passed"
    
    def _load_single_model(self, config: ModelConfig) -> ModelLoadResult:
        """
        Load a single model with validation and retry logic.
        
        Args:
            config: Model configuration
            
        Returns:
            ModelLoadResult with success status and details
        """
        start_time = time.time()
        
        # Update status
        self.model_status[config.name] = ModelStatus.LOADING
        
        # Validate file first
        is_valid, validation_msg = self._validate_model_file(config)
        if not is_valid:
            self.logger.error(f"❌ {config.name} validation failed: {validation_msg}")
            self.model_status[config.name] = ModelStatus.FAILED
            self.model_errors[config.name] = validation_msg
            return ModelLoadResult(
                success=False,
                error_message=validation_msg,
                load_time=time.time() - start_time
            )
        
        # Attempt to load with retries
        for attempt in range(config.retry_count):
            try:
                self.logger.info(
                    f"Loading {config.name} from {config.path} "
                    f"(attempt {attempt + 1}/{config.retry_count})"
                )
                
                # Call the loader function
                loader_kwargs = config.loader_kwargs or {}
                model = config.loader_func(config.path, **loader_kwargs)
                
                # Validate model object
                if model is None:
                    raise RuntimeError("Loader returned None")
                
                # Success!
                load_time = time.time() - start_time
                self.models[config.name] = model
                self.model_status[config.name] = ModelStatus.LOADED
                self.model_errors.pop(config.name, None)  # Clear any previous errors
                
                self.logger.info(
                    f"✅ {config.name} loaded successfully in {load_time:.2f}s"
                )
                
                return ModelLoadResult(
                    success=True,
                    model=model,
                    load_time=load_time,
                    checksum=self.model_checksums.get(config.name)
                )
                
            except Exception as e:
                error_msg = f"Load attempt {attempt + 1} failed: {str(e)}"
                self.logger.warning(f"⚠️  {config.name}: {error_msg}")
                
                if attempt == config.retry_count - 1:  # Last attempt
                    load_time = time.time() - start_time
                    self.logger.error(
                        f"❌ Failed to load {config.name} after "
                        f"{config.retry_count} attempts"
                    )
                    self.model_status[config.name] = ModelStatus.FAILED
                    self.model_errors[config.name] = str(e)
                    
                    return ModelLoadResult(
                        success=False,
                        error_message=str(e),
                        load_time=load_time
                    )
                
                # Wait before retry (exponential backoff)
                wait_time = 0.5 * (2 ** attempt)
                time.sleep(wait_time)
        
        # Should not reach here, but handle gracefully
        return ModelLoadResult(
            success=False,
            error_message="Unknown error during loading",
            load_time=time.time() - start_time
        )
    
    def load_all_models(
        self,
        parallel: bool = True,
        max_workers: Optional[int] = None
    ) -> Dict[str, ModelLoadResult]:
        """
        Load all registered models.
        
        Args:
            parallel: Whether to load models in parallel
            max_workers: Max parallel workers (defaults to min(num_models, 3))
            
        Returns:
            Dictionary mapping model names to load results
        """
        start_time = time.time()
        
        self.logger.info("=" * 70)
        self.logger.info("Starting model loading process...")
        self.logger.info(f"Model directory: {self.model_dir}")
        self.logger.info(f"Parallel loading: {parallel}")
        self.logger.info(f"Checksum validation: {self.validate_checksums}")
        self.logger.info(f"Models to load: {len(self.model_configs)}")
        self.logger.info("=" * 70)
        
        # Validate model directory
        if not self.model_dir.exists():
            self.logger.warning(
                f"⚠️  Model directory does not exist: {self.model_dir}"
            )
            self.logger.info("Creating model directory...")
            self.model_dir.mkdir(parents=True, exist_ok=True)
        
        results = {}
        
        if parallel and len(self.model_configs) > 1:
            # Parallel loading
            import concurrent.futures
            
            if max_workers is None:
                max_workers = min(len(self.model_configs), 3)
            
            self.logger.info(f"Using {max_workers} parallel workers")
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all loading tasks
                future_to_model = {
                    executor.submit(self._load_single_model, config): config.name
                    for config in self.model_configs.values()
                }
                
                # Collect results as they complete
                for future in concurrent.futures.as_completed(future_to_model):
                    model_name = future_to_model[future]
                    try:
                        results[model_name] = future.result()
                    except Exception as e:
                        self.logger.error(
                            f"❌ {model_name} loading failed with exception: {e}"
                        )
                        results[model_name] = ModelLoadResult(
                            success=False,
                            error_message=str(e)
                        )
        else:
            # Sequential loading
            for config in self.model_configs.values():
                results[config.name] = self._load_single_model(config)
        
        # Print summary
        elapsed_time = time.time() - start_time
        self._print_loading_summary(results, elapsed_time)
        
        # Check if required models loaded
        self._validate_required_models(results)
        
        return results
    
    def _print_loading_summary(
        self,
        results: Dict[str, ModelLoadResult],
        elapsed_time: float
    ) -> None:
        """Print summary of model loading results"""
        self.logger.info("\n" + "=" * 70)
        self.logger.info("Model Loading Summary:")
        self.logger.info("=" * 70)
        
        for model_name, result in results.items():
            config = self.model_configs[model_name]
            status = "✅ LOADED" if result.success else "❌ FAILED"
            required = " (REQUIRED)" if config.required else " (optional)"
            
            self.logger.info(
                f"{model_name:25s}: {status}{required} "
                f"({result.load_time:.2f}s)"
            )
            
            if not result.success:
                self.logger.info(f"  Error: {result.error_message}")
        
        loaded_count = sum(1 for r in results.values() if r.success)
        total_count = len(results)
        
        self.logger.info("=" * 70)
        self.logger.info(
            f"Total: {loaded_count}/{total_count} models loaded successfully"
        )
        self.logger.info(f"Total loading time: {elapsed_time:.2f} seconds")
        self.logger.info("=" * 70)
    
    def _validate_required_models(
        self,
        results: Dict[str, ModelLoadResult]
    ) -> None:
        """
        Validate that all required models loaded successfully.
        
        Raises:
            RuntimeError: If any required model failed to load
        """
        missing_required = [
            name for name, config in self.model_configs.items()
            if config.required and not results.get(name, ModelLoadResult(False)).success
        ]
        
        if missing_required:
            error_msg = (
                f"Critical models failed to load: {', '.join(missing_required)}. "
                f"Service cannot start without these models."
            )
            self.logger.error(f"❌ {error_msg}")
            raise RuntimeError(error_msg)
        
        if not any(r.success for r in results.values()):
            error_msg = "No models loaded successfully! Service cannot start."
            self.logger.error(f"❌ {error_msg}")
            raise RuntimeError(error_msg)
    
    def get_model(self, model_name: str) -> Any:
        """
        Get a loaded model by name.
        
        Args:
            model_name: Name of the model
            
        Returns:
            The loaded model object
            
        Raises:
            ValueError: If model name is unknown
            RuntimeError: If model failed to load
        """
        if model_name not in self.model_configs:
            available = ", ".join(self.model_configs.keys())
            raise ValueError(
                f"Unknown model: '{model_name}'. Available models: {available}"
            )
        
        model = self.models.get(model_name)
        if model is None:
            status = self.model_status.get(model_name, ModelStatus.NOT_LOADED)
            error_detail = self.model_errors.get(model_name, "Unknown error")
            
            raise RuntimeError(
                f"Model '{model_name}' is not available (status: {status.value}). "
                f"Loading failed with: {error_detail}"
            )
        
        return model
    
    def is_model_loaded(self, model_name: str) -> bool:
        """Check if a model is loaded successfully"""
        return (
            model_name in self.models and
            self.models[model_name] is not None and
            self.model_status.get(model_name) == ModelStatus.LOADED
        )
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status of all models.
        
        Returns:
            Dictionary with health information
        """
        models_status = {
            name: self.is_model_loaded(name)
            for name in self.model_configs.keys()
        }
        
        loaded_count = sum(models_status.values())
        total_count = len(models_status)
        
        # Determine overall health
        required_models = [
            name for name, config in self.model_configs.items()
            if config.required
        ]
        
        missing_required = [
            name for name in required_models
            if not models_status.get(name, False)
        ]
        
        if loaded_count == total_count:
            status = "healthy"
            message = "All models loaded successfully"
        elif missing_required:
            # Required models missing - always unhealthy
            status = "unhealthy"
            message = f"Critical models not loaded: {', '.join(missing_required)}"
        elif loaded_count > 0:
            # Some models loaded, no required missing - degraded
            status = "degraded"
            message = (
                f"{loaded_count}/{total_count} models loaded "
                f"(optional models missing)"
            )
        else:
            # No models loaded at all
            status = "unhealthy"
            message = "No models loaded"
        
        # Add error details
        if self.model_errors:
            error_summary = "; ".join([
                f"{k}: {v}" for k, v in self.model_errors.items()
            ])
            message = f"{message}. Errors: {error_summary}"
        
        return {
            "status": status,
            "message": message,
            "models_loaded": models_status,
            "loaded_count": loaded_count,
            "total_count": total_count,
            "errors": dict(self.model_errors),
        }
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Dictionary with model information
        """
        if model_name not in self.model_configs:
            raise ValueError(f"Unknown model: {model_name}")
        
        config = self.model_configs[model_name]
        
        return {
            "name": config.name,
            "path": str(config.path),
            "required": config.required,
            "status": self.model_status.get(model_name, ModelStatus.NOT_LOADED).value,
            "loaded": self.is_model_loaded(model_name),
            "error": self.model_errors.get(model_name),
            "checksum": self.model_checksums.get(model_name),
        }
