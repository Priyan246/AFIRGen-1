"""
Test CloudWatch Metrics Integration
Tests the CloudWatch metrics module and integration with the application
"""

import sys
import os
import time
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Add main backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "main backend"))

def test_cloudwatch_metrics_module():
    """Test CloudWatch metrics module functionality"""
    print("\n" + "="*60)
    print("TEST: CloudWatch Metrics Module")
    print("="*60)
    
    from cloudwatch_metrics import CloudWatchMetrics
    
    # Test initialization with CloudWatch disabled (local dev)
    metrics = CloudWatchMetrics(enabled=False)
    assert not metrics.enabled, "Metrics should be disabled in local dev"
    print("✅ Metrics disabled in local development mode")
    
    # Test metric recording (should not fail when disabled)
    metrics.put_metric("TestMetric", 1.0, unit="Count")
    metrics.record_count("TestCount", 5)
    metrics.record_duration("TestDuration", 100.0)
    metrics.record_percentage("TestPercentage", 95.5)
    metrics.record_size("TestSize", 1024)
    print("✅ Metric recording works when disabled (no-op)")
    
    # Test buffer management
    assert len(metrics.metric_buffer) == 0, "Buffer should be empty when disabled"
    print("✅ Metric buffer management works")
    
    # Test flush (should not fail when disabled)
    metrics.flush()
    print("✅ Flush works when disabled")
    
    print("\n✅ All CloudWatch metrics module tests passed!")
    return True


def test_cloudwatch_metrics_with_mock_aws():
    """Test CloudWatch metrics with mocked AWS client"""
    print("\n" + "="*60)
    print("TEST: CloudWatch Metrics with Mock AWS")
    print("="*60)
    
    # Mock boto3 at the module level before importing
    import sys
    mock_boto3 = MagicMock()
    sys.modules['boto3'] = mock_boto3
    sys.modules['botocore'] = MagicMock()
    sys.modules['botocore.exceptions'] = MagicMock()
    
    # Reload the module to pick up the mock
    import importlib
    import cloudwatch_metrics
    importlib.reload(cloudwatch_metrics)
    
    from cloudwatch_metrics import CloudWatchMetrics
    
    mock_client = Mock()
    mock_boto3.client.return_value = mock_client
    
    # Test initialization with CloudWatch enabled
    metrics = CloudWatchMetrics(enabled=True)
    assert metrics.enabled, "Metrics should be enabled"
    assert metrics.client is not None, "Client should be initialized"
    print("✅ Metrics enabled with mocked AWS client")
    
    # Test metric recording
    metrics.put_metric("TestMetric", 1.0, unit="Count", dimensions={"Service": "Test"})
    assert len(metrics.metric_buffer) == 1, "Metric should be buffered"
    print("✅ Metric buffering works")
    
    # Test metric with dimensions
    metric = metrics.metric_buffer[0]
    assert metric["MetricName"] == "TestMetric"
    assert metric["Value"] == 1.0
    assert metric["Unit"] == "Count"
    assert len(metric["Dimensions"]) == 1
    assert metric["Dimensions"][0]["Name"] == "Service"
    assert metric["Dimensions"][0]["Value"] == "Test"
    print("✅ Metric dimensions work correctly")
    
    # Test flush
    metrics.flush()
    assert len(metrics.metric_buffer) == 0, "Buffer should be empty after flush"
    mock_client.put_metric_data.assert_called_once()
    call_args = mock_client.put_metric_data.call_args
    assert call_args[1]["Namespace"] == "AFIRGen"
    assert len(call_args[1]["MetricData"]) == 1
    print("✅ Metric flush works correctly")
    
    # Test auto-flush on buffer size
    for i in range(25):
        metrics.put_metric(f"Metric{i}", float(i), unit="Count")
    
    # Should have flushed once (20 metrics) and have 5 remaining
    assert len(metrics.metric_buffer) == 5, f"Should have 5 metrics in buffer, got {len(metrics.metric_buffer)}"
    assert mock_client.put_metric_data.call_count == 2, "Should have flushed once automatically"
    print("✅ Auto-flush on buffer size works")
    
    print("\n✅ All CloudWatch metrics with mock AWS tests passed!")
    return True


