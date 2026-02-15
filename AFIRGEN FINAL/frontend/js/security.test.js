/**
 * Unit tests for security.js module
 * Tests sanitization functions for XSS prevention
 */

const { sanitizeHTML, sanitizeText, escapeHTML, sanitizeURL } = require('./security');

// Mock DOMPurify for testing
global.DOMPurify = {
  sanitize: (html) => {
    // Mock that removes dangerous tags and attributes
    let sanitized = html;
    // Remove script tags
    sanitized = sanitized.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
    // Remove iframe tags (including self-closing)
    sanitized = sanitized.replace(/<iframe\b[^<]*(?:(?!<\/iframe>)<[^<]*)*<\/iframe>/gi, '');
    sanitized = sanitized.replace(/<iframe[^>]*>/gi, '');
    // Remove svg tags
    sanitized = sanitized.replace(/<svg\b[^<]*(?:(?!<\/svg>)<[^<]*)*<\/svg>/gi, '');
    sanitized = sanitized.replace(/<svg[^>]*>/gi, '');
    // Remove body tags
    sanitized = sanitized.replace(/<body\b[^<]*(?:(?!<\/body>)<[^<]*)*<\/body>/gi, '');
    sanitized = sanitized.replace(/<body[^>]*>/gi, '');
    // Remove event handlers (onerror, onload, etc.)
    sanitized = sanitized.replace(/\s*on\w+\s*=\s*["'][^"']*["']/gi, '');
    sanitized = sanitized.replace(/\s*on\w+\s*=\s*[^\s>]*/gi, '');
    // Remove img tags with event handlers
    sanitized = sanitized.replace(/<img[^>]*on\w+[^>]*>/gi, '');
    return sanitized;
  }
};

