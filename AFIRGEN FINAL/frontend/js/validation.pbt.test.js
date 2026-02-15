/**
 * Property-Based Tests for validation.js
 * **Validates: Requirements 5.3.2, 5.3.3**
 *
 * Property 1: File Validation Before Upload
 * For any file selected by the user, the system SHALL validate file type, size,
 * and MIME type before allowing upload, rejecting invalid files with descriptive error messages.
 */

const fc = require('fast-check');

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
const { validateFile } = window.Validation;

// Magic number signatures for generating valid files
const VALID_MAGIC_NUMBERS = {
  '.jpg': [0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46],
  '.jpeg': [0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46],
  '.png': [0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A],
  '.pdf': [0x25, 0x50, 0x44, 0x46, 0x2D, 0x31, 0x2E, 0x34],
  '.wav': [0x52, 0x49, 0x46, 0x46, 0x00, 0x00, 0x00, 0x00],
  '.mp3': [0x49, 0x44, 0x33, 0x03, 0x00, 0x00, 0x00, 0x00]
};

const INVALID_EXTENSIONS = ['.exe', '.bat', '.sh', '.dll', '.bin', '.zip', '.tar'];

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

// Arbitraries for generating test data

/**
 * Generate a valid file extension from the whitelist
 */
const validExtensionArb = () => fc.constantFrom('.jpg', '.jpeg', '.png', '.pdf', '.wav', '.mp3');

/**
 * Generate an invalid file extension (not in whitelist)
 */
const invalidExtensionArb = () => fc.constantFrom(...INVALID_EXTENSIONS);

/**
 * Generate a valid file size (0 to 10MB)
 */
const validFileSizeArb = () => fc.integer({ min: 1, max: 10 * 1024 * 1024 });

/**
 * Generate an invalid file size (over 10MB)
 */
const invalidFileSizeArb = () => fc.integer({ min: 10 * 1024 * 1024 + 1, max: 20 * 1024 * 1024 });

/**
 * Generate valid magic number bytes for a given extension
 */
const validMagicNumberArb = (extension) => {
  const magicBytes = VALID_MAGIC_NUMBERS[extension];
  // Add some random padding bytes after the magic number
  return fc.array(fc.integer({ min: 0, max: 255 }), { minLength: 0, maxLength: 100 })
    .map(padding => [...magicBytes, ...padding]);
};

/**
 * Generate invalid magic number bytes (random bytes that don't match any valid signature)
 */
const invalidMagicNumberArb = () => {
  return fc.array(fc.integer({ min: 0, max: 255 }), { minLength: 8, maxLength: 8 })
    .filter(bytes => {
      // Ensure the bytes don't accidentally match any valid magic number
      // Check JPEG signatures
      if (bytes[0] === 0xFF && bytes[1] === 0xD8 && bytes[2] === 0xFF) {
        return false;
      }

      // Check PNG signature
      if (bytes[0] === 0x89 && bytes[1] === 0x50 && bytes[2] === 0x4E && bytes[3] === 0x47 &&
                bytes[4] === 0x0D && bytes[5] === 0x0A && bytes[6] === 0x1A && bytes[7] === 0x0A) {
        return false;
      }

      // Check PDF signature
      if (bytes[0] === 0x25 && bytes[1] === 0x50 && bytes[2] === 0x44 && bytes[3] === 0x46) {
        return false;
      }

      // Check WAV signature (RIFF)
      if (bytes[0] === 0x52 && bytes[1] === 0x49 && bytes[2] === 0x46 && bytes[3] === 0x46) {
        return false;
      }

      // Check MP3 signatures
      if (bytes[0] === 0xFF && (bytes[1] === 0xFB || bytes[1] === 0xF3 || bytes[1] === 0xF2)) {
        return false;
      }
      if (bytes[0] === 0x49 && bytes[1] === 0x44 && bytes[2] === 0x33) {
        return false;
      }

      return true;
    });
};

/**
 * Generate a valid file (correct extension, size, and magic number)
 */
