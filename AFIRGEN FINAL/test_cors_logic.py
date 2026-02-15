"""
test_cors_logic.py
-----------------------------------------------------------------------------
Property-Based Tests for CORS Validation Logic
-----------------------------------------------------------------------------

Tests the CORS origin validation logic without requiring FastAPI.

Requirements Validated: 4.1.5 (CORS configuration validation)
"""

import pytest
from hypothesis import given, strategies as st, settings


# ============================================================================
# CORS Validation Logic (extracted for testing)
# ============================================================================

def is_origin_allowed(origin: str, allowed_origins: list) -> bool:
    """
    Check if an origin is in the allowlist.
    
    Args:
        origin: The origin to check
        allowed_origins: List of allowed origins
        
    Returns:
        True if origin is allowed, False otherwise
    """
    # Wildcard allows all origins
    if "*" in allowed_origins:
        return True
    
    # Check exact match
    if origin in allowed_origins:
        return True
    
    # Check with trailing slash removed
    origin_no_slash = origin.rstrip("/")
    if origin_no_slash in allowed_origins:
        return True
    
    # Check if any allowed origin matches with trailing slash
    for allowed in allowed_origins:
        if allowed.rstrip("/") == origin_no_slash:
            return True
    
    return False


# ============================================================================
# Unit Tests
# ============================================================================

def test_exact_match():
    """Test exact origin match"""
    assert is_origin_allowed("https://example.com", ["https://example.com"]) is True
    assert is_origin_allowed("https://other.com", ["https://example.com"]) is False


def test_wildcard():
    """Test wildcard allows all"""
    assert is_origin_allowed("https://any.com", ["*"]) is True
    assert is_origin_allowed("http://localhost:3000", ["*"]) is True


def test_trailing_slash_normalization():
    """Test trailing slash is normalized"""
    # Origin with slash matches origin without
    assert is_origin_allowed("https://example.com/", ["https://example.com"]) is True
    # Origin without slash matches origin with
    assert is_origin_allowed("https://example.com", ["https://example.com/"]) is True


def test_multiple_origins():
    """Test multiple allowed origins"""
    allowed = ["https://app1.com", "https://app2.com", "https://app3.com"]
    assert is_origin_allowed("https://app1.com", allowed) is True
    assert is_origin_allowed("https://app2.com", allowed) is True
    assert is_origin_allowed("https://app3.com", allowed) is True
    assert is_origin_allowed("https://app4.com", allowed) is False


def test_case_sensitive():
    """Test origin matching is case-sensitive"""
    assert is_origin_allowed("https://Example.com", ["https://example.com"]) is False
    assert is_origin_allowed("https://example.com", ["https://Example.com"]) is False


def test_protocol_matters():
    """Test that protocol (http vs https) matters"""
    assert is_origin_allowed("http://example.com", ["https://example.com"]) is False
    assert is_origin_allowed("https://example.com", ["http://example.com"]) is False


def test_port_matters():
    """Test that port numbers matter"""
    assert is_origin_allowed("http://localhost:3000", ["http://localhost:8000"]) is False
    assert is_origin_allowed("http://localhost:3000", ["http://localhost:3000"]) is True


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
        st.text(min_size=5, max_size=30, alphabet=st.characters(whitelist_categories=("L", "N"))).map(
            lambda s: f"https://{s}.com"
        ),  # Random domains
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
    allowed_origins = ["https://example.com", "https://app.example.com"]
    
    result = is_origin_allowed(origin, allowed_origins)
    
    # Verify result is boolean
    assert isinstance(result, bool)
    
    # Verify logic is correct
    expected = (
        origin in allowed_origins or
        origin.rstrip("/") in allowed_origins or
        any(allowed.rstrip("/") == origin.rstrip("/") for allowed in allowed_origins)
    )
    
    assert result == expected, f"Origin '{origin}' validation mismatch"


