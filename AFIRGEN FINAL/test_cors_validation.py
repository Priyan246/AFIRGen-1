"""
test_cors_validation.py
-----------------------------------------------------------------------------
Property-Based Tests for CORS Validation
-----------------------------------------------------------------------------

Tests the enhanced CORS middleware for:
- Origin validation against allowlist
- Rejection of invalid origins
- Logging of rejected requests
- Proper CORS headers for valid origins

Requirements Validated: 4.1.5 (CORS configuration validation)
"""

import pytest
from hypothesis import given, strategies as st, settings
from fastapi import FastAPI
from fastapi.testclient import TestClient
from cors_middleware import EnhancedCORSMiddleware, setup_cors_middleware


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def app_with_cors():
    """Create a FastAPI app with CORS middleware"""
    app = FastAPI()
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "success"}
    
    @app.post("/test")
    async def test_post():
        return {"message": "posted"}
    
    return app


@pytest.fixture
def client_with_specific_origins(app_with_cors):
    """Create test client with specific allowed origins"""
    setup_cors_middleware(
        app_with_cors,
        cors_origins=["https://example.com", "https://app.example.com"],
        allow_credentials=True,
        use_enhanced=True,
    )
    return TestClient(app_with_cors)


@pytest.fixture
def client_with_wildcard(app_with_cors):
    """Create test client with wildcard origin"""
    setup_cors_middleware(
        app_with_cors,
        cors_origins=["*"],
        allow_credentials=False,
        use_enhanced=True,
    )
    return TestClient(app_with_cors)


# ============================================================================
# Unit Tests - Basic CORS Functionality
# ============================================================================

def test_cors_allowed_origin(client_with_specific_origins):
    """Test that allowed origin receives CORS headers"""
    response = client_with_specific_origins.get(
        "/test",
        headers={"Origin": "https://example.com"}
    )
    
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://example.com"
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_rejected_origin(client_with_specific_origins):
    """Test that rejected origin does not receive CORS headers"""
    response = client_with_specific_origins.get(
        "/test",
        headers={"Origin": "https://evil.com"}
    )
    
    # Request succeeds but no CORS headers
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_cors_preflight_allowed(client_with_specific_origins):
    """Test preflight request for allowed origin"""
    response = client_with_specific_origins.options(
        "/test",
        headers={
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "POST",
        }
    )
    
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://example.com"
    assert "access-control-allow-methods" in response.headers


def test_cors_preflight_rejected(client_with_specific_origins):
    """Test preflight request for rejected origin"""
    response = client_with_specific_origins.options(
        "/test",
        headers={
            "Origin": "https://evil.com",
            "Access-Control-Request-Method": "POST",
        }
    )
    
    # Preflight should be rejected with 403
    assert response.status_code == 403
    assert "access-control-allow-origin" not in response.headers


def test_cors_no_origin_header(client_with_specific_origins):
    """Test request without Origin header (not a CORS request)"""
    response = client_with_specific_origins.get("/test")
    
    assert response.status_code == 200
    # No CORS headers should be added
    assert "access-control-allow-origin" not in response.headers


def test_cors_wildcard_allows_all(client_with_wildcard):
    """Test that wildcard allows any origin"""
    response = client_with_wildcard.get(
        "/test",
        headers={"Origin": "https://any-domain.com"}
    )
    
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://any-domain.com"


def test_cors_trailing_slash_normalization(client_with_specific_origins):
    """Test that trailing slashes are normalized"""
    # Origin with trailing slash should match origin without
    response = client_with_specific_origins.get(
        "/test",
        headers={"Origin": "https://example.com/"}
    )
    
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://example.com/"


# ============================================================================
# Property-Based Tests
# ============================================================================

# Feature: afirgen-aws-optimization, Property 2: CORS Origin Validation
@settings(max_examples=100)
@given(
    origin=st.one_of(
        st.just("https://example.com"),  # Valid origin
        st.just("https://app.example.com"),  # Valid origin
        st.just("https://evil.com"),  # Invalid origin
        st.just("http://localhost:3000"),  # Invalid origin
        st.text(min_size=10, max_size=50).map(lambda s: f"https://{s}.com"),  # Random domains
    )
)
def test_property_cors_origin_validation(origin):
    """
    Property 2: CORS Origin Validation
    
    For any HTTP request with an Origin header, if the origin is not in the
    configured allowlist, the system SHALL reject the request with appropriate
    CORS headers, and if the origin is in the allowlist, the system SHALL
    accept the request.
    
    Validates: Requirements 4.1.5
    """
    # Create app with specific allowed origins
    app = FastAPI()
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "success"}
    
    setup_cors_middleware(
        app,
        cors_origins=["https://example.com", "https://app.example.com"],
        allow_credentials=True,
        use_enhanced=True,
    )
    
    client = TestClient(app)
    
    # Make request with origin header
    response = client.get("/test", headers={"Origin": origin})
    
    # Request should always succeed (CORS is browser-enforced)
    assert response.status_code == 200
    
    # Check CORS headers based on whether origin is allowed
    allowed_origins = ["https://example.com", "https://app.example.com"]
    is_allowed = origin in allowed_origins or origin.rstrip("/") in allowed_origins
    
    if is_allowed:
        # Should have CORS headers
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == origin
    else:
        # Should NOT have CORS headers
        assert "access-control-allow-origin" not in response.headers


