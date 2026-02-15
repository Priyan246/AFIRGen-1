/**
 * Integration tests for error handling system
 * Tests that all error handling uses the new system with specific, actionable messages
 */

// Load required modules
require('./api.js');
require('./validation.js');
require('./ui.js');

describe('Error Handling Integration', () => {
  let mockToastContainer;

  beforeEach(() => {
    // Create mock toast container
    mockToastContainer = document.createElement('div');
    mockToastContainer.id = 'toast-container';
    document.body.appendChild(mockToastContainer);

    // Reset toast counter
    window.toastIdCounter = 0;
    window.activeToasts = new Map();
  });

  afterEach(() => {
    // Clean up
    if (mockToastContainer && mockToastContainer.parentNode) {
      mockToastContainer.parentNode.removeChild(mockToastContainer);
    }

    // Clear any remaining toasts
    document.querySelectorAll('.toast').forEach(toast => toast.remove());
  });

  describe('Network Error Handling', () => {
    test('should provide specific error message for network timeout', () => {
      const error = new Error('Request timeout');
      const result = window.API.handleNetworkError(error, 'file upload');

      expect(result.success).toBe(false);
      expect(result.errorCode).toBe('TIMEOUT');
      expect(result.message).toContain('took too long');
      expect(result.suggestion).toContain('try again');
      expect(result.operation).toBe('file upload');
    });

    test('should provide specific error message for connection failure', () => {
      const error = new Error('Failed to fetch');
      const result = window.API.handleNetworkError(error, 'validation');

      expect(result.success).toBe(false);
      expect(result.errorCode).toBe('NETWORK_ERROR');
      expect(result.message).toContain('connect to the server');
      expect(result.suggestion).toContain('check your connection');
      expect(result.operation).toBe('validation');
      expect(result.isCritical).toBe(true);
    });

    test('should include operation context in error message', () => {
      const error = new Error('Network error');
      const result = window.API.handleNetworkError(error, 'content regeneration');

      expect(result.operation).toBe('content regeneration');
      expect(result.message).toBeTruthy();
    });

    test('should show toast notification with error details', () => {
      const error = new Error('Network error');
      window.API.handleNetworkError(error, 'file processing');

      // Check that toast was created
      const toasts = document.querySelectorAll('.toast');
      expect(toasts.length).toBeGreaterThan(0);

      const toast = toasts[0];
      expect(toast.classList.contains('toast-error')).toBe(true);
      expect(toast.textContent).toContain('connect to the server');
    });
  });

  describe('API Error Handling', () => {
    test('should provide specific error message for 400 Bad Request', async () => {
      const mockResponse = {
        status: 400,
        statusText: 'Bad Request',
        headers: { get: () => 'application/json' },
        json: async () => ({ error: 'Invalid file format' }),
        url: 'http://localhost:8000/process'
      };

      const result = await window.API.handleAPIError(mockResponse, 'file upload');

      expect(result.success).toBe(false);
      expect(result.errorCode).toBe('400');
      expect(result.message).toContain('Invalid request');
      expect(result.suggestion).toContain('review your input');
      expect(result.operation).toBe('file upload');
      expect(result.details).toBe('Invalid file format');
    });

    test('should provide specific error message for 401 Unauthorized', async () => {
      const mockResponse = {
        status: 401,
        statusText: 'Unauthorized',
        headers: { get: () => 'application/json' },
        json: async () => ({ error: 'Invalid API key' }),
        url: 'http://localhost:8000/validate'
      };

      const result = await window.API.handleAPIError(mockResponse, 'validation');

      expect(result.success).toBe(false);
      expect(result.errorCode).toBe('401');
      expect(result.message).toContain('Authentication failed');
      expect(result.suggestion).toContain('refresh the page');
      expect(result.operation).toBe('validation');
      expect(result.isCritical).toBe(true);
    });

    test('should provide specific error message for 404 Not Found', async () => {
      const mockResponse = {
        status: 404,
        statusText: 'Not Found',
        headers: { get: () => 'application/json' },
        json: async () => ({ error: 'Session not found' }),
        url: 'http://localhost:8000/session/123/status'
      };

      const result = await window.API.handleAPIError(mockResponse, 'session status check');

      expect(result.success).toBe(false);
      expect(result.errorCode).toBe('404');
      expect(result.message).toContain('not found');
      expect(result.suggestion).toContain('verify');
      expect(result.operation).toBe('session status check');
    });

    test('should provide specific error message for 429 Rate Limit', async () => {
      const mockResponse = {
        status: 429,
        statusText: 'Too Many Requests',
        headers: { get: () => 'application/json' },
        json: async () => ({ error: 'Rate limit exceeded' }),
        url: 'http://localhost:8000/process'
      };

      const result = await window.API.handleAPIError(mockResponse, 'file processing');

      expect(result.success).toBe(false);
      expect(result.errorCode).toBe('429');
      expect(result.message).toContain('Too many requests');
      expect(result.suggestion).toContain('wait');
      expect(result.operation).toBe('file processing');
    });

    test('should provide specific error message for 500 Server Error', async () => {
      const mockResponse = {
        status: 500,
        statusText: 'Internal Server Error',
        headers: { get: () => 'application/json' },
        json: async () => ({ error: 'Database connection failed' }),
        url: 'http://localhost:8000/regenerate'
      };

      const result = await window.API.handleAPIError(mockResponse, 'content regeneration');

      expect(result.success).toBe(false);
      expect(result.errorCode).toBe('500');
      expect(result.message).toContain('Server error');
      expect(result.suggestion).toContain('try again in a few minutes');
      expect(result.operation).toBe('content regeneration');
      expect(result.isCritical).toBe(true);
    });

    test('should include operation context in all API errors', async () => {
      const operations = [
        'file upload',
        'validation',
        'content regeneration',
        'session status check',
        'FIR retrieval'
      ];

      for (const operation of operations) {
        const mockResponse = {
          status: 500,
          statusText: 'Error',
          headers: { get: () => null },
          json: async () => ({}),
          url: 'http://localhost:8000/test'
        };

        const result = await window.API.handleAPIError(mockResponse, operation);
        expect(result.operation).toBe(operation);
        expect(result.message).toContain(operation);
      }
    });

    test('should show toast notification with error details', async () => {
      const mockResponse = {
        status: 400,
        statusText: 'Bad Request',
        headers: { get: () => 'application/json' },
        json: async () => ({ error: 'Invalid input' }),
        url: 'http://localhost:8000/process'
      };

      await window.API.handleAPIError(mockResponse, 'file upload');

      // Check that toast was created
      const toasts = document.querySelectorAll('.toast');
      expect(toasts.length).toBeGreaterThan(0);

      const toast = toasts[0];
      expect(toast.classList.contains('toast-error')).toBe(true);
      expect(toast.textContent).toContain('Invalid');
    });
  });

  describe('Validation Error Handling', () => {
    test('should provide specific error message for file type validation', () => {
      const error = { error: 'File type not allowed. Allowed types: .jpg, .png' };
      const result = window.Validation.handleValidationError(error, 'file upload');

      expect(result.success).toBe(false);
      expect(result.errorCode).toBe('VALIDATION_ERROR');
      expect(result.errors[0].errorCode).toBe('FILE_TYPE_INVALID');
      expect(result.errors[0].suggestion).toContain('JPG, PNG, PDF');
      expect(result.context).toBe('file upload');
    });

    test('should provide specific error message for file size validation', () => {
      const error = { error: 'File size (15.5MB) exceeds maximum allowed size of 10MB' };
      const result = window.Validation.handleValidationError(error, 'file upload');

      expect(result.success).toBe(false);
      expect(result.errors[0].errorCode).toBe('FILE_SIZE_EXCEEDED');
      expect(result.errors[0].suggestion).toContain('smaller than 10MB');
      expect(result.context).toBe('file upload');
    });

    test('should provide specific error message for required field', () => {
      const error = { error: 'Text is required' };
      const result = window.Validation.handleValidationError(error, 'form submission');

      expect(result.success).toBe(false);
      expect(result.errors[0].errorCode).toBe('TEXT_REQUIRED');
      expect(result.errors[0].suggestion).toContain('fill in');
      expect(result.context).toBe('form submission');
    });

    test('should provide specific error message for invalid format', () => {
      const error = { error: 'Invalid email format' };
      const result = window.Validation.handleValidationError(error, 'email validation');

      expect(result.success).toBe(false);
      expect(result.errors[0].errorCode).toBe('TEXT_INVALID_FORMAT');
      expect(result.errors[0].suggestion).toContain('check the format');
      expect(result.context).toBe('email validation');
    });

    test('should handle multiple validation errors', () => {
      const errors = {
        errors: [
          { field: 'email', message: 'Invalid email format' },
          { field: 'phone', message: 'Invalid phone number format' }
        ]
      };

      const result = window.Validation.handleValidationError(errors, 'form submission');

      expect(result.success).toBe(false);
      expect(result.count).toBe(2);
      expect(result.errors).toHaveLength(2);
      expect(result.message).toContain('2 validation errors');
    });

    test('should include operation context in validation errors', () => {
      const error = { error: 'Validation failed' };
      const result = window.Validation.handleValidationError(error, 'step validation');

      expect(result.context).toBe('step validation');
      expect(result.message).toContain('step validation');
    });

    test('should show toast notification with validation error', () => {
      const error = { error: 'File type not allowed' };
      window.Validation.handleValidationError(error, 'file upload');

      // Check that toast was created
      const toasts = document.querySelectorAll('.toast');
      expect(toasts.length).toBeGreaterThan(0);

      const toast = toasts[0];
      expect(toast.classList.contains('toast-warning')).toBe(true);
      expect(toast.textContent).toContain('File type not allowed');
    });
  });

  describe('Error Message Actionability', () => {
    test('all network errors should have actionable suggestions', () => {
      const errorTypes = [
        new Error('Request timeout'),
        new Error('Failed to fetch'),
        new Error('Network error'),
        new Error('Connection aborted')
      ];

      errorTypes.forEach(error => {
        const result = window.API.handleNetworkError(error, 'test operation');
        expect(result.suggestion).toBeTruthy();
        expect(result.suggestion.length).toBeGreaterThan(10);
        // Suggestion should contain action words
        expect(
          result.suggestion.match(/try|check|wait|reload|refresh/i)
        ).toBeTruthy();
      });
    });

    test('all API errors should have actionable suggestions', async () => {
      const statusCodes = [400, 401, 403, 404, 429, 500, 502, 503];

      for (const status of statusCodes) {
        const mockResponse = {
          status,
          statusText: 'Error',
          headers: { get: () => null },
          json: async () => ({}),
          url: 'http://localhost:8000/test'
        };

        const result = await window.API.handleAPIError(mockResponse, 'test operation');
        expect(result.suggestion).toBeTruthy();
        expect(result.suggestion.length).toBeGreaterThan(10);
        // Suggestion should contain action words
        expect(
          result.suggestion.match(/try|check|wait|reload|refresh|review|verify|contact/i)
        ).toBeTruthy();
      }
    });

    test('all validation errors should have actionable suggestions', () => {
      const validationErrors = [
        { error: 'File type not allowed' },
        { error: 'File size exceeds maximum' },
        { error: 'Text is required' },
        { error: 'Invalid email format' },
        { error: 'Text contains invalid characters' }
      ];

      validationErrors.forEach(error => {
        const result = window.Validation.handleValidationError(error, 'test');
        expect(result.errors[0].suggestion).toBeTruthy();
        expect(result.errors[0].suggestion.length).toBeGreaterThan(10);
        // Suggestion should contain action words
        expect(
          result.errors[0].suggestion.match(/upload|enter|remove|check|try|fill/i)
        ).toBeTruthy();
      });
    });
  });

  describe('Error Context Specificity', () => {
    test('should include specific operation context in all errors', () => {
      const operations = [
        'file upload',
        'file processing',
        'validation',
        'step validation',
        'content regeneration',
        'session status check',
        'FIR retrieval',
        'clipboard copy'
      ];

      operations.forEach(operation => {
        const error = new Error('Test error');
        const result = window.API.handleNetworkError(error, operation);

        expect(result.operation).toBe(operation);
        // Operation should be mentioned in logs or tracking
        expect(result).toHaveProperty('operation');
      });
    });

    test('should not use generic error messages', () => {
      const genericPhrases = [
        'something went wrong',
        'an error occurred',
        'error',
        'failed'
      ];

      // Test network errors
      const networkError = new Error('Network error');
      const networkResult = window.API.handleNetworkError(networkError, 'test');

      genericPhrases.forEach(phrase => {
        expect(networkResult.message.toLowerCase()).not.toBe(phrase);
      });

      // Message should be specific
      expect(networkResult.message).toContain('connect');
    });
  });

  describe('Critical Error Handling', () => {
    test('should identify critical errors correctly', () => {
      const criticalErrors = [
        new Error('Failed to fetch')
      ];

      criticalErrors.forEach(error => {
        const result = window.API.handleNetworkError(error, 'test');
        expect(result.isCritical).toBe(true);
      });
    });

    test('should show reload button for critical errors', () => {
      const error = new Error('Failed to fetch');
      window.API.handleNetworkError(error, 'critical operation');

      // Check that critical error toast was created with reload button
      const toasts = document.querySelectorAll('.toast.critical-error');
      expect(toasts.length).toBeGreaterThan(0);

      const toast = toasts[0];
      const reloadButton = toast.querySelector('.toast-button');
      expect(reloadButton).toBeTruthy();
      expect(reloadButton.textContent).toContain('Reload');
    });
  });
});