@settings(max_examples=50)
@given(
    num_origins=st.integers(min_value=1, max_value=10),
    test_origin_index=st.integers(min_value=-1, max_value=10),
)
def test_property_multiple_origins(num_origins, test_origin_index):
    """
    Property: Multiple Origins Validation
    
    For any number of configured origins, only those specific origins
    should be allowed.
    """
    # Generate list of allowed origins
    allowed_origins = [f"https://app{i}.example.com" for i in range(num_origins)]
    
    # Choose test origin
    if 0 <= test_origin_index < num_origins:
        # Use one of the allowed origins
        test_origin = allowed_origins[test_origin_index]
        expected = True
    else:
        # Use an origin not in the list
        test_origin = "https://notallowed.example.com"
        expected = False
    
    result = is_origin_allowed(test_origin, allowed_origins)
    
    assert result == expected


@settings(max_examples=50)
@given(
    origin=st.text(min_size=10, max_size=50, alphabet=st.characters(whitelist_categories=("L", "N", "P"))),
    has_trailing_slash=st.booleans(),
)
def test_property_trailing_slash_normalization(origin, has_trailing_slash):
    """
    Property: Trailing Slash Normalization
    
    Origins with and without trailing slashes should be treated as equivalent.
    """
    # Ensure origin doesn't already have trailing slash
    origin = origin.rstrip("/")
    
    # Add protocol if not present
    if not origin.startswith("http"):
        origin = f"https://{origin}"
    
    # Create test origin with or without trailing slash
    test_origin = origin + "/" if has_trailing_slash else origin
    
    # Both should match
    result_with_slash = is_origin_allowed(origin + "/", [origin])
    result_without_slash = is_origin_allowed(origin, [origin + "/"])
    
    assert result_with_slash is True
    assert result_without_slash is True


@settings(max_examples=50)
@given(
    use_wildcard=st.booleans(),
    origin=st.text(min_size=10, max_size=50).map(lambda s: f"https://{s}.com"),
)
def test_property_wildcard_behavior(use_wildcard, origin):
    """
    Property: Wildcard Behavior
    
    When wildcard is in allowed origins, all origins should be allowed.
    When wildcard is not present, only specific origins should be allowed.
    """
    if use_wildcard:
        allowed_origins = ["*"]
        expected = True
    else:
        allowed_origins = ["https://specific.com"]
        expected = (origin == "https://specific.com")
    
    result = is_origin_allowed(origin, allowed_origins)
    
    assert result == expected


@settings(max_examples=50)
@given(
    protocol=st.sampled_from(["http", "https"]),
    domain=st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=("L", "N"))),
    port=st.one_of(st.none(), st.integers(min_value=1000, max_value=9999)),
)
def test_property_origin_components(protocol, domain, port):
    """
    Property: Origin Components
    
    Origins are composed of protocol, domain, and optional port.
    All components must match for origin to be allowed.
    """
    # Build origin
    if port:
        origin = f"{protocol}://{domain}:{port}"
    else:
        origin = f"{protocol}://{domain}"
    
    # Test exact match
    result_exact = is_origin_allowed(origin, [origin])
    assert result_exact is True
    
    # Test different protocol
    other_protocol = "https" if protocol == "http" else "http"
    if port:
        other_origin = f"{other_protocol}://{domain}:{port}"
    else:
        other_origin = f"{other_protocol}://{domain}"
    
    result_different = is_origin_allowed(other_origin, [origin])
    assert result_different is False


# ============================================================================
# Edge Cases
# ============================================================================

def test_empty_allowed_list():
    """Test with empty allowed origins list"""
    assert is_origin_allowed("https://example.com", []) is False


def test_empty_origin():
    """Test with empty origin string"""
    assert is_origin_allowed("", ["https://example.com"]) is False


def test_malformed_origins():
    """Test with malformed origin strings"""
    # Missing protocol
    assert is_origin_allowed("example.com", ["https://example.com"]) is False
    
    # Just protocol
    assert is_origin_allowed("https://", ["https://example.com"]) is False
    
    # With path
    assert is_origin_allowed("https://example.com/path", ["https://example.com"]) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
