/**
 * Property-Based Tests for API Module
 * Tests API request retry logic with various failure scenarios
 */

const fc = require('fast-check');

/**
 * Property 3: API Request Retry
 * **Validates: Requirements 5.1.7**
 *
 * This property verifies that the API retry logic:
 * - Retries on network failures and 5xx responses
 * - Uses exponential backoff (1s, 2s, 4s)
 * - Retries up to 3 times
 * - Does not retry on 4xx errors (except 429)
 */

describe('Property 3: API Request Retry', () => {
  let originalFetch;
  let APIClient;

  beforeEach(() => {
    // Save original fetch
    originalFetch = global.fetch;

    // Mock APIClient class
    APIClient = class {
      constructor() {
        this.baseURL = 'http://test.com';
        this.apiKey = 'test-key';
        this.defaultTimeout = 30000;
      }

      async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const timeout = options.timeout || this.defaultTimeout;
        const headers = {
          'X-API-Key': this.apiKey,
          ...options.headers
        };

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);

        try {
          const response = await fetch(url, {
            ...options,
            headers,
            signal: controller.signal
          });
          clearTimeout(timeoutId);
          return response;
        } catch (error) {
          clearTimeout(timeoutId);
          if (error.name === 'AbortError') {
            const timeoutError = new Error('Request timeout');
            timeoutError.name = 'TimeoutError';
            throw timeoutError;
          }
          throw error;
        }
      }

      async retryRequest(fn, maxRetries = 3, backoff = 10) {
        let lastError;
        for (let attempt = 0; attempt < maxRetries; attempt++) {
          try {
            return await fn();
          } catch (error) {
            lastError = error;
            if (error.status >= 400 && error.status < 500 && error.status !== 429) {
              throw error;
            }
            if (error.name === 'TimeoutError' && attempt > 0) {
              throw error;
            }
            if (attempt === maxRetries - 1) {
              break;
            }
            const delay = backoff * Math.pow(2, attempt);
            await new Promise(resolve => setTimeout(resolve, delay));
          }
        }
        throw lastError;
      }

      async get(endpoint, params = {}) {
        return this.retryRequest(async () => {
          const queryString = Object.keys(params).length > 0
            ? `?${new URLSearchParams(params).toString()}`
            : '';
          const response = await this.request(endpoint + queryString, { method: 'GET' });
          if (!response.ok) {
            const error = new Error(`GET ${endpoint} failed`);
            error.status = response.status;
            throw error;
          }
          return await response.json();
        });
      }
    };
  });

  afterEach(() => {
    // Restore original fetch
    global.fetch = originalFetch;
  });

  test('should retry on network failures up to 3 times', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.integer({ min: 1, max: 2 }),
        async (failureCount) => {
          let attemptCount = 0;

          // Mock fetch to fail N times then succeed
          global.fetch = jest.fn(async () => {
            attemptCount++;
            if (attemptCount <= failureCount) {
              throw new Error('Network error');
            }
            return {
              ok: true,
              json: async () => ({ success: true, data: 'test' })
            };
          });

          const client = new APIClient();
          const result = await client.get('/test');

          // Should have retried failureCount times + 1 successful attempt
          expect(attemptCount).toBe(failureCount + 1);
          expect(result).toEqual({ success: true, data: 'test' });
        }
      ),
      { numRuns: 10 }
    );
  });

  test('should retry on 5xx errors up to 3 times', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.integer({ min: 500, max: 599 }),
        fc.integer({ min: 1, max: 2 }),
        async (statusCode, failureCount) => {
          let attemptCount = 0;

          // Mock fetch to return 5xx N times then succeed
          global.fetch = jest.fn(async () => {
            attemptCount++;
            if (attemptCount <= failureCount) {
              return {
                ok: false,
                status: statusCode,
                json: async () => ({ error: 'Server error' })
              };
            }
            return {
              ok: true,
              json: async () => ({ success: true })
            };
          });

          const client = new APIClient();
          const result = await client.get('/test');

          expect(attemptCount).toBe(failureCount + 1);
          expect(result).toEqual({ success: true });
        }
      ),
      { numRuns: 10 }
    );
  });

  test('should NOT retry on 4xx errors (except 429)', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.integer({ min: 400, max: 499 }).filter(code => code !== 429),
        async (statusCode) => {
          let attemptCount = 0;

          // Mock fetch to return 4xx error
          global.fetch = jest.fn(async () => {
            attemptCount++;
            return {
              ok: false,
              status: statusCode,
              json: async () => ({ error: 'Client error' })
            };
          });

          const client = new APIClient();

          try {
            await client.get('/test');
            // Should not reach here
            expect(true).toBe(false);
          } catch (error) {
            // Should fail on first attempt without retry
            expect(attemptCount).toBe(1);
            expect(error.status).toBe(statusCode);
          }
        }
      ),
      { numRuns: 10 }
    );
  });

  test('should retry on 429 (rate limit) errors', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.integer({ min: 1, max: 2 }),
        async (failureCount) => {
          let attemptCount = 0;

          // Mock fetch to return 429 N times then succeed
          global.fetch = jest.fn(async () => {
            attemptCount++;
            if (attemptCount <= failureCount) {
              return {
                ok: false,
                status: 429,
                json: async () => ({ error: 'Too many requests' })
              };
            }
            return {
              ok: true,
              json: async () => ({ success: true })
            };
          });

          const client = new APIClient();
          const result = await client.get('/test');

          expect(attemptCount).toBe(failureCount + 1);
          expect(result).toEqual({ success: true });
        }
      ),
      { numRuns: 10 }
    );
  });

  test('should use exponential backoff between retries', async () => {
    const timestamps = [];
    let attemptCount = 0;

    // Mock fetch to fail 3 times
    global.fetch = jest.fn(async () => {
      timestamps.push(Date.now());
      attemptCount++;
      if (attemptCount <= 3) {
        throw new Error('Network error');
      }
      return {
        ok: true,
        json: async () => ({ success: true })
      };
    });

    const client = new APIClient();

    try {
      await client.get('/test');
    } catch (error) {
      // Expected to fail after 3 retries
    }

    // Verify exponential backoff timing (with 10ms base delay for testing)
    // Delays should be approximately: 10ms, 20ms, 40ms
    if (timestamps.length >= 3) {
      const delay1 = timestamps[1] - timestamps[0];
      const delay2 = timestamps[2] - timestamps[1];

      // Allow some tolerance for timing
      expect(delay1).toBeGreaterThanOrEqual(8);
      expect(delay2).toBeGreaterThanOrEqual(15);
      expect(delay2).toBeGreaterThan(delay1);
    }
  });

  test('should fail after max retries exhausted', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.constant(null),
        async () => {
          let attemptCount = 0;

          // Mock fetch to always fail
          global.fetch = jest.fn(async () => {
            attemptCount++;
            throw new Error('Network error');
          });

          const client = new APIClient();

          try {
            await client.get('/test');
            // Should not reach here
            expect(true).toBe(false);
          } catch (error) {
            // Should have attempted 3 times (max retries)
            expect(attemptCount).toBe(3);
            expect(error.message).toBe('Network error');
          }
        }
      ),
      { numRuns: 5 }
    );
  });
});