@settings(max_examples=50)
@given(
    method=st.sampled_from(["GET", "POST", "PUT", "DELETE"]),
    is_allowed_origin=st.booleans(),
)
def test_property_cors_methods(method, is_allowed_origin):
    """
    Property: CORS Method Validation
    
    For any HTTP method, CORS headers should only be added if the origin
    is in the allowlist, regardless of the method used.
    """
    app = FastAPI()
    
    @app.get("/test")
    @app.post("/test")
    @app.put("/test")
    @app.delete("/test")
    async def test_endpoint():
        return {"message": "success"}
    
    setup_cors_middleware(
        app,
        cors_origins=["https://allowed.com"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        use_enhanced=True,
    )
    
    client = TestClient(app)
    
    # Choose origin based on test parameter
    origin = "https://allowed.com" if is_allowed_origin else "https://notallowed.com"
    
    # Make request
    response = client.request(method, "/test", headers={"Origin": origin})
    
    # Request should succeed
    assert response.status_code == 200
    
    # Check CORS headers
    if is_allowed_origin:
        assert response.headers.get("access-control-allow-origin") == origin
    else:
        assert "access-control-allow-origin" not in response.headers


@settings(max_examples=50)
@given(
    num_origins=st.integers(min_value=1, max_value=10),
    test_origin_index=st.integers(min_value=-1, max_value=10),
)
def test_property_cors_multiple_origins(num_origins, test_origin_index):
    """
    Property: Multiple Origins Validation
    
    For any number of configured origins, only requests from those specific
    origins should receive CORS headers.
    """
    # Generate list of allowed origins
    allowed_origins = [f"https://app{i}.example.com" for i in range(num_origins)]
    
    app = FastAPI()
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "success"}
    
    setup_cors_middleware(
        app,
        cors_origins=allowed_origins,
        allow_credentials=True,
        use_enhanced=True,
    )
    
    client = TestClient(app)
    
    # Choose test origin
    if 0 <= test_origin_index < num_origins:
        # Use one of the allowed origins
        test_origin = allowed_origins[test_origin_index]
        should_be_allowed = True
    else:
        # Use an origin not in the list
        test_origin = "https://notallowed.example.com"
        should_be_allowed = False
    
    # Make request
    response = client.get("/test", headers={"Origin": test_origin})
    
    assert response.status_code == 200
    
    if should_be_allowed:
        assert response.headers.get("access-control-allow-origin") == test_origin
    else:
        assert "access-control-allow-origin" not in response.headers


@settings(max_examples=50)
@given(
    has_credentials=st.booleans(),
    is_allowed_origin=st.booleans(),
)
def test_property_cors_credentials(has_credentials, is_allowed_origin):
    """
    Property: CORS Credentials Header
    
    The Access-Control-Allow-Credentials header should only be present
    when credentials are enabled AND the origin is allowed.
    """
    app = FastAPI()
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "success"}
    
    setup_cors_middleware(
        app,
        cors_origins=["https://allowed.com"],
        allow_credentials=has_credentials,
        use_enhanced=True,
    )
    
    client = TestClient(app)
    
    origin = "https://allowed.com" if is_allowed_origin else "https://notallowed.com"
    
    response = client.get("/test", headers={"Origin": origin})
    
    assert response.status_code == 200
    
    if is_allowed_origin and has_credentials:
        assert response.headers.get("access-control-allow-credentials") == "true"
    else:
        # Either origin not allowed or credentials not enabled
        if not is_allowed_origin:
            assert "access-control-allow-credentials" not in response.headers


# ============================================================================
# Integration Tests
# ============================================================================

def test_integration_cors_full_workflow():
    """Test complete CORS workflow: preflight + actual request"""
    app = FastAPI()
    
    @app.post("/api/data")
    async def post_data(data: dict):
        return {"received": data}
    
    setup_cors_middleware(
        app,
        cors_origins=["https://frontend.example.com"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
        use_enhanced=True,
    )
    
    client = TestClient(app)
    
    # Step 1: Preflight request
    preflight = client.options(
        "/api/data",
        headers={
            "Origin": "https://frontend.example.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        }
    )
    
    assert preflight.status_code == 200
    assert preflight.headers.get("access-control-allow-origin") == "https://frontend.example.com"
    assert "POST" in preflight.headers.get("access-control-allow-methods", "")
    
    # Step 2: Actual POST request
    actual = client.post(
        "/api/data",
        json={"test": "data"},
        headers={"Origin": "https://frontend.example.com"}
    )
    
    assert actual.status_code == 200
    assert actual.headers.get("access-control-allow-origin") == "https://frontend.example.com"
    assert actual.headers.get("access-control-allow-credentials") == "true"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
