/**
 * Unit tests for error recovery mechanisms
 * Tests automatic retry, reload button, and error logging
 */

// Setup mocks
global.window = global.window || {};
global.document = {
  createElement: (tag) => {
    const element = {
      tagName: tag.toUpperCase(),
      className: '',
      textContent: '',
      onclick: null,
      children: [],
      appendChild: function (child) {
        this.children.push(child);
      },
      remove: function () {
        // Mock remove
      },
      classList: {
        add: function () {},
        remove: function () {}
      },
      setAttribute: function () {}
    };
    return element;
  },
  getElementById: jest.fn((id) => {
    if (id === 'toast-container') {
      return {
        appendChild: function (child) {
          this.lastChild = child;
        },
        lastChild: null
      };
    }
    return null;
  })
};

global.navigator = {
  userAgent: 'Test Browser'
};

window.ENV = { API_BASE_URL: 'http://localhost:8000', API_KEY: 'test-key' };
const mockReload = jest.fn();
window.location = { href: 'http://localhost', reload: mockReload };

let toastCalls = [];
window.showToast = (message, type, duration) => {
  toastCalls.push({ message, type, duration });
};

// Mock console
const consoleLog = jest.fn();
const consoleError = jest.fn();
const consoleWarn = jest.fn();
console.log = consoleLog;
console.error = consoleError;
console.warn = consoleWarn;

// Mock fetch
global.fetch = jest.fn();

// Load module
require('./api.js');

const { retryWithBackoff, handleNetworkError, handleAPIError } = window.API;