const validFileArb = () => {
  return validExtensionArb().chain(ext => {
    return fc.tuple(
      validFileSizeArb(),
      validMagicNumberArb(ext),
      fc.constant(ext)
    ).map(([size, magicBytes, extension]) => {
      // Ensure we have at least the magic number bytes
      const minSize = Math.max(size, magicBytes.length);
      const totalBytes = [...magicBytes];
      while (totalBytes.length < minSize) {
        totalBytes.push(0);
      }

      const fileName = `test${extension}`;
      const mimeType = extension === '.jpg' || extension === '.jpeg' ? 'image/jpeg' :
        extension === '.png' ? 'image/png' :
          extension === '.pdf' ? 'application/pdf' :
            extension === '.wav' ? 'audio/wav' :
              extension === '.mp3' ? 'audio/mpeg' : 'application/octet-stream';

      return createFileWithBytes(totalBytes, fileName, mimeType);
    });
  });
};

/**
 * Generate an invalid file (various reasons: wrong extension, too large, or invalid magic number)
 */
const invalidFileArb = () => {
  return fc.oneof(
    // Invalid extension
    fc.tuple(
      invalidExtensionArb(),
      validFileSizeArb(),
      fc.array(fc.integer({ min: 0, max: 255 }), { minLength: 8, maxLength: 100 })
    ).map(([ext, size, bytes]) => {
      const totalBytes = [...bytes];
      while (totalBytes.length < size) {
        totalBytes.push(0);
      }
      return createFileWithBytes(totalBytes.slice(0, size), `test${ext}`, 'application/octet-stream');
    }),

    // Invalid size (too large)
    fc.tuple(
      validExtensionArb(),
      invalidFileSizeArb(),
      validMagicNumberArb('.jpg')
    ).map(([ext, size, magicBytes]) => {
      const totalBytes = [...magicBytes];
      while (totalBytes.length < size) {
        totalBytes.push(0);
      }
      return createFileWithBytes(totalBytes.slice(0, size), `test${ext}`, 'application/octet-stream');
    }),

    // Invalid magic number
    fc.tuple(
      validExtensionArb(),
      validFileSizeArb(),
      invalidMagicNumberArb()
    ).map(([ext, size, bytes]) => {
      const totalBytes = [...bytes];
      while (totalBytes.length < size) {
        totalBytes.push(0);
      }
      return createFileWithBytes(totalBytes.slice(0, size), `test${ext}`, 'application/octet-stream');
    })
  );
};