def test_convenience_functions():
    """Test convenience functions for common metrics"""
    print("\n" + "="*60)
    print("TEST: Convenience Functions")
    print("="*60)
    
    with patch('cloudwatch_metrics.boto3'):
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
        
        # Initialize with disabled metrics for testing
        metrics = get_metrics()
        metrics.enabled = False
        
        # Test API request recording
        record_api_request("/test", "GET", 200, 150.0)
        print("✅ record_api_request works")
        
        # Test FIR generation recording
        record_fir_generation(success=True, duration_ms=25000.0, step="summary")
        print("✅ record_fir_generation works")
        
        # Test model inference recording
        record_model_inference("llama", 5000.0, token_count=150)
        print("✅ record_model_inference works")
        
        # Test database operation recording
        record_database_operation("save", 50.0, success=True)
        print("✅ record_database_operation works")
        
        # Test cache operation recording
        record_cache_operation("session_cache", hit=True)
        print("✅ record_cache_operation works")
        
        # Test rate limit event recording
        record_rate_limit_event("192.168.1.1", blocked=False)
        print("✅ record_rate_limit_event works")
        
        # Test auth event recording
        record_auth_event(success=True)
        print("✅ record_auth_event works")
        
        # Test health check recording
        record_health_check("model_server", healthy=True, response_time_ms=100.0)
        print("✅ record_health_check works")
    
    print("\n✅ All convenience function tests passed!")
    return True


def test_track_duration_decorator():
    """Test the track_duration decorator"""
    print("\n" + "="*60)
    print("TEST: Track Duration Decorator")
    print("="*60)
    
    with patch('cloudwatch_metrics.boto3'):
        from cloudwatch_metrics import track_duration, get_metrics
        
        # Initialize with disabled metrics for testing
        metrics = get_metrics()
        metrics.enabled = False
        
        # Test sync function
        @track_duration("SyncFunction", {"Type": "Test"})
        def sync_function():
            time.sleep(0.1)
            return "result"
        
        result = sync_function()
        assert result == "result", "Function should return correct result"
        print("✅ Sync function decorator works")
        
        # Test async function
        @track_duration("AsyncFunction", {"Type": "Test"})
        async def async_function():
            await asyncio.sleep(0.1)
            return "async_result"
        
        result = asyncio.run(async_function())
        assert result == "async_result", "Async function should return correct result"
        print("✅ Async function decorator works")
        
        # Test error handling
        @track_duration("ErrorFunction", {"Type": "Test"})
        def error_function():
            raise ValueError("Test error")
        
        try:
            error_function()
            assert False, "Should have raised ValueError"
        except ValueError:
            pass
        print("✅ Error handling in decorator works")
    
    print("\n✅ All decorator tests passed!")
    return True


def test_async_flush():
    """Test async flush functionality"""
    print("\n" + "="*60)
    print("TEST: Async Flush")
    print("="*60)
    
    with patch('cloudwatch_metrics.boto3') as mock_boto3:
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client
        
        from cloudwatch_metrics import CloudWatchMetrics
        
        metrics = CloudWatchMetrics(enabled=True)
        
        # Add some metrics
        metrics.put_metric("TestMetric1", 1.0)
        metrics.put_metric("TestMetric2", 2.0)
        
        # Test async flush
        async def test_async():
            await metrics.flush_async()
            assert len(metrics.metric_buffer) == 0, "Buffer should be empty after async flush"
            assert mock_client.put_metric_data.called, "Should have called put_metric_data"
        
        asyncio.run(test_async())
        print("✅ Async flush works correctly")
    
    print("\n✅ All async flush tests passed!")
    return True


def test_environment_detection():
    """Test automatic environment detection"""
    print("\n" + "="*60)
    print("TEST: Environment Detection")
    print("="*60)
    
    with patch('cloudwatch_metrics.boto3'):
        from cloudwatch_metrics import CloudWatchMetrics
        
        # Test development environment (should disable CloudWatch)
        os.environ["ENVIRONMENT"] = "development"
        metrics = CloudWatchMetrics()
        assert not metrics.enabled, "Should be disabled in development"
        print("✅ CloudWatch disabled in development environment")
        
        # Test production environment (should enable CloudWatch)
        os.environ["ENVIRONMENT"] = "production"
        metrics = CloudWatchMetrics()
        assert metrics.enabled, "Should be enabled in production"
        print("✅ CloudWatch enabled in production environment")
        
        # Clean up
        if "ENVIRONMENT" in os.environ:
            del os.environ["ENVIRONMENT"]
    
    print("\n✅ All environment detection tests passed!")
    return True