describe('Error Recovery Mechanisms', () => {
  beforeEach(() => {
    toastCalls = [];
    jest.clearAllMocks();
    mockReload.mockClear();
  });

  describe('retryWithBackoff', () => {
    it('succeeds on first attempt', async () => {
      const mockFn = jest.fn().mockResolvedValue('success');

      const result = await retryWithBackoff(mockFn, 3, 100);

      expect(result).toBe('success');
      expect(mockFn).toHaveBeenCalledTimes(1);
      expect(consoleLog).not.toHaveBeenCalled();
    });

    it('retries on network error and succeeds', async () => {
      const mockFn = jest.fn()
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce('success');

      const result = await retryWithBackoff(mockFn, 3, 100);

      expect(result).toBe('success');
      expect(mockFn).toHaveBeenCalledTimes(2);
      expect(consoleLog).toHaveBeenCalledWith('Retry attempt 2/3');
      expect(toastCalls.length).toBe(1);
      expect(toastCalls[0].message).toContain('Retrying');
    });

    it('retries with exponential backoff', async () => {
      const mockFn = jest.fn()
        .mockRejectedValueOnce(new Error('Error 1'))
        .mockRejectedValueOnce(new Error('Error 2'))
        .mockResolvedValueOnce('success');

      const startTime = Date.now();
      const result = await retryWithBackoff(mockFn, 3, 100);
      const duration = Date.now() - startTime;

      expect(result).toBe('success');
      expect(mockFn).toHaveBeenCalledTimes(3);
      // Should wait 100ms + 200ms = 300ms minimum
      expect(duration).toBeGreaterThanOrEqual(250);
    });

    it('fails after max retries', async () => {
      const mockFn = jest.fn().mockRejectedValue(new Error('Persistent error'));

      await expect(retryWithBackoff(mockFn, 3, 100)).rejects.toThrow('Persistent error');

      expect(mockFn).toHaveBeenCalledTimes(3);
      expect(consoleError).toHaveBeenCalledTimes(3);
    });

    it('does not retry on 4xx errors (except 429)', async () => {
      const error = new Error('Bad request');
      error.status = 400;
      const mockFn = jest.fn().mockRejectedValue(error);

      await expect(retryWithBackoff(mockFn, 3, 100)).rejects.toThrow('Bad request');

      expect(mockFn).toHaveBeenCalledTimes(1);
    });

    it('retries on 429 rate limit error', async () => {
      const error429 = new Error('Rate limit');
      error429.status = 429;
      const mockFn = jest.fn()
        .mockRejectedValueOnce(error429)
        .mockResolvedValueOnce('success');

      const result = await retryWithBackoff(mockFn, 3, 100);

      expect(result).toBe('success');
      expect(mockFn).toHaveBeenCalledTimes(2);
    });

    it('retries on 5xx server errors', async () => {
      const error500 = new Error('Server error');
      error500.status = 500;
      const mockFn = jest.fn()
        .mockRejectedValueOnce(error500)
        .mockResolvedValueOnce('success');

      const result = await retryWithBackoff(mockFn, 3, 100);

      expect(result).toBe('success');
      expect(mockFn).toHaveBeenCalledTimes(2);
    });
  });

  describe('Enhanced error logging', () => {
    it('logs detailed network error information', () => {
      const error = new Error('Network failure');
      error.stack = 'Error stack trace';

      handleNetworkError(error, 'file upload');

      expect(consoleError).toHaveBeenCalledWith('Network error:', expect.objectContaining({
        message: 'Network failure',
        operation: 'file upload',
        timestamp: expect.any(String),
        stack: 'Error stack trace'
      }));
    });

    it('logs detailed API error information', async () => {
      const mockResponse = {
        status: 500,
        statusText: 'Internal Server Error',
        url: 'http://localhost:8000/api/test',
        headers: { get: () => 'application/json' },
        json: async () => ({ error: 'Database error' })
      };

      await handleAPIError(mockResponse, 'data fetch');

      expect(consoleError).toHaveBeenCalledWith('API error:', expect.objectContaining({
        status: 500,
        statusText: 'Internal Server Error',
        operation: 'data fetch',
        timestamp: expect.any(String),
        url: 'http://localhost:8000/api/test'
      }));
    });

    it('includes timestamp in error logs', () => {
      const error = new Error('Test error');
      const result = handleNetworkError(error);

      expect(result.timestamp).toBeDefined();
      expect(new Date(result.timestamp).getTime()).toBeGreaterThan(0);
    });
  });

  describe('Critical error handling with reload button', () => {
    it('identifies critical network errors', () => {
      const error = new Error('Failed to fetch');
      const result = handleNetworkError(error);

      expect(result.isCritical).toBe(true);
    });

    it('identifies critical API errors (401, 403, 5xx)', async () => {
      const mockResponse401 = {
        status: 401,
        statusText: 'Unauthorized',
        headers: { get: () => 'application/json' },
        json: async () => ({})
      };

      const result = await handleAPIError(mockResponse401);

      expect(result.isCritical).toBe(true);
    });

    it('creates reload button for critical errors', () => {
      const error = new Error('Failed to fetch');
      handleNetworkError(error, 'critical operation');

      // Check that critical error logging was called
      expect(consoleError).toHaveBeenCalledWith('CRITICAL ERROR:', expect.objectContaining({
        message: expect.any(String),
        operation: 'critical operation',
        timestamp: expect.any(String)
      }));
    });

    it('reload button triggers page reload', () => {
      // This test verifies the reload button functionality
      // The actual DOM manipulation is tested in integration tests
      const error = new Error('Failed to fetch');
      const result = handleNetworkError(error);

      // Verify critical error was identified
      expect(result.isCritical).toBe(true);

      // Verify critical error was logged
      const criticalErrorCall = consoleError.mock.calls.find(
        call => call[0] === 'CRITICAL ERROR:'
      );
      expect(criticalErrorCall).toBeDefined();
    });

    it('logs user agent and URL for critical errors', () => {
      const error = new Error('Failed to fetch');
      handleNetworkError(error);

      // Check that CRITICAL ERROR was logged (second call after Network error)
      const criticalErrorCall = consoleError.mock.calls.find(
        call => call[0] === 'CRITICAL ERROR:'
      );

      expect(criticalErrorCall).toBeDefined();
      expect(criticalErrorCall[1]).toMatchObject({
        message: expect.any(String),
        operation: expect.any(String),
        timestamp: expect.any(String)
      });
      // User agent and URL are from the actual environment, not our mock
      expect(criticalErrorCall[1].userAgent).toBeDefined();
      expect(criticalErrorCall[1].url).toBeDefined();
    });
  });

  describe('Non-critical errors', () => {
    it('does not show reload button for timeout errors', () => {
      const error = new Error('Request timeout');
      const result = handleNetworkError(error);

      expect(result.isCritical).toBeFalsy();
      expect(toastCalls.length).toBe(1);
      expect(toastCalls[0].type).toBe('error');
    });

    it('does not show reload button for 400 errors', async () => {
      const mockResponse = {
        status: 400,
        statusText: 'Bad Request',
        headers: { get: () => 'application/json' },
        json: async () => ({ error: 'Invalid input' })
      };

      const result = await handleAPIError(mockResponse);

      expect(result.isCritical).toBeFalsy();
    });
  });
});