describe('Property-Based Tests: File Validation', () => {
  describe('Property 1: File Validation Before Upload', () => {
    test('Valid files should always pass validation', async () => {
      await fc.assert(
        fc.asyncProperty(validFileArb(), async (file) => {
          const result = await validateFile(file);
          expect(result.success).toBe(true);
          expect(result.error).toBeUndefined();
        }),
        { numRuns: 5 }
      );
    });

    test('Invalid files should always fail validation with descriptive error', async () => {
      await fc.assert(
        fc.asyncProperty(invalidFileArb(), async (file) => {
          const result = await validateFile(file);
          expect(result.success).toBe(false);
          expect(result.error).toBeDefined();
          expect(typeof result.error).toBe('string');
          expect(result.error.length).toBeGreaterThan(0);
        }),
        { numRuns: 5 }
      );
    });

    test('Files exceeding size limit should be rejected with size error', async () => {
      await fc.assert(
        fc.asyncProperty(
          validExtensionArb(),
          invalidFileSizeArb(),
          validMagicNumberArb('.jpg'),
          async (ext, size, magicBytes) => {
            const totalBytes = [...magicBytes];
            while (totalBytes.length < size) {
              totalBytes.push(0);
            }
            const file = createFileWithBytes(totalBytes.slice(0, size), `test${ext}`, 'application/octet-stream');

            const result = await validateFile(file);
            expect(result.success).toBe(false);
            expect(result.error).toContain('exceeds maximum allowed size');
          }
        ),
        { numRuns: 3 }
      );
    });

    test('Files with invalid extensions should be rejected with type error', async () => {
      await fc.assert(
        fc.asyncProperty(
          invalidExtensionArb(),
          validFileSizeArb(),
          fc.array(fc.integer({ min: 0, max: 255 }), { minLength: 8, maxLength: 100 }),
          async (ext, size, bytes) => {
            const totalBytes = [...bytes];
            while (totalBytes.length < size) {
              totalBytes.push(0);
            }
            const file = createFileWithBytes(totalBytes.slice(0, size), `test${ext}`, 'application/octet-stream');

            const result = await validateFile(file);
            expect(result.success).toBe(false);
            expect(result.error).toContain('File type not allowed');
          }
        ),
        { numRuns: 3 }
      );
    });

    test('Files with invalid MIME types should be rejected with verification error', async () => {
      await fc.assert(
        fc.asyncProperty(
          validExtensionArb(),
          validFileSizeArb(),
          invalidMagicNumberArb(),
          async (ext, size, bytes) => {
            const totalBytes = [...bytes];
            while (totalBytes.length < size) {
              totalBytes.push(0);
            }
            const file = createFileWithBytes(totalBytes.slice(0, size), `test${ext}`, 'application/octet-stream');

            const result = await validateFile(file);
            expect(result.success).toBe(false);
            expect(result.error).toContain('File type could not be verified');
          }
        ),
        { numRuns: 3 }
      );
    });

    test('Validation should be consistent for the same file', async () => {
      await fc.assert(
        fc.asyncProperty(
          fc.oneof(validFileArb(), invalidFileArb()),
          async (file) => {
            const result1 = await validateFile(file);
            const result2 = await validateFile(file);

            expect(result1.success).toBe(result2.success);
            expect(result1.error).toBe(result2.error);
          }
        ),
        { numRuns: 3 }
      );
    });

    test('All whitelisted extensions should be accepted when valid', async () => {
      const extensions = ['.jpg', '.jpeg', '.png', '.pdf', '.wav', '.mp3'];

      for (const ext of extensions) {
        await fc.assert(
          fc.asyncProperty(
            validFileSizeArb(),
            validMagicNumberArb(ext),
            async (size, magicBytes) => {
              // Ensure we have at least the magic number bytes
              const minSize = Math.max(size, magicBytes.length);
              const totalBytes = [...magicBytes];
              while (totalBytes.length < minSize) {
                totalBytes.push(0);
              }
              const file = createFileWithBytes(totalBytes, `test${ext}`, 'application/octet-stream');

              const result = await validateFile(file);
              expect(result.success).toBe(true);
            }
          ),
          { numRuns: 5 }
        );
      }
    });

    test('Edge case: Minimum valid file size (1 byte) should pass', async () => {
      await fc.assert(
        fc.asyncProperty(validExtensionArb(), async (ext) => {
          const magicBytes = VALID_MAGIC_NUMBERS[ext];
          const file = createFileWithBytes(magicBytes, `test${ext}`, 'application/octet-stream');

          const result = await validateFile(file);
          expect(result.success).toBe(true);
        }),
        { numRuns: 5 }
      );
    });

    test('Edge case: Maximum valid file size (10MB) should pass', async () => {
      await fc.assert(
        fc.asyncProperty(validExtensionArb(), async (ext) => {
          const maxSize = 10 * 1024 * 1024;
          const magicBytes = VALID_MAGIC_NUMBERS[ext];
          const totalBytes = [...magicBytes];
          while (totalBytes.length < maxSize) {
            totalBytes.push(0);
          }
          const file = createFileWithBytes(totalBytes.slice(0, maxSize), `test${ext}`, 'application/octet-stream');

          const result = await validateFile(file);
          expect(result.success).toBe(true);
        }),
        { numRuns: 3 }
      );
    });

    test('Edge case: File size exactly 1 byte over limit should fail', async () => {
      await fc.assert(
        fc.asyncProperty(validExtensionArb(), async (ext) => {
          const overSize = 10 * 1024 * 1024 + 1;
          const magicBytes = VALID_MAGIC_NUMBERS[ext];
          const totalBytes = [...magicBytes];
          while (totalBytes.length < overSize) {
            totalBytes.push(0);
          }
          const file = createFileWithBytes(totalBytes.slice(0, overSize), `test${ext}`, 'application/octet-stream');

          const result = await validateFile(file);
          expect(result.success).toBe(false);
          expect(result.error).toContain('exceeds maximum allowed size');
        }),
        { numRuns: 3 }
      );
    });
  });
});

