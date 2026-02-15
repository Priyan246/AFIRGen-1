/**
 * Security Module
 * Provides client-side security measures including input sanitization and XSS prevention
 * Requirements: 5.3.1
 */

/**
 * Sanitize HTML content using DOMPurify
 * Removes potentially dangerous HTML tags and attributes to prevent XSS attacks
 *
 * @param {string} html - The HTML string to sanitize
 * @returns {string} - Sanitized HTML safe for rendering
 *
 * @example
 * const userInput = '<script>alert("XSS")</script><p>Hello</p>';
 * const safe = sanitizeHTML(userInput); // Returns: '<p>Hello</p>'
 */
function sanitizeHTML(html) {
  if (typeof html !== 'string') {
    return '';
  }

  // Check if DOMPurify is available
  if (typeof DOMPurify === 'undefined') {
    console.error('DOMPurify library not loaded');
    return escapeHTML(html); // Fallback to basic escaping
  }

  // Configure DOMPurify to allow only safe tags
  const config = {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'p', 'br', 'span', 'div'],
    ALLOWED_ATTR: ['class'],
    KEEP_CONTENT: true,
    RETURN_DOM: false,
    RETURN_DOM_FRAGMENT: false
  };

  return DOMPurify.sanitize(html, config);
}

/**
 * Sanitize plain text input
 * Removes control characters and limits length to prevent DoS
 *
 * @param {string} text - The text to sanitize
 * @param {Object} options - Sanitization options
 * @param {number} options.maxLength - Maximum allowed length (default: 10000)
 * @returns {string} - Sanitized text
 *
 * @example
 * const userInput = 'Hello\x00World';
 * const safe = sanitizeText(userInput); // Returns: 'HelloWorld'
 */
function sanitizeText(text, options = {}) {
  if (typeof text !== 'string') {
    return '';
  }

  const { maxLength = 10000 } = options;

  // Remove control characters (except newline, tab, carriage return)
  // eslint-disable-next-line no-control-regex
  let sanitized = text.replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, '');

  // Limit length to prevent DoS
  if (sanitized.length > maxLength) {
    sanitized = sanitized.substring(0, maxLength);
  }

  // Trim whitespace
  sanitized = sanitized.trim();

  return sanitized;
}

/**
 * Escape HTML entities
 * Converts special characters to HTML entities to prevent XSS
 *
 * @param {string} str - The string to escape
 * @returns {string} - Escaped string safe for HTML rendering
 *
 * @example
 * const userInput = '<script>alert("XSS")</script>';
 * const safe = escapeHTML(userInput);
 * // Returns: '&lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;'
 */
function escapeHTML(str) {
  if (typeof str !== 'string') {
    return '';
  }

  const htmlEscapeMap = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#x27;',
    '/': '&#x2F;'
  };

  return str.replace(/[&<>"'/]/g, (char) => htmlEscapeMap[char]);
}

/**
 * Validate and sanitize URL
 * Ensures URL is safe and uses allowed protocols
 *
 * @param {string} url - The URL to validate
 * @param {Array<string>} allowedProtocols - Allowed protocols (default: ['http:', 'https:'])
 * @returns {string|null} - Sanitized URL or null if invalid
 *
 * @example
 * const url = 'javascript:alert("XSS")';
 * const safe = sanitizeURL(url); // Returns: null
 */
function sanitizeURL(url, allowedProtocols = ['http:', 'https:']) {
  if (typeof url !== 'string' || !url.trim()) {
    return null;
  }

  try {
    const parsed = new URL(url);

    // Check if protocol is allowed
    if (!allowedProtocols.includes(parsed.protocol)) {
      return null;
    }

    return parsed.href;
  } catch (e) {
    // Invalid URL
    return null;
  }
}

// Export functions for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    sanitizeHTML,
    sanitizeText,
    escapeHTML,
    sanitizeURL
  };
}

/**
 * Enforce Content Security Policy
 * Verifies that CSP is properly configured and active
 * Requirements: 5.3.6
 *
 * @returns {boolean} - True if CSP is enforced, false otherwise
 */
function enforceCSP() {
  // Check if CSP meta tag exists
  const cspMeta = document.querySelector('meta[http-equiv="Content-Security-Policy"]');

  if (!cspMeta) {
    console.error('CSP meta tag not found in document');
    return false;
  }

  const cspContent = cspMeta.getAttribute('content');

  if (!cspContent) {
    console.error('CSP meta tag has no content');
    return false;
  }

  // Verify required directives are present
  const requiredDirectives = [
    'default-src',
    'script-src',
    'style-src',
    'font-src',
    'connect-src',
    'img-src',
    'frame-ancestors',
    'base-uri',
    'form-action'
  ];

  const missingDirectives = requiredDirectives.filter(
    directive => !cspContent.includes(directive)
  );

  if (missingDirectives.length > 0) {
    console.warn('CSP missing directives:', missingDirectives);
  }

  console.log('CSP enforced:', cspContent);
  return true;
}

/**
 * Report CSP violation
 * Logs CSP violations for monitoring and debugging
 * Requirements: 5.3.6
 *
 * @param {SecurityPolicyViolationEvent} violation - The CSP violation event
 */
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

  console.error('CSP Violation:', violationDetails);

  // In production, you would send this to a logging service
  // Example: sendToLoggingService(violationDetails);
}

/**
 * Initialize CSP monitoring
 * Sets up event listener for CSP violations
 * Requirements: 5.3.6
 */
function initCSPMonitoring() {
  // Listen for CSP violations
  document.addEventListener('securitypolicyviolation', reportCSPViolation);

  // Verify CSP is enforced on page load
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', enforceCSP);
  } else {
    enforceCSP();
  }
}

// Initialize CSP monitoring when script loads
if (typeof window !== 'undefined') {
  initCSPMonitoring();
}
