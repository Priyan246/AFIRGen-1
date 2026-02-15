/**
 * Unit tests for error handling utilities
 */

// Setup mocks
global.window = global.window || {};
global.document = {
  createElement: () => ({
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

window.ENV = { API_BASE_URL: 'http://localhost:8000', API_KEY: 'test-key' };
global.fetch = jest.fn();

let toastCalls = [];
window.showToast = (message, type, duration) => {
  toastCalls.push({ message, type, duration });
};

console.error = jest.fn();
console.warn = jest.fn();

// Load modules
require('./api.js');
require('./validation.js');

const { handleNetworkError, handleAPIError } = window.API;
const { handleValidationError } = window.Validation;

describe('Error Handling Utilities', () => {
  beforeEach(() => {
    toastCalls = [];
    jest.clearAllMocks();
  });

  describe('handleNetworkError', () => {
    it('handles generic network error', () => {
      const error = new Error('Network error occurred');
      const result = handleNetworkError(error, 'file upload');

      expect(result.success).toBe(false);
      expect(result.errorCode).toBe('NETWORK_ERROR');
      expect(result.message).toContain('Unable to connect');
      expect(result.operation).toBe('file upload');
      expect(toastCalls.length).toBe(1);
    });

    it('handles timeout error', () => {
      const error = new Error('Request timeout');
      const result = handleNetworkError(error);

      expect(result.errorCode).toBe('TIMEOUT');
      expect(result.message).toContain('took too long');
    });

    it('handles abort error', () => {
      const error = new Error('Request aborted');
      const result = handleNetworkError(error);

      expect(result.errorCode).toBe('ABORT');
      expect(result.message).toContain('cancelled');
    });
  });

  describe('handleAPIError', () => {
    it('handles 400 Bad Request', async () => {
      const mockResponse = {
        status: 400,
        statusText: 'Bad Request',
        headers: { get: () => 'application/json' },
        json: async () => ({ error: 'Invalid input' })
      };

      const result = await handleAPIError(mockResponse, 'form submission');

      expect(result.success).toBe(false);
      expect(result.errorCode).toBe('400');
      expect(result.message).toContain('Invalid request');
      expect(result.details).toBe('Invalid input');
    });

    it('handles 500 Internal Server Error', async () => {
      const mockResponse = {
        status: 500,
        statusText: 'Internal Server Error',
        headers: { get: () => 'application/json' },
        json: async () => ({ error: 'Database error' })
      };

      const result = await handleAPIError(mockResponse);

      expect(result.errorCode).toBe('500');
      expect(result.message).toContain('Server error');
    });
  });

  describe('handleValidationError', () => {
    it('handles single error object', () => {
      const error = { error: 'File type not allowed' };
      const result = handleValidationError(error, 'file upload');

      expect(result.success).toBe(false);
      expect(result.errorCode).toBe('VALIDATION_ERROR');
      expect(result.errors.length).toBe(1);
      expect(result.errors[0].message).toBe('File type not allowed');
    });

    it('handles array of errors', () => {
      const errors = [
        { field: 'email', message: 'Invalid email' },
        { field: 'phone', message: 'Phone required' }
      ];
      const result = handleValidationError(errors);

      expect(result.errors.length).toBe(2);
      expect(result.count).toBe(2);
      expect(result.message).toContain('2 validation errors');
    });

    it('maps file type errors correctly', () => {
      const error = { error: 'File type not allowed' };
      const result = handleValidationError(error);

      expect(result.errors[0].errorCode).toBe('FILE_TYPE_INVALID');
      expect(result.errors[0].suggestion).toContain('JPG, PNG, PDF');
    });

    it('maps file size errors correctly', () => {
      const error = { error: 'File size (15MB) exceeds maximum' };
      const result = handleValidationError(error);

      expect(result.errors[0].errorCode).toBe('FILE_SIZE_EXCEEDED');
      expect(result.errors[0].suggestion).toContain('smaller than 10MB');
    });
  });
});
