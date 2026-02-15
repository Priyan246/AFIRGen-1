# Content Security Policy (CSP) Implementation

## Overview

This document describes the Content Security Policy (CSP) implementation for the AFIRGen frontend application. CSP is a security feature that helps prevent Cross-Site Scripting (XSS), clickjacking, and other code injection attacks.

**Requirements:** 5.3.6

## CSP Configuration

The CSP is configured via a meta tag in `index.html`:

```html
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; connect-src 'self' http://localhost:8000 https://*; img-src 'self' data: blob:; frame-ancestors 'none'; base-uri 'self'; form-action 'self';">
```

## Directive Breakdown

### `default-src 'self'`
- **Purpose:** Sets the default policy for all resource types
- **Value:** Only allow resources from the same origin
- **Security:** Prevents loading resources from external domains by default

### `script-src 'self' 'unsafe-inline'`
- **Purpose:** Controls which scripts can be executed
- **Value:** Allow scripts from same origin and inline scripts
- **Note:** `'unsafe-inline'` is used for inline event handlers and scripts. In production, consider using nonces or hashes for better security.

### `style-src 'self' 'unsafe-inline' https://fonts.googleapis.com`
- **Purpose:** Controls which stylesheets can be loaded
- **Value:** Allow styles from same origin, inline styles, and Google Fonts
- **Note:** `'unsafe-inline'` is needed for inline styles. Google Fonts is whitelisted for font loading.

### `font-src 'self' https://fonts.gstatic.com`
- **Purpose:** Controls which fonts can be loaded
- **Value:** Allow fonts from same origin and Google Fonts CDN
- **Security:** Restricts font loading to trusted sources

### `connect-src 'self' http://localhost:8000 https://*`
- **Purpose:** Controls which URLs can be loaded via fetch, XMLHttpRequest, WebSocket, etc.
- **Value:** Allow connections to same origin, localhost backend (development), and any HTTPS endpoint
- **Note:** In production, replace `https://*` with specific API domain (e.g., `https://api.afirgen.example.com`)

### `img-src 'self' data: blob:`
- **Purpose:** Controls which images can be loaded
- **Value:** Allow images from same origin, data URIs, and blob URIs
- **Use Case:** Supports base64-encoded images and dynamically generated images

### `frame-ancestors 'none'`
- **Purpose:** Controls which sites can embed this page in frames/iframes
- **Value:** Prevent all framing
- **Security:** Protects against clickjacking attacks

### `base-uri 'self'`
- **Purpose:** Controls which URLs can be used in the `<base>` element
- **Value:** Only allow same origin
- **Security:** Prevents base tag injection attacks

### `form-action 'self'`
- **Purpose:** Controls which URLs can be used as form submission targets
- **Value:** Only allow same origin
- **Security:** Prevents form hijacking attacks

## Security Functions

The `security.js` module provides functions for CSP enforcement and monitoring:

### `enforceCSP()`
Verifies that the CSP meta tag is properly configured with all required directives.

```javascript
function enforceCSP() {
  // Checks for CSP meta tag
  // Validates required directives
  // Logs warnings for missing directives
  // Returns true if CSP is enforced
}
```

### `reportCSPViolation(violation)`
Logs CSP violations for monitoring and debugging.

```javascript
function reportCSPViolation(violation) {
  // Captures violation details
  // Logs to console
  // Can be extended to send to logging service
}
```

### `initCSPMonitoring()`
Initializes CSP monitoring by setting up event listeners.

```javascript
function initCSPMonitoring() {
  // Listens for securitypolicyviolation events
  // Calls enforceCSP() on page load
  // Automatically initialized when security.js loads
}
```

## Testing

### Unit Tests
Location: `js/security-csp.test.js`

Tests cover:
- CSP directive validation
- Security properties
- Violation reporting structure
- Best practices compliance

Run tests:
```bash
npm test -- security-csp.test.js
```

### Browser Testing
Location: `test-csp.html`

Interactive test page that:
- Displays current CSP configuration
- Tests inline scripts (should work)
- Tests external scripts from same origin (should work)
- Tests inline styles (should work)
- Tests data URI images (should work)
- Tests fetch to same origin (should work)
- Captures and displays CSP violations in real-time

Open in browser:
```
http://localhost:8080/test-csp.html
```

## Monitoring CSP Violations

CSP violations are automatically logged to the browser console. In production, you can send these to a logging service:

```javascript
function reportCSPViolation(violation) {
  const violationDetails = {
    blockedURI: violation.blockedURI,
    violatedDirective: violation.violatedDirective,
    effectiveDirective: violation.effectiveDirective,
    originalPolicy: violation.originalPolicy,
    sourceFile: violation.sourceFile,
    lineNumber: violation.lineNumber,
    columnNumber: violation.columnNumber,
    timestamp: new Date().toISOString()
  };

  // Send to logging service
  fetch('/api/csp-report', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(violationDetails)
  });
}
```

## Production Recommendations

### 1. Remove `'unsafe-inline'`
Replace inline scripts and styles with external files, or use nonces/hashes:

```html
<!-- Generate a unique nonce per request -->
<meta http-equiv="Content-Security-Policy" content="script-src 'self' 'nonce-{random}';">
<script nonce="{random}">
  // Inline script
</script>
```

### 2. Restrict `connect-src`
Replace wildcard with specific API domain:

```
connect-src 'self' https://api.afirgen.example.com
```

### 3. Add `report-uri` or `report-to`
Configure CSP violation reporting:

```
report-uri /csp-report; report-to csp-endpoint
```

### 4. Use CSP Headers
Move CSP from meta tag to HTTP headers for better security:

```
Content-Security-Policy: default-src 'self'; ...
```

### 5. Test in Report-Only Mode
Before enforcing, test with `Content-Security-Policy-Report-Only`:

```html
<meta http-equiv="Content-Security-Policy-Report-Only" content="...">
```

## Browser Compatibility

CSP is supported in all modern browsers:
- Chrome 25+
- Firefox 23+
- Safari 7+
- Edge 12+
- Opera 15+

For older browsers, CSP is ignored gracefully (no errors).

## Resources

- [MDN: Content Security Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP)
- [CSP Evaluator](https://csp-evaluator.withgoogle.com/)
- [CSP Best Practices](https://web.dev/csp/)

## Changelog

### Version 1.0 (Current)
- Initial CSP implementation
- All required directives configured
- CSP enforcement and monitoring functions
- Unit tests and browser tests
- Documentation
