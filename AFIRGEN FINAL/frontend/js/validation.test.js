/**
 * Unit tests for validation.js
 * Requirements: 5.3.2, 5.3.3
 */

// Mock DOM APIs needed by validation.js
global.document = {
  createElement: (tag) => ({
    textContent: '',
    get innerHTML() {
      return this.textContent
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
    }
  })
};

// Mock window object
global.window = {};

// Load the validation module
require('./validation.js');

// Extract the functions from window.Validation
const {
  validateFile,
  validateFileType,
  validateFileSize,
  validateMimeType,
  validateText,
  sanitizeInput,
  validateForm
} = window.Validation;

describe('Validation Module', () => {
  describe('validateFileSize', () => {
    test('should accept file within size limit', () => {
      const file = new File(['a'.repeat(1024)], 'test.txt', { type: 'text/plain' });
      const result = validateFileSize(file, 10 * 1024 * 1024);
      expect(result.success).toBe(true);
    });

    test('should reject file exceeding size limit', () => {
      const file = new File(['a'.repeat(11 * 1024 * 1024)], 'large.txt', { type: 'text/plain' });
      const result = validateFileSize(file, 10 * 1024 * 1024);
      expect(result.success).toBe(false);
      expect(result.error).toContain('exceeds maximum allowed size');
    });

    test('should reject null file', () => {
      const result = validateFileSize(null);
      expect(result.success).toBe(false);
      expect(result.error).toBe('No file provided');
    });

    test('should use default max size of 10MB', () => {
      const file = new File(['a'.repeat(11 * 1024 * 1024)], 'large.txt', { type: 'text/plain' });
      const result = validateFileSize(file);
      expect(result.success).toBe(false);
    });
  });

  describe('validateFileType', () => {
    test('should accept file with allowed extension', () => {
      const file = new File(['content'], 'test.jpg', { type: 'image/jpeg' });
      const result = validateFileType(file, ['.jpg', '.png']);
      expect(result.success).toBe(true);
    });

    test('should reject file with disallowed extension', () => {
      const file = new File(['content'], 'test.exe', { type: 'application/x-msdownload' });
      const result = validateFileType(file, ['.jpg', '.png']);
      expect(result.success).toBe(false);
      expect(result.error).toContain('File type not allowed');
    });

    test('should be case insensitive', () => {
      const file = new File(['content'], 'test.JPG', { type: 'image/jpeg' });
      const result = validateFileType(file, ['.jpg']);
      expect(result.success).toBe(true);
    });

    test('should use default allowed types', () => {
      const file = new File(['content'], 'test.jpg', { type: 'image/jpeg' });
      const result = validateFileType(file);
      expect(result.success).toBe(true);
    });

    test('should accept all whitelisted types', () => {
      const allowedTypes = ['.jpg', '.jpeg', '.png', '.pdf', '.wav', '.mp3'];
      allowedTypes.forEach(ext => {
        const file = new File(['content'], `test${ext}`, { type: 'application/octet-stream' });
        const result = validateFileType(file, allowedTypes);
        expect(result.success).toBe(true);
      });
    });

    test('should reject null file', () => {
      const result = validateFileType(null);
      expect(result.success).toBe(false);
      expect(result.error).toBe('No file provided');
    });
  });

  describe('validateMimeType', () => {
    // Helper to create a file with specific bytes
    const createFileWithBytes = (bytes, name, type) => {
      const file = new File([new Uint8Array(bytes)], name, { type });
      // Mock the slice and arrayBuffer methods for jsdom
      file.slice = jest.fn((start, end) => {
        const slicedBytes = bytes.slice(start, end);
        return {
          arrayBuffer: jest.fn(() => Promise.resolve(new Uint8Array(slicedBytes).buffer))
        };
      });
      return file;
    };

    test('should validate JPEG magic number', async () => {
      const file = createFileWithBytes(
        [0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46],
        'test.jpg',
        'image/jpeg'
      );

      const result = await validateMimeType(file);
      expect(result.success).toBe(true);
      expect(result.mimeType).toBe('image/jpeg');
    });

    test('should validate PNG magic number', async () => {
      const file = createFileWithBytes(
        [0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A],
        'test.png',
        'image/png'
      );

      const result = await validateMimeType(file);
      expect(result.success).toBe(true);
      expect(result.mimeType).toBe('image/png');
    });

    test('should validate PDF magic number', async () => {
      const file = createFileWithBytes(
        [0x25, 0x50, 0x44, 0x46, 0x2D, 0x31, 0x2E, 0x34],
        'test.pdf',
        'application/pdf'
      );

      const result = await validateMimeType(file);
      expect(result.success).toBe(true);
      expect(result.mimeType).toBe('application/pdf');
    });

    test('should validate WAV magic number', async () => {
      const file = createFileWithBytes(
        [0x52, 0x49, 0x46, 0x46, 0x00, 0x00, 0x00, 0x00],
        'test.wav',
        'audio/wav'
      );

      const result = await validateMimeType(file);
      expect(result.success).toBe(true);
      expect(result.mimeType).toBe('audio/wav');
    });

    test('should validate MP3 magic number (ID3)', async () => {
      const file = createFileWithBytes(
        [0x49, 0x44, 0x33, 0x03, 0x00, 0x00, 0x00, 0x00],
        'test.mp3',
        'audio/mpeg'
      );

      const result = await validateMimeType(file);
      expect(result.success).toBe(true);
      expect(result.mimeType).toBe('audio/mpeg');
    });

    test('should reject file with invalid magic number', async () => {
      const file = createFileWithBytes(
        [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
        'test.bin',
        'application/octet-stream'
      );

      const result = await validateMimeType(file);
      expect(result.success).toBe(false);
      expect(result.error).toContain('File type could not be verified');
    });

    test('should reject null file', async () => {
      const result = await validateMimeType(null);
      expect(result.success).toBe(false);
      expect(result.error).toBe('No file provided');
    });
  });

  describe('validateFile', () => {
    // Helper to create a file with specific bytes
    const createFileWithBytes = (bytes, name, type) => {
      const file = new File([new Uint8Array(bytes)], name, { type });
      // Mock the slice and arrayBuffer methods for jsdom
      file.slice = jest.fn((start, end) => {
        const slicedBytes = bytes.slice(start, end);
        return {
          arrayBuffer: jest.fn(() => Promise.resolve(new Uint8Array(slicedBytes).buffer))
        };
      });
      return file;
    };

    test('should validate file with all checks passing', async () => {
      const file = createFileWithBytes(
        [0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46],
        'test.jpg',
        'image/jpeg'
      );

      const result = await validateFile(file);
      expect(result.success).toBe(true);
    });

    test('should reject file exceeding size limit', async () => {
      const largeContent = new Array(11 * 1024 * 1024).fill(0);
      const file = createFileWithBytes(largeContent, 'large.jpg', 'image/jpeg');

      const result = await validateFile(file);
      expect(result.success).toBe(false);
      expect(result.error).toContain('exceeds maximum allowed size');
    });

    test('should reject file with invalid extension', async () => {
      const file = createFileWithBytes(
        [0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46],
        'test.exe',
        'application/x-msdownload'
      );

      const result = await validateFile(file);
      expect(result.success).toBe(false);
      expect(result.error).toContain('File type not allowed');
    });

    test('should reject file with invalid MIME type', async () => {
      const file = createFileWithBytes(
        [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
        'test.jpg',
        'application/octet-stream'
      );

      const result = await validateFile(file);
      expect(result.success).toBe(false);
      expect(result.error).toContain('File type could not be verified');
    });

    test('should skip MIME type check when checkMimeType is false', async () => {
      const file = createFileWithBytes(
        [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
        'test.jpg',
        'application/octet-stream'
      );

      const result = await validateFile(file, { checkMimeType: false });
      expect(result.success).toBe(true);
    });

    test('should accept custom options', async () => {
      const file = createFileWithBytes(
        [0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46],
        'test.jpg',
        'image/jpeg'
      );

      const result = await validateFile(file, {
        maxSize: 1024 * 1024, // 1MB
        allowedTypes: ['.jpg', '.png']
      });
      expect(result.success).toBe(true);
    });

    test('should reject null file', async () => {
      const result = await validateFile(null);
      expect(result.success).toBe(false);
      expect(result.error).toBe('No file provided');
    });
  });

  describe('validateText', () => {
    test('should accept valid text', () => {
      const result = validateText('Valid text');
      expect(result.success).toBe(true);
    });

    test('should reject empty text when required', () => {
      const result = validateText('', { required: true });
      expect(result.success).toBe(false);
      expect(result.error).toBe('Text is required');
    });

    test('should accept empty text when not required', () => {
      const result = validateText('', { required: false });
      expect(result.success).toBe(true);
    });

    test('should reject text below minimum length', () => {
      const result = validateText('ab', { minLength: 5 });
      expect(result.success).toBe(false);
      expect(result.error).toContain('at least 5 characters');
    });

    test('should reject text exceeding maximum length', () => {
      const result = validateText('a'.repeat(101), { maxLength: 100 });
      expect(result.success).toBe(false);
      expect(result.error).toContain('must not exceed 100 characters');
    });

    test('should validate email format', () => {
      expect(validateText('test@example.com', { format: 'email' }).success).toBe(true);
      expect(validateText('invalid-email', { format: 'email' }).success).toBe(false);
      expect(validateText('test@', { format: 'email' }).success).toBe(false);
      expect(validateText('@example.com', { format: 'email' }).success).toBe(false);
    });

    test('should validate phone format', () => {
      expect(validateText('1234567890', { format: 'phone' }).success).toBe(true);
      expect(validateText('+1-234-567-8900', { format: 'phone' }).success).toBe(true);
      expect(validateText('(123) 456-7890', { format: 'phone' }).success).toBe(true);
      expect(validateText('123', { format: 'phone' }).success).toBe(false);
      expect(validateText('abc', { format: 'phone' }).success).toBe(false);
    });

    test('should validate alphanumeric format', () => {
      expect(validateText('abc123', { format: 'alphanumeric' }).success).toBe(true);
      expect(validateText('abc 123', { format: 'alphanumeric' }).success).toBe(true);
      expect(validateText('abc-123', { format: 'alphanumeric' }).success).toBe(false);
      expect(validateText('abc@123', { format: 'alphanumeric' }).success).toBe(false);
    });

    test('should validate numeric format', () => {
      expect(validateText('12345', { format: 'numeric' }).success).toBe(true);
      expect(validateText('123abc', { format: 'numeric' }).success).toBe(false);
      expect(validateText('12.34', { format: 'numeric' }).success).toBe(false);
    });

    test('should validate alpha format', () => {
      expect(validateText('abcdef', { format: 'alpha' }).success).toBe(true);
      expect(validateText('abc def', { format: 'alpha' }).success).toBe(true);
      expect(validateText('abc123', { format: 'alpha' }).success).toBe(false);
    });

    test('should validate custom pattern', () => {
      const pattern = /^[A-Z]{3}-\d{3}$/;
      expect(validateText('ABC-123', { pattern }).success).toBe(true);
      expect(validateText('abc-123', { pattern }).success).toBe(false);
      expect(validateText('ABC-12', { pattern }).success).toBe(false);
    });

    test('should reject special characters when noSpecialChars is true', () => {
      expect(validateText('normal text', { noSpecialChars: true }).success).toBe(true);
      expect(validateText('text<script>', { noSpecialChars: true }).success).toBe(false);
      expect(validateText('text&more', { noSpecialChars: true }).success).toBe(false);
      expect(validateText('text"quote', { noSpecialChars: true }).success).toBe(false);
    });

    test('should handle unknown format', () => {
      const result = validateText('test', { format: 'unknown' });
      expect(result.success).toBe(false);
      expect(result.error).toContain('Unknown format');
    });
  });

  describe('sanitizeInput', () => {
    test('should escape HTML entities', () => {
      const result = sanitizeInput('<script>alert("XSS")</script>');
      expect(result).not.toContain('<script>');
      expect(result).toContain('&lt;script&gt;');
    });

    test('should handle empty input', () => {
      const result = sanitizeInput('');
      expect(result).toBe('');
    });

    test('should handle null input', () => {
      const result = sanitizeInput(null);
      expect(result).toBe('');
    });

    test('should escape special characters', () => {
      const result = sanitizeInput('<>&"\'');
      expect(result).toContain('&lt;');
      expect(result).toContain('&gt;');
      expect(result).toContain('&amp;');
      expect(result).toContain('&quot;');
      expect(result).toContain('&#039;');
    });

    test('should trim whitespace by default', () => {
      const result = sanitizeInput('  text  ');
      expect(result).toBe('text');
    });

    test('should not trim whitespace when option is false', () => {
      const result = sanitizeInput('  text  ', { trimWhitespace: false });
      expect(result).toBe('  text  ');
    });

    test('should remove control characters', () => {
      const result = sanitizeInput('text\x00\x01\x02');
      expect(result).toBe('text');
    });

    test('should preserve newlines and tabs', () => {
      const result = sanitizeInput('line1\nline2\ttab', { stripTags: false, escapeQuotes: false });
      expect(result).toContain('\n');
      expect(result).toContain('\t');
    });

    test('should not escape quotes when option is false', () => {
      const result = sanitizeInput('"test"', { escapeQuotes: false, stripTags: false });
      expect(result).toBe('"test"');
    });
  });

  describe('validateForm', () => {
    test('should return success for valid form with no rules', () => {
      const formData = new FormData();
      formData.append('field1', 'value1');
      const result = validateForm(formData);
      expect(result.success).toBe(true);
    });

    test('should validate form with rules', () => {
      const formData = {
        email: 'test@example.com',
        name: 'John Doe',
        phone: '1234567890'
      };
      const rules = {
        email: { required: true, format: 'email' },
        name: { required: true, minLength: 2 },
        phone: { required: true, format: 'phone' }
      };
      const result = validateForm(formData, rules);
      expect(result.success).toBe(true);
    });

    test('should return errors for invalid fields', () => {
      const formData = {
        email: 'invalid-email',
        name: 'J',
        phone: '123'
      };
      const rules = {
        email: { required: true, format: 'email' },
        name: { required: true, minLength: 2 },
        phone: { required: true, format: 'phone' }
      };
      const result = validateForm(formData, rules);
      expect(result.success).toBe(false);
      expect(result.errors).toHaveLength(3);
      expect(result.errors[0].field).toBe('email');
      expect(result.errors[1].field).toBe('name');
      expect(result.errors[2].field).toBe('phone');
    });

    test('should handle missing required fields', () => {
      const formData = {
        name: 'John Doe'
      };
      const rules = {
        email: { required: true, format: 'email' },
        name: { required: true }
      };
      const result = validateForm(formData, rules);
      expect(result.success).toBe(false);
      expect(result.errors).toHaveLength(1);
      expect(result.errors[0].field).toBe('email');
    });

    test('should handle optional fields', () => {
      const formData = {
        email: 'test@example.com'
      };
      const rules = {
        email: { required: true, format: 'email' },
        phone: { required: false, format: 'phone' }
      };
      const result = validateForm(formData, rules);
      expect(result.success).toBe(true);
    });

    test('should work with FormData object', () => {
      const formData = new FormData();
      formData.append('email', 'test@example.com');
      formData.append('name', 'John Doe');
      const rules = {
        email: { required: true, format: 'email' },
        name: { required: true, minLength: 2 }
      };
      const result = validateForm(formData, rules);
      expect(result.success).toBe(true);
    });

    test('should return error for empty form with no rules', () => {
      const formData = {};
      const result = validateForm(formData);
      expect(result.success).toBe(false);
      expect(result.errors[0].field).toBe('form');
    });
  });
});