def test_metric_batching():
    """Test metric batching (max 20 per request)"""
    print("\n" + "="*60)
    print("TEST: Metric Batching")
    print("="*60)
    
    with patch('cloudwatch_metrics.boto3') as mock_boto3:
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client
        
        from cloudwatch_metrics import CloudWatchMetrics
        
        metrics = CloudWatchMetrics(enabled=True)
        
        # Add 45 metrics (should batch into 3 requests: 20, 20, 5)
        for i in range(45):
            metrics.put_metric(f"Metric{i}", float(i))
        
        metrics.flush()
        
        # Should have made 3 calls to put_metric_data
        assert mock_client.put_metric_data.call_count == 3, f"Should have made 3 calls, got {mock_client.put_metric_data.call_count}"
        
        # Verify batch sizes
        calls = mock_client.put_metric_data.call_args_list
        assert len(calls[0][1]["MetricData"]) == 20, "First batch should have 20 metrics"
        assert len(calls[1][1]["MetricData"]) == 20, "Second batch should have 20 metrics"
        assert len(calls[2][1]["MetricData"]) == 5, "Third batch should have 5 metrics"
        
        print("✅ Metric batching works correctly (max 20 per request)")
    
    print("\n✅ All metric batching tests passed!")
    return True


def test_error_handling():
    """Test error handling in metric publishing"""
    print("\n" + "="*60)
    print("TEST: Error Handling")
    print("="*60)
    
    # Mock boto3 and botocore exceptions properly
    import sys
    from unittest.mock import MagicMock
    
    # Create proper exception classes
    class MockClientError(Exception):
        pass
    
    class MockBotoCoreError(Exception):
        pass
    
    mock_boto3 = MagicMock()
    mock_botocore = MagicMock()
    mock_botocore.exceptions = MagicMock()
    mock_botocore.exceptions.ClientError = MockClientError
    mock_botocore.exceptions.BotoCoreError = MockBotoCoreError
    
    sys.modules['boto3'] = mock_boto3
    sys.modules['botocore'] = mock_botocore
    sys.modules['botocore.exceptions'] = mock_botocore.exceptions
    
    # Reload module to pick up mocked exceptions
    import importlib
    import cloudwatch_metrics
    importlib.reload(cloudwatch_metrics)
    
    from cloudwatch_metrics import CloudWatchMetrics
    
    mock_client = Mock()
    mock_client.put_metric_data.side_effect = MockClientError("AWS Error")
    mock_boto3.client.return_value = mock_client
    
    metrics = CloudWatchMetrics(enabled=True)
    metrics.put_metric("TestMetric", 1.0)
    
    # Flush should not raise exception
    try:
        metrics.flush()
        print("✅ Error handling works (no exception raised)")
    except Exception as e:
        assert False, f"Should not raise exception: {e}"
    
    # Buffer should be cleared even on error
    assert len(metrics.metric_buffer) == 0, "Buffer should be cleared after flush attempt"
    print("✅ Buffer cleared even on error")
    
    print("\n✅ All error handling tests passed!")
    return True


def run_all_tests():
    """Run all CloudWatch metrics tests"""
    print("\n" + "="*70)
    print("CLOUDWATCH METRICS TEST SUITE")
    print("="*70)
    
    tests = [
        ("CloudWatch Metrics Module", test_cloudwatch_metrics_module),
        ("CloudWatch Metrics with Mock AWS", test_cloudwatch_metrics_with_mock_aws),
        ("Convenience Functions", test_convenience_functions),
        ("Track Duration Decorator", test_track_duration_decorator),
        ("Async Flush", test_async_flush),
        ("Environment Detection", test_environment_detection),
        ("Metric Batching", test_metric_batching),
        ("Error Handling", test_error_handling),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"\n❌ {test_name} FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Total Tests: {len(tests)}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        return True
    else:
        print(f"\n⚠️  {failed} TEST(S) FAILED")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
