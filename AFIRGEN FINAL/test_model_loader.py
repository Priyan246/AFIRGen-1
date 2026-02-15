"""
test_model_loader.py
-----------------------------------------------------------------------------
Unit and Property-Based Tests for Model Loader Module
-----------------------------------------------------------------------------

Tests the model_loader module for:
- File existence validation
- Checksum validation
- Error handling for missing/corrupted models
- Graceful degradation
- Descriptive error messages

Requirements Validated: 4.1.4 (Model loading with error handling)
"""

import os
import pytest
import tempfile
import hashlib
from pathlib import Path
from unittest.mock import Mock, patch
from hypothesis import given, strategies as st, settings, assume

from model_loader import (
    ModelLoader,
    ModelConfig,
    ModelLoadResult,
    ModelStatus,
    ModelValidationError,
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def temp_model_dir():
    """Create a temporary directory for test models"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_model_file(temp_model_dir):
    """Create a sample model file with known content"""
    model_path = temp_model_dir / "test_model.gguf"
    content = b"This is a test model file with some content"
    model_path.write_bytes(content)
    
    # Calculate checksum
    checksum = hashlib.sha256(content).hexdigest()
    
    return model_path, checksum


@pytest.fixture
def model_loader(temp_model_dir):
    """Create a ModelLoader instance"""
    return ModelLoader(model_dir=temp_model_dir, validate_checksums=True)


def mock_loader_success(path, **kwargs):
    """Mock loader function that succeeds"""
    return {"model": "loaded", "path": str(path)}


def mock_loader_failure(path, **kwargs):
    """Mock loader function that fails"""
    raise RuntimeError("Mock loader failure")


# ============================================================================
# Unit Tests - File Validation
# ============================================================================

def test_validate_file_exists_success(model_loader, sample_model_file):
    """Test file validation succeeds for valid file"""
    model_path, _ = sample_model_file
    is_valid, error_msg = model_loader._validate_file_exists(model_path)
    
    assert is_valid is True
    assert "passed" in error_msg.lower()


def test_validate_file_exists_missing(model_loader, temp_model_dir):
    """Test file validation fails for missing file"""
    missing_path = temp_model_dir / "nonexistent.gguf"
    is_valid, error_msg = model_loader._validate_file_exists(missing_path)
    
    assert is_valid is False
    assert "not found" in error_msg.lower()
    assert str(missing_path) in error_msg


def test_validate_file_exists_empty(model_loader, temp_model_dir):
    """Test file validation fails for empty file"""
    empty_path = temp_model_dir / "empty.gguf"
    empty_path.write_bytes(b"")
    
    is_valid, error_msg = model_loader._validate_file_exists(empty_path)
    
    assert is_valid is False
    assert "empty" in error_msg.lower()


def test_validate_file_exists_directory(model_loader, temp_model_dir):
    """Test file validation fails for directory"""
    dir_path = temp_model_dir / "not_a_file"
    dir_path.mkdir()
    
    is_valid, error_msg = model_loader._validate_file_exists(dir_path)
    
    assert is_valid is False
    assert "not a file" in error_msg.lower()


# ============================================================================
# Unit Tests - Checksum Validation
# ============================================================================

def test_calculate_checksum_success(model_loader, sample_model_file):
    """Test checksum calculation succeeds"""
    model_path, expected_checksum = sample_model_file
    actual_checksum = model_loader._calculate_checksum(model_path)
    
    assert actual_checksum == expected_checksum
    assert len(actual_checksum) == 64  # SHA256 hex digest length


def test_calculate_checksum_different_algorithms(model_loader, sample_model_file):
    """Test checksum calculation with different algorithms"""
    model_path, _ = sample_model_file
    
    sha256 = model_loader._calculate_checksum(model_path, algorithm="sha256")
    md5 = model_loader._calculate_checksum(model_path, algorithm="md5")
    sha1 = model_loader._calculate_checksum(model_path, algorithm="sha1")
    
    assert len(sha256) == 64
    assert len(md5) == 32
    assert len(sha1) == 40
    assert sha256 != md5 != sha1


def test_calculate_checksum_invalid_algorithm(model_loader, sample_model_file):
    """Test checksum calculation fails with invalid algorithm"""
    model_path, _ = sample_model_file
    
    with pytest.raises(ValueError, match="Unsupported hash algorithm"):
        model_loader._calculate_checksum(model_path, algorithm="invalid")


def test_validate_checksum_success(model_loader, sample_model_file):
    """Test checksum validation succeeds for matching checksum"""
    model_path, expected_checksum = sample_model_file
    
    is_valid, actual, error_msg = model_loader._validate_checksum(
        model_path, expected_checksum
    )
    
    assert is_valid is True
    assert actual == expected_checksum
    assert "passed" in error_msg.lower()


def test_validate_checksum_mismatch(model_loader, sample_model_file):
    """Test checksum validation fails for mismatched checksum"""
    model_path, _ = sample_model_file
    wrong_checksum = "0" * 64
    
    is_valid, actual, error_msg = model_loader._validate_checksum(
        model_path, wrong_checksum
    )
    
    assert is_valid is False
    assert "mismatch" in error_msg.lower()
    assert wrong_checksum in error_msg
    assert actual in error_msg


def test_validate_checksum_case_insensitive(model_loader, sample_model_file):
    """Test checksum validation is case-insensitive"""
    model_path, expected_checksum = sample_model_file
    
    # Test with uppercase
    is_valid, _, _ = model_loader._validate_checksum(
        model_path, expected_checksum.upper()
    )
    assert is_valid is True
    
    # Test with lowercase
    is_valid, _, _ = model_loader._validate_checksum(
        model_path, expected_checksum.lower()
    )
    assert is_valid is True


# ============================================================================
# Unit Tests - Model Registration and Loading
# ============================================================================

def test_register_model(model_loader):
    """Test model registration"""
    config = ModelConfig(
        name="test_model",
        path=Path("test.gguf"),
        loader_func=mock_loader_success,
        required=True,
    )
    
    model_loader.register_model(config)
    
    assert "test_model" in model_loader.model_configs
    assert model_loader.model_status["test_model"] == ModelStatus.NOT_LOADED


def test_load_single_model_success(model_loader, sample_model_file):
    """Test successful single model loading"""
    model_path, checksum = sample_model_file
    
    config = ModelConfig(
        name="test_model",
        path=model_path,
        loader_func=mock_loader_success,
        required=True,
        expected_checksum=checksum,
    )
    
    result = model_loader._load_single_model(config)
    
    assert result.success is True
    assert result.model is not None
    assert result.error_message is None
    assert result.load_time > 0
    assert model_loader.model_status["test_model"] == ModelStatus.LOADED


def test_load_single_model_missing_file(model_loader, temp_model_dir):
    """Test model loading fails gracefully for missing file"""
    config = ModelConfig(
        name="missing_model",
        path=temp_model_dir / "nonexistent.gguf",
        loader_func=mock_loader_success,
        required=True,
    )
    
    result = model_loader._load_single_model(config)
    
    assert result.success is False
    assert "not found" in result.error_message.lower()
    assert model_loader.model_status["missing_model"] == ModelStatus.FAILED
    assert "missing_model" in model_loader.model_errors


def test_load_single_model_checksum_mismatch(model_loader, sample_model_file):
    """Test model loading fails for checksum mismatch"""
    model_path, _ = sample_model_file
    wrong_checksum = "0" * 64
    
    config = ModelConfig(
        name="corrupted_model",
        path=model_path,
        loader_func=mock_loader_success,
        required=True,
        expected_checksum=wrong_checksum,
    )
    
    result = model_loader._load_single_model(config)
    
    assert result.success is False
    assert "mismatch" in result.error_message.lower()
    assert model_loader.model_status["corrupted_model"] == ModelStatus.FAILED


def test_load_single_model_loader_failure(model_loader, sample_model_file):
    """Test model loading fails gracefully when loader function fails"""
    model_path, checksum = sample_model_file
    
    config = ModelConfig(
        name="failing_model",
        path=model_path,
        loader_func=mock_loader_failure,
        required=True,
        expected_checksum=checksum,
    )
    
    result = model_loader._load_single_model(config)
    
    assert result.success is False
    assert "Mock loader failure" in result.error_message
    assert model_loader.model_status["failing_model"] == ModelStatus.FAILED


def test_load_single_model_with_retry(model_loader, sample_model_file):
    """Test model loading retries on failure"""
    model_path, checksum = sample_model_file
    
    # Mock loader that fails first time, succeeds second time
    call_count = [0]
    def mock_loader_retry(path, **kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            raise RuntimeError("First attempt fails")
        return {"model": "loaded"}
    
    config = ModelConfig(
        name="retry_model",
        path=model_path,
        loader_func=mock_loader_retry,
        required=True,
        expected_checksum=checksum,
        retry_count=2,
    )
    
    result = model_loader._load_single_model(config)
    
    assert result.success is True
    assert call_count[0] == 2  # Should have retried


# ============================================================================
# Unit Tests - Get Model
# ============================================================================

def test_get_model_success(model_loader, sample_model_file):
    """Test getting a loaded model"""
    model_path, checksum = sample_model_file
    
    config = ModelConfig(
        name="test_model",
        path=model_path,
        loader_func=mock_loader_success,
        expected_checksum=checksum,
    )
    
    model_loader.register_model(config)
    model_loader._load_single_model(config)
    
    model = model_loader.get_model("test_model")
    assert model is not None


def test_get_model_unknown(model_loader):
    """Test getting unknown model raises ValueError"""
    with pytest.raises(ValueError, match="Unknown model"):
        model_loader.get_model("nonexistent")


def test_get_model_not_loaded(model_loader, temp_model_dir):
    """Test getting failed model raises RuntimeError"""
    config = ModelConfig(
        name="failed_model",
        path=temp_model_dir / "missing.gguf",
        loader_func=mock_loader_success,
    )
    
    model_loader.register_model(config)
    model_loader._load_single_model(config)
    
    with pytest.raises(RuntimeError, match="not available"):
        model_loader.get_model("failed_model")


# ============================================================================
# Unit Tests - Health Status
# ============================================================================

def test_health_status_all_loaded(model_loader, sample_model_file):
    """Test health status when all models loaded"""
    model_path, checksum = sample_model_file
    
    config = ModelConfig(
        name="test_model",
        path=model_path,
        loader_func=mock_loader_success,
        expected_checksum=checksum,
    )
    
    model_loader.register_model(config)
    model_loader._load_single_model(config)
    
    health = model_loader.get_health_status()
    
    assert health["status"] == "healthy"
    assert health["loaded_count"] == 1
    assert health["total_count"] == 1
    assert health["models_loaded"]["test_model"] is True


def test_health_status_required_missing(model_loader, temp_model_dir):
    """Test health status when required model missing"""
    config = ModelConfig(
        name="required_model",
        path=temp_model_dir / "missing.gguf",
        loader_func=mock_loader_success,
        required=True,
    )
    
    model_loader.register_model(config)
    model_loader._load_single_model(config)
    
    health = model_loader.get_health_status()
    
    assert health["status"] == "unhealthy"
    assert "Critical models not loaded" in health["message"]
    assert health["loaded_count"] == 0


def test_health_status_optional_missing(model_loader, sample_model_file, temp_model_dir):
    """Test health status when optional model missing"""
    model_path, checksum = sample_model_file
    
    # Required model that loads
    config1 = ModelConfig(
        name="required_model",
        path=model_path,
        loader_func=mock_loader_success,
        required=True,
        expected_checksum=checksum,
    )
    
    # Optional model that fails
    config2 = ModelConfig(
        name="optional_model",
        path=temp_model_dir / "missing.gguf",
        loader_func=mock_loader_success,
        required=False,
    )
    
    model_loader.register_model(config1)
    model_loader.register_model(config2)
    model_loader._load_single_model(config1)
    model_loader._load_single_model(config2)
    
    health = model_loader.get_health_status()
    
    assert health["status"] == "degraded"
    assert "optional models missing" in health["message"]
    assert health["loaded_count"] == 1
    assert health["total_count"] == 2


# ============================================================================
# Unit Tests - Load All Models
# ============================================================================

def test_load_all_models_sequential(model_loader, temp_model_dir):
    """Test loading all models sequentially"""
    # Create two test model files
    model1_path = temp_model_dir / "model1.gguf"
    model2_path = temp_model_dir / "model2.gguf"
    model1_path.write_bytes(b"model1")
    model2_path.write_bytes(b"model2")
    
    config1 = ModelConfig(
        name="model1",
        path=model1_path,
        loader_func=mock_loader_success,
    )
    config2 = ModelConfig(
        name="model2",
        path=model2_path,
        loader_func=mock_loader_success,
    )
    
    model_loader.register_model(config1)
    model_loader.register_model(config2)
    
    results = model_loader.load_all_models(parallel=False)
    
    assert len(results) == 2
    assert results["model1"].success is True
    assert results["model2"].success is True


def test_load_all_models_parallel(model_loader, temp_model_dir):
    """Test loading all models in parallel"""
    # Create two test model files
    model1_path = temp_model_dir / "model1.gguf"
    model2_path = temp_model_dir / "model2.gguf"
    model1_path.write_bytes(b"model1")
    model2_path.write_bytes(b"model2")
    
    config1 = ModelConfig(
        name="model1",
        path=model1_path,
        loader_func=mock_loader_success,
    )
    config2 = ModelConfig(
        name="model2",
        path=model2_path,
        loader_func=mock_loader_success,
    )
    
    model_loader.register_model(config1)
    model_loader.register_model(config2)
    
    results = model_loader.load_all_models(parallel=True)
    
    assert len(results) == 2
    assert results["model1"].success is True
    assert results["model2"].success is True


def test_load_all_models_required_missing_raises(model_loader, temp_model_dir):
    """Test loading fails when required model missing"""
    config = ModelConfig(
        name="required_model",
        path=temp_model_dir / "missing.gguf",
        loader_func=mock_loader_success,
        required=True,
    )
    
    model_loader.register_model(config)
    
    with pytest.raises(RuntimeError, match="Critical models failed to load"):
        model_loader.load_all_models()


# ============================================================================
# Property-Based Tests
# ============================================================================

# Feature: afirgen-aws-optimization, Property 1: Model Loading Error Handling
@settings(max_examples=100)
@given(
    file_scenario=st.sampled_from([
        "missing",      # File doesn't exist
        "empty",        # File is empty
        "corrupted",    # Checksum mismatch
    ])
)
def test_property_model_loading_error_handling(file_scenario):
    """
    Property 1: Model Loading Error Handling
    
    For any model file that is missing, corrupted, or invalid, the system
    SHALL return a descriptive error message and fail gracefully without
    crashing, allowing other services to continue operating.
    
    Validates: Requirements 4.1.4
    """
    # Create temp directory for this test - keep it in scope
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_model_dir = Path(tmpdir)
        loader = ModelLoader(model_dir=temp_model_dir, validate_checksums=True)
        
        # Setup scenario
        if file_scenario == "missing":
            model_path = temp_model_dir / "nonexistent.gguf"
            expected_checksum = None
        elif file_scenario == "empty":
            model_path = temp_model_dir / "empty.gguf"
            model_path.write_bytes(b"")
            expected_checksum = None
        elif file_scenario == "corrupted":
            model_path = temp_model_dir / "corrupted.gguf"
            model_path.write_bytes(b"some content")
            expected_checksum = "0" * 64  # Wrong checksum
        
        config = ModelConfig(
            name="test_model",
            path=model_path,
            loader_func=mock_loader_success,
            required=False,  # Don't raise exception
            expected_checksum=expected_checksum,
        )
        
        loader.register_model(config)
        
        # Load should not crash
        result = loader._load_single_model(config)
        
        # Verify graceful failure
        assert result.success is False, f"Should fail for {file_scenario} model"
        assert result.error_message is not None, "Should have error message"
        assert len(result.error_message) > 0, "Error message should be descriptive"
        assert result.model is None, "Should not return a model object"
        
        # Verify error is tracked
        assert "test_model" in loader.model_errors
        assert loader.model_status["test_model"] == ModelStatus.FAILED
        
        # Verify system continues operating (can check health)
        health = loader.get_health_status()
        assert health is not None
        assert "status" in health


@settings(max_examples=50)
@given(
    num_models=st.integers(min_value=1, max_value=5),
    failure_rate=st.floats(min_value=0.0, max_value=1.0),
)
def test_property_partial_model_loading(num_models, failure_rate):
    """
    Property: Partial Model Loading
    
    For any set of models where some fail to load, the system SHALL load
    the successful models and provide detailed status for each model.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_model_dir = Path(tmpdir)
        loader = ModelLoader(model_dir=temp_model_dir, validate_checksums=False)
    
    # Create models with some that will fail
    for i in range(num_models):
        model_path = temp_model_dir / f"model{i}.gguf"
        
        # Determine if this model should fail
        should_fail = (i / num_models) < failure_rate
        
        if should_fail:
            # Don't create the file (will fail)
            pass
        else:
            # Create valid file
            model_path.write_bytes(f"model{i}".encode())
        
        config = ModelConfig(
            name=f"model{i}",
            path=model_path,
            loader_func=mock_loader_success,
            required=False,  # Don't raise on failure
        )
        loader.register_model(config)
    
    # Load all models
    results = loader.load_all_models(parallel=False)
    
    # Verify results
    assert len(results) == num_models
    
    # Check each model has a result
    for i in range(num_models):
        assert f"model{i}" in results
        result = results[f"model{i}"]
        assert isinstance(result, ModelLoadResult)
        
        # If failed, should have error message
        if not result.success:
            assert result.error_message is not None
            assert len(result.error_message) > 0


@settings(max_examples=50)
@given(
    content=st.binary(min_size=1, max_size=1024),
    algorithm=st.sampled_from(["sha256", "md5", "sha1"]),
)
def test_property_checksum_consistency(content, algorithm):
    """
    Property: Checksum Consistency
    
    For any file content and hash algorithm, calculating the checksum
    multiple times SHALL always return the same result.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_model_dir = Path(tmpdir)
        loader = ModelLoader(model_dir=temp_model_dir)
    
    # Create file with content
    model_path = temp_model_dir / "test.bin"
    model_path.write_bytes(content)
    
    # Calculate checksum multiple times
    checksum1 = loader._calculate_checksum(model_path, algorithm)
    checksum2 = loader._calculate_checksum(model_path, algorithm)
    checksum3 = loader._calculate_checksum(model_path, algorithm)
    
    # All should be identical
    assert checksum1 == checksum2 == checksum3
    
    # Should be valid hex string
    assert all(c in "0123456789abcdef" for c in checksum1.lower())


# ============================================================================
# Integration Tests
# ============================================================================

def test_integration_full_workflow(temp_model_dir):
    """Test complete workflow: register, load, get, health check"""
    # Create test model files
    model1_path = temp_model_dir / "model1.gguf"
    model2_path = temp_model_dir / "model2.gguf"
    content1 = b"model1 content"
    content2 = b"model2 content"
    model1_path.write_bytes(content1)
    model2_path.write_bytes(content2)
    
    checksum1 = hashlib.sha256(content1).hexdigest()
    checksum2 = hashlib.sha256(content2).hexdigest()
    
    # Initialize loader
    loader = ModelLoader(model_dir=temp_model_dir, validate_checksums=True)
    
    # Register models
    loader.register_model(ModelConfig(
        name="model1",
        path=model1_path,
        loader_func=mock_loader_success,
        required=True,
        expected_checksum=checksum1,
    ))
    loader.register_model(ModelConfig(
        name="model2",
        path=model2_path,
        loader_func=mock_loader_success,
        required=False,
        expected_checksum=checksum2,
    ))
    
    # Load all models
    results = loader.load_all_models(parallel=True)
    
    # Verify loading
    assert results["model1"].success is True
    assert results["model2"].success is True
    
    # Get models
    model1 = loader.get_model("model1")
    model2 = loader.get_model("model2")
    assert model1 is not None
    assert model2 is not None
    
    # Check health
    health = loader.get_health_status()
    assert health["status"] == "healthy"
    assert health["loaded_count"] == 2
    assert health["total_count"] == 2
    
    # Get model info
    info1 = loader.get_model_info("model1")
    assert info1["loaded"] is True
    assert info1["required"] is True
    assert info1["checksum"] == checksum1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