describe('Security Module', () => {
  describe('sanitizeHTML', () => {
    test('should remove script tags from HTML', () => {
      const input = '<script>alert("XSS")</script><p>Hello</p>';
      const result = sanitizeHTML(input);
      expect(result).not.toContain('<script>');
      expect(result).toContain('<p>Hello</p>');
    });

    test('should handle non-string input', () => {
      expect(sanitizeHTML(null)).toBe('');
      expect(sanitizeHTML(undefined)).toBe('');
      expect(sanitizeHTML(123)).toBe('');
      expect(sanitizeHTML({})).toBe('');
    });

    test('should handle empty string', () => {
      expect(sanitizeHTML('')).toBe('');
    });

    test('should preserve safe HTML tags', () => {
      const input = '<p>Hello <strong>World</strong></p>';
      const result = sanitizeHTML(input);
      expect(result).toContain('<p>');
      expect(result).toContain('<strong>');
    });

    test('should fallback to escapeHTML when DOMPurify is not available', () => {
      const originalDOMPurify = global.DOMPurify;
      global.DOMPurify = undefined;

      const input = '<script>alert("XSS")</script>';
      const result = sanitizeHTML(input);
      expect(result).toContain('&lt;script&gt;');

      global.DOMPurify = originalDOMPurify;
    });
  });

  describe('sanitizeText', () => {
    test('should remove control characters', () => {
      const input = 'Hello\x00World\x01Test';
      const result = sanitizeText(input);
      expect(result).toBe('HelloWorldTest');
    });

    test('should preserve newlines and tabs', () => {
      const input = 'Hello\nWorld\tTest';
      const result = sanitizeText(input);
      expect(result).toBe('Hello\nWorld\tTest');
    });

    test('should trim whitespace', () => {
      const input = '  Hello World  ';
      const result = sanitizeText(input);
      expect(result).toBe('Hello World');
    });

    test('should limit length to maxLength', () => {
      const input = 'a'.repeat(15000);
      const result = sanitizeText(input, { maxLength: 10000 });
      expect(result.length).toBe(10000);
    });

    test('should use default maxLength of 10000', () => {
      const input = 'a'.repeat(15000);
      const result = sanitizeText(input);
      expect(result.length).toBe(10000);
    });

    test('should handle non-string input', () => {
      expect(sanitizeText(null)).toBe('');
      expect(sanitizeText(undefined)).toBe('');
      expect(sanitizeText(123)).toBe('');
      expect(sanitizeText({})).toBe('');
    });

    test('should handle empty string', () => {
      expect(sanitizeText('')).toBe('');
    });
  });

  describe('escapeHTML', () => {
    test('should escape HTML special characters', () => {
      const input = '<script>alert("XSS")</script>';
      const result = escapeHTML(input);
      expect(result).toBe(
        '&lt;script&gt;alert(&quot;XSS&quot;)&lt;&#x2F;script&gt;'
      );
    });

    test('should escape ampersands', () => {
      const input = 'Tom & Jerry';
      const result = escapeHTML(input);
      expect(result).toBe('Tom &amp; Jerry');
    });

    test('should escape quotes', () => {
      const input = 'He said "Hello" and \'Goodbye\'';
      const result = escapeHTML(input);
      expect(result).toBe('He said &quot;Hello&quot; and &#x27;Goodbye&#x27;');
    });

    test('should escape forward slashes', () => {
      const input = '</script>';
      const result = escapeHTML(input);
      expect(result).toBe('&lt;&#x2F;script&gt;');
    });

    test('should handle non-string input', () => {
      expect(escapeHTML(null)).toBe('');
      expect(escapeHTML(undefined)).toBe('');
      expect(escapeHTML(123)).toBe('');
      expect(escapeHTML({})).toBe('');
    });

    test('should handle empty string', () => {
      expect(escapeHTML('')).toBe('');
    });

    test('should handle text without special characters', () => {
      const input = 'Hello World';
      const result = escapeHTML(input);
      expect(result).toBe('Hello World');
    });
  });

  describe('sanitizeURL', () => {
    test('should accept valid HTTP URLs', () => {
      const input = 'http://example.com';
      const result = sanitizeURL(input);
      expect(result).toBe('http://example.com/');
    });

    test('should accept valid HTTPS URLs', () => {
      const input = 'https://example.com/path?query=value';
      const result = sanitizeURL(input);
      expect(result).toBe('https://example.com/path?query=value');
    });

    test('should reject javascript: protocol', () => {
      // eslint-disable-next-line no-script-url
      const input = 'javascript:alert("XSS")';
      const result = sanitizeURL(input);
      expect(result).toBeNull();
    });

    test('should reject data: protocol', () => {
      const input = 'data:text/html,<script>alert("XSS")</script>';
      const result = sanitizeURL(input);
      expect(result).toBeNull();
    });

    test('should reject file: protocol', () => {
      const input = 'file:///etc/passwd';
      const result = sanitizeURL(input);
      expect(result).toBeNull();
    });

    test('should handle invalid URLs', () => {
      expect(sanitizeURL('not a url')).toBeNull();
      expect(sanitizeURL('htp://invalid')).toBeNull();
    });

    test('should handle non-string input', () => {
      expect(sanitizeURL(null)).toBeNull();
      expect(sanitizeURL(undefined)).toBeNull();
      expect(sanitizeURL(123)).toBeNull();
      expect(sanitizeURL({})).toBeNull();
    });

    test('should handle empty string', () => {
      expect(sanitizeURL('')).toBeNull();
      expect(sanitizeURL('   ')).toBeNull();
    });

    test('should accept custom allowed protocols', () => {
      const input = 'ftp://example.com';
      const result = sanitizeURL(input, ['ftp:']);
      expect(result).toBe('ftp://example.com/');
    });

    test('should reject URLs not in custom allowed protocols', () => {
      const input = 'http://example.com';
      const result = sanitizeURL(input, ['ftp:']);
      expect(result).toBeNull();
    });
  });

  describe('XSS Prevention', () => {
    test('should prevent common XSS attacks with sanitizeHTML', () => {
      const xssPayloads = [
        '<script>alert("XSS")</script>',
        '<img src=x onerror=alert("XSS")>',
        '<svg onload=alert("XSS")>',
        '<iframe src="javascript:alert(\'XSS\')">',
        '<body onload=alert("XSS")>'
      ];

      xssPayloads.forEach((payload) => {
        const result = sanitizeHTML(payload);
        expect(result).not.toContain('alert');
        expect(result).not.toContain('onerror');
        expect(result).not.toContain('onload');
      });
    });

    test('should prevent XSS attacks with escapeHTML', () => {
      const xssPayloads = [
        '<script>alert("XSS")</script>',
        '<img src=x onerror=alert("XSS")>',
        '"><script>alert("XSS")</script>'
      ];

      xssPayloads.forEach((payload) => {
        const result = escapeHTML(payload);
        expect(result).not.toContain('<script>');
        expect(result).not.toContain('<img');
        expect(result).toContain('&lt;');
        expect(result).toContain('&gt;');
      });
    });
  });
});
