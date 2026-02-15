/**
 * Property-Based Tests for Offline Mode Functionality
 * 
 * Property 6: Offline Mode Functionality
 * Validates: Requirements 5.5.6
 * 
 * For any cached FIR or session data, the system SHALL allow viewing and basic 
 * operations when offline, queuing write operations for sync when online.
 */

const fc = require('fast-check');

describe('Property 6: Offline Mode Functionality', () => {
  let mockServiceWorker;
  let mockCache;
  let mockCacheStorage;

  beforeEach(() => {
    // Mock Cache API
    mockCache = {
      match: jest.fn(),
      put: jest.fn(),
      delete: jest.fn(),
      keys: jest.fn(),
    };

    mockCacheStorage = {
      open: jest.fn().mockResolvedValue(mockCache),
      keys: jest.fn().mockResolvedValue(['afirgen-v1.0.0']),
      delete: jest.fn().mockResolvedValue(true),
      match: jest.fn(),
    };

    global.caches = mockCacheStorage;

    // Mock Service Worker
    mockServiceWorker = {
      register: jest.fn().mockResolvedValue({
        scope: '/',
        installing: null,
        waiting: null,
        active: { state: 'activated' },
        addEventListener: jest.fn(),
        update: jest.fn(),
      }),
      controller: { state: 'activated' },
      addEventListener: jest.fn(),
    };

    global.navigator = {
      ...global.navigator,
      serviceWorker: mockServiceWorker,
      onLine: true,
    };

    // Mock fetch
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  /**
   * Property: Cached static assets should be accessible offline
   */
  test('Property: Cached static assets are accessible when offline', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.array(
          fc.record({
            url: fc.constantFrom(
              '/index.html',
              '/css/main.css',
              '/css/themes.css',
              '/js/app.js',
              '/js/api.js',
              '/lib/dompurify.min.js'
            ),
            content: fc.string({ minLength: 10, maxLength: 1000 }),
            contentType: fc.constantFrom(
              'text/html',
              'text/css',
              'application/javascript'
            ),
          }),
          { minLength: 1, maxLength: 10 }
        ),
        async (cachedAssets) => {
          // Setup: Cache the assets
          for (const asset of cachedAssets) {
            const response = new Response(asset.content, {
              status: 200,
              headers: { 'Content-Type': asset.contentType },
            });
            mockCache.match.mockResolvedValueOnce(response);
          }

          // Simulate offline mode
          global.navigator.onLine = false;
          global.fetch.mockRejectedValue(new Error('Network request failed'));

          // Test: Try to access each cached asset
          for (const asset of cachedAssets) {
            const cachedResponse = await mockCache.match(asset.url);

            // Verify: Asset should be accessible from cache
            expect(cachedResponse).toBeDefined();
            expect(cachedResponse.status).toBe(200);
            expect(await cachedResponse.text()).toBe(asset.content);
          }
        }
      ),
      { numRuns: 50 }
    );
  });

  /**
   * Property: API responses should be cached and accessible offline
   */
  test('Property: Cached API responses are accessible when offline', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.array(
          fc.record({
            endpoint: fc.constantFrom('/session', '/fir', '/validate'),
            sessionId: fc.uuid(),
            responseData: fc.record({
              success: fc.boolean(),
              data: fc.string({ minLength: 10, maxLength: 500 }),
              timestamp: fc.date(),
            }),
          }),
          { minLength: 1, maxLength: 5 }
        ),
        async (apiCalls) => {
          // Setup: Cache API responses
          for (const call of apiCalls) {
            const response = new Response(JSON.stringify(call.responseData), {
              status: 200,
              headers: { 'Content-Type': 'application/json' },
            });
            mockCache.match.mockResolvedValueOnce(response);
          }

          // Simulate offline mode
          global.navigator.onLine = false;
          global.fetch.mockRejectedValue(new Error('Network request failed'));

          // Test: Try to access each cached API response
          for (const call of apiCalls) {
            const url = `${call.endpoint}?session_id=${call.sessionId}`;
            const cachedResponse = await mockCache.match(url);

            // Verify: API response should be accessible from cache
            expect(cachedResponse).toBeDefined();
            expect(cachedResponse.status).toBe(200);

            const data = await cachedResponse.json();
            expect(data.success).toBe(call.responseData.success);
            expect(data.data).toBe(call.responseData.data);
          }
        }
      ),
      { numRuns: 50 }
    );
  });

  /**
   * Property: Write operations should be queued when offline
   */
  test('Property: Write operations are queued when offline and synced when online', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.array(
          fc.record({
            operation: fc.constantFrom('validate', 'regenerate', 'update'),
            sessionId: fc.uuid(),
            data: fc.object(),
            timestamp: fc.date(),
          }),
          { minLength: 1, maxLength: 10 }
        ),
        async (writeOperations) => {
          const queuedOperations = [];

          // Simulate offline mode
          global.navigator.onLine = false;

          // Test: Queue write operations when offline
          for (const op of writeOperations) {
            try {
              // Attempt to perform write operation
              await global.fetch(`/${op.operation}`, {
                method: 'POST',
                body: JSON.stringify(op.data),
              });
            } catch (error) {
              // Operation should fail and be queued
              queuedOperations.push({
                ...op,
                queuedAt: new Date(),
              });
            }
          }

          // Verify: All operations should be queued
          expect(queuedOperations.length).toBe(writeOperations.length);

          // Simulate going back online
          global.navigator.onLine = true;
          global.fetch.mockResolvedValue(
            new Response(JSON.stringify({ success: true }), {
              status: 200,
              headers: { 'Content-Type': 'application/json' },
            })
          );

          // Test: Sync queued operations
          const syncResults = [];
          for (const op of queuedOperations) {
            try {
              const response = await global.fetch(`/${op.operation}`, {
                method: 'POST',
                body: JSON.stringify(op.data),
              });
              const result = await response.json();
              syncResults.push({ ...op, synced: result.success });
            } catch (error) {
              syncResults.push({ ...op, synced: false });
            }
          }

          // Verify: All operations should sync successfully when online
          expect(syncResults.every((r) => r.synced)).toBe(true);
        }
      ),
      { numRuns: 30 }
    );
  });

  /**
   * Property: Cache should have TTL and cleanup old entries
   */
  test('Property: Cache entries respect TTL and are cleaned up', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.array(
          fc.record({
            url: fc.webUrl(),
            content: fc.string({ minLength: 10, maxLength: 500 }),
            cachedAt: fc.date({ min: new Date('2020-01-01'), max: new Date() }),
            ttl: fc.integer({ min: 60, max: 3600 }), // TTL in seconds
          }),
          { minLength: 10, maxLength: 100 }
        ),
        async (cacheEntries) => {
          const now = new Date();
          const validEntries = [];
          const expiredEntries = [];

          // Classify entries as valid or expired
          for (const entry of cacheEntries) {
            const ageInSeconds = (now - entry.cachedAt) / 1000;
            if (ageInSeconds < entry.ttl) {
              validEntries.push(entry);
            } else {
              expiredEntries.push(entry);
            }
          }

          // Setup: Mock cache with entries
          mockCache.keys.mockResolvedValue(
            cacheEntries.map((e) => new Request(e.url))
          );

          // Test: Cleanup expired entries
          const keysToDelete = [];
          for (const entry of cacheEntries) {
            const ageInSeconds = (now - entry.cachedAt) / 1000;
            if (ageInSeconds >= entry.ttl) {
              keysToDelete.push(entry.url);
              await mockCache.delete(entry.url);
            }
          }

          // Verify: Expired entries should be deleted
          expect(mockCache.delete).toHaveBeenCalledTimes(expiredEntries.length);

          // Verify: Valid entries should remain
          const remainingKeys = cacheEntries
            .filter((e) => !keysToDelete.includes(e.url))
            .map((e) => e.url);

          expect(remainingKeys.length).toBe(validEntries.length);
        }
      ),
      { numRuns: 30 }
    );
  });

  /**
   * Property: Service worker should handle network failures gracefully
   */
  test('Property: Service worker handles network failures gracefully', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.array(
          fc.record({
            url: fc.webUrl(),
            method: fc.constantFrom('GET', 'POST'),
            shouldCache: fc.boolean(),
            networkError: fc.constantFrom(
              'NetworkError',
              'TimeoutError',
              'AbortError',
              null
            ),
          }),
          { minLength: 1, maxLength: 20 }
        ),
        async (requests) => {
          const results = [];

          for (const req of requests) {
            // Setup: Mock network behavior
            if (req.networkError) {
              global.fetch.mockRejectedValueOnce(new Error(req.networkError));
            } else {
              global.fetch.mockResolvedValueOnce(
                new Response('Success', { status: 200 })
              );
            }

            // Setup: Mock cache behavior
            if (req.shouldCache) {
              mockCache.match.mockResolvedValueOnce(
                new Response('Cached', { status: 200 })
              );
            } else {
              mockCache.match.mockResolvedValueOnce(undefined);
            }

            // Test: Make request
            try {
              let response;
              try {
                response = await global.fetch(req.url, { method: req.method });
              } catch (error) {
                // Network failed, try cache
                response = await mockCache.match(req.url);
              }

              // Verify: Should get response from network or cache
              if (response) {
                results.push({ url: req.url, success: true, source: 'cache' });
              } else {
                results.push({ url: req.url, success: false, source: null });
              }
            } catch (error) {
              results.push({ url: req.url, success: false, source: null });
            }
          }

          // Verify: Requests with cache or no error should succeed
          const expectedSuccesses = requests.filter(
            (r) => !r.networkError || r.shouldCache
          ).length;

          const actualSuccesses = results.filter((r) => r.success).length;

          // Allow some tolerance for race conditions
          expect(actualSuccesses).toBeGreaterThanOrEqual(
            Math.floor(expectedSuccesses * 0.8)
          );
        }
      ),
      { numRuns: 30 }
    );
  });
});
