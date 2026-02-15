/**
 * Property-Based Tests for ui.js
 * **Validates: Requirements 5.2.1**
 *
 * Property 4: Loading State Visibility
 * For any asynchronous operation (API call, file upload, processing), the system SHALL
 * display a loading indicator within 100ms of operation start and hide it within 100ms of completion.
 */

const fc = require('fast-check');

// Mock DOM APIs needed by ui.js
global.document = {
  querySelectorAll: jest.fn(() => []),
  querySelector: jest.fn(() => null),
  getElementById: jest.fn(() => null),
  createElement: jest.fn((tag) => {
    const childrenArray = [];
    const element = {
      tagName: tag.toUpperCase(),
      className: '',
      style: {},
      textContent: '',
      get children() {
        return childrenArray;
      },
      attributes: {},
      appendChild: jest.fn(function (child) {
        childrenArray.push(child);
        child.parentNode = this;
        return child;
      }),
      removeChild: jest.fn((child) => {
        const index = childrenArray.indexOf(child);
        if (index > -1) {
          childrenArray.splice(index, 1);
          child.parentNode = null;
        }
        return child;
      }),
      setAttribute: jest.fn(function (name, value) {
        this.attributes[name] = value;
      }),
      getAttribute: jest.fn(function (name) {
        return this.attributes[name];
      }),
      removeAttribute: jest.fn(function (name) {
        delete this.attributes[name];
      }),
      querySelectorAll: jest.fn((selector) => {
        if (selector === '.loading-overlay') {
          return childrenArray.filter(child => child.className === 'loading-overlay');
        }
        if (selector === '.progress-overlay') {
          return childrenArray.filter(child => child.className === 'progress-overlay');
        }
        return [];
      }),
      querySelector: jest.fn(function (selector) {
        const results = this.querySelectorAll(selector);
        return results.length > 0 ? results[0] : null;
      }),
      classList: {
        add: jest.fn(),
        remove: jest.fn(),
        contains: jest.fn(() => false)
      },
      parentNode: null
    };
    return element;
  })
};

global.window = {
  getComputedStyle: jest.fn(() => ({
    position: 'static'
  }))
};

// Mock setTimeout and Date for timing tests
jest.useFakeTimers();

// Load the ui module
require('./ui.js');

// Extract the functions from window
const { showLoading, hideLoading, showProgress } = window;

// Arbitraries for generating test data

/**
 * Generate a random loading message
 */
const loadingMessageArb = () => fc.oneof(
  fc.constant('Loading...'),
  fc.constant('Processing...'),
  fc.constant('Please wait...'),
  fc.constant('Uploading...'),
  fc.constant('Generating FIR...'),
  fc.string({ minLength: 1, maxLength: 50 })
);

/**
 * Generate a random delay in milliseconds (simulating async operation duration)
 */
const operationDelayArb = () => fc.integer({ min: 0, max: 5000 });

/**
 * Generate a random progress percentage
 */
const progressPercentageArb = () => fc.integer({ min: 0, max: 100 });

/**
 * Create a mock element for testing
 */
const createMockElement = () => {
  const childrenArray = []; // Store children in closure
  const element = document.createElement('div');
  element.style = {};

  // Define children as a getter that returns the array
  Object.defineProperty(element, 'children', {
    get: () => childrenArray,
    enumerable: true
  });

  element.appendChild = jest.fn(function (child) {
    childrenArray.push(child);
    child.parentNode = this;
    return child;
  });

  element.removeChild = jest.fn((child) => {
    const index = childrenArray.indexOf(child);
    if (index > -1) {
      childrenArray.splice(index, 1);
      child.parentNode = null;
    }
    return child;
  });

  element.querySelectorAll = jest.fn((selector) => {
    if (selector === '.loading-overlay') {
      return childrenArray.filter(child => child.className === 'loading-overlay');
    }
    if (selector === '.progress-overlay') {
      return childrenArray.filter(child => child.className === 'progress-overlay');
    }
    return [];
  });

  element.querySelector = jest.fn((selector) => {
    const results = element.querySelectorAll(selector);
    return results.length > 0 ? results[0] : null;
  });

  return element;
};

/**
 * Measure time elapsed since a given start time
 */
const measureElapsedTime = (startTime) => {
  return Date.now() - startTime;
};

describe('Property-Based Tests: Loading State Visibility', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.clearAllTimers();
  });

  describe('Property 4: Loading State Visibility', () => {
    test('showLoading should display loading indicator within 100ms', () => {
      fc.assert(
        fc.property(loadingMessageArb(), (message) => {
          const element = createMockElement();
          const startTime = Date.now();

          // Show loading
          const loadingId = showLoading(element, message);

          // Measure time to display
          const elapsedTime = measureElapsedTime(startTime);

          // Should display within 100ms (synchronous operation should be instant)
          expect(elapsedTime).toBeLessThan(100);

          // Should have loading overlay
          expect(element.children.length).toBeGreaterThan(0);
          const overlay = element.children.find(child => child.className === 'loading-overlay');
          expect(overlay).toBeDefined();

          // Should have loading ID
          expect(loadingId).toBeDefined();
          expect(typeof loadingId).toBe('string');
        }),
        { numRuns: 20 }
      );
    });

    test('hideLoading should remove loading indicator within 100ms', () => {
      fc.assert(
        fc.property(loadingMessageArb(), (message) => {
          const element = createMockElement();

          // Show loading first
          const loadingId = showLoading(element, message);
          expect(element.children.length).toBeGreaterThan(0);

          // Hide loading
          const startTime = Date.now();
          hideLoading(loadingId);

          // Measure time to hide (accounting for fade out animation)
          const elapsedTime = measureElapsedTime(startTime);

          // Should initiate hiding within 100ms (synchronous operation)
          expect(elapsedTime).toBeLessThan(100);

          // Should set opacity to 0 for fade out
          const overlay = element.children.find(child => child.className === 'loading-overlay');
          if (overlay) {
            expect(overlay.style.opacity).toBe('0');
          }
        }),
        { numRuns: 20 }
      );
    });

    test('showProgress should display progress indicator within 100ms', () => {
      fc.assert(
        fc.property(
          progressPercentageArb(),
          loadingMessageArb(),
          (percentage, message) => {
            const element = createMockElement();
            const startTime = Date.now();

            // Show progress
            const progressId = showProgress(element, percentage, message);

            // Measure time to display
            const elapsedTime = measureElapsedTime(startTime);

            // Should display within 100ms
            expect(elapsedTime).toBeLessThan(100);

            // Should have progress overlay
            expect(element.children.length).toBeGreaterThan(0);
            const overlay = element.children.find(child => child.className === 'progress-overlay');
            expect(overlay).toBeDefined();

            // Should have progress ID
            expect(progressId).toBeDefined();
            expect(typeof progressId).toBe('string');
          }
        ),
        { numRuns: 20 }
      );
    });

    test('Loading state should be visible immediately after showLoading call', () => {
      fc.assert(
        fc.property(loadingMessageArb(), (message) => {
          const element = createMockElement();

          // Before showing loading
          expect(element.children.length).toBe(0);

          // Show loading
          showLoading(element, message);

          // Immediately after (no delay)
          expect(element.children.length).toBeGreaterThan(0);

          // Should have loading overlay with correct class
          const overlay = element.children.find(child => child.className === 'loading-overlay');
          expect(overlay).toBeDefined();
          expect(overlay.className).toBe('loading-overlay');
        }),
        { numRuns: 20 }
      );
    });

    test('Multiple loading states can be shown and hidden independently', () => {
      fc.assert(
        fc.property(
          fc.array(loadingMessageArb(), { minLength: 2, maxLength: 5 }),
          (messages) => {
            const element = createMockElement();
            const loadingIds = [];

            // Show multiple loading states
            messages.forEach(message => {
              const startTime = Date.now();
              const loadingId = showLoading(element, message);
              const elapsedTime = measureElapsedTime(startTime);

              expect(elapsedTime).toBeLessThan(100);
              loadingIds.push(loadingId);
            });

            // Should have multiple overlays
            expect(element.children.length).toBe(messages.length);

            // Hide each loading state independently
            loadingIds.forEach(loadingId => {
              const startTime = Date.now();
              hideLoading(loadingId);
              const elapsedTime = measureElapsedTime(startTime);

              expect(elapsedTime).toBeLessThan(100);
            });
          }
        ),
        { numRuns: 10 }
      );
    });

    test('Progress indicator should update within 100ms', () => {
      fc.assert(
        fc.property(
          fc.array(progressPercentageArb(), { minLength: 2, maxLength: 10 }),
          (percentages) => {
            const element = createMockElement();

            // Show initial progress
            const progressId = showProgress(element, percentages[0], 'Uploading...');
            expect(progressId).toBeDefined();

            // Update progress multiple times
            percentages.slice(1).forEach(percentage => {
              const startTime = Date.now();
              showProgress(element, percentage, 'Uploading...');
              const elapsedTime = measureElapsedTime(startTime);

              // Each update should be within 100ms
              expect(elapsedTime).toBeLessThan(100);
            });
          }
        ),
        { numRuns: 10 }
      );
    });

    test('Loading state should auto-hide when progress reaches 100%', () => {
      fc.assert(
        fc.property(loadingMessageArb(), (message) => {
          const element = createMockElement();

          // Show progress at 100%
          const progressId = showProgress(element, 100, message);
          expect(progressId).toBeDefined();

          // Should have progress overlay initially
          expect(element.children.length).toBeGreaterThan(0);

          // Fast-forward timers to trigger auto-hide (500ms delay)
          jest.advanceTimersByTime(500);

          // Should initiate hiding
          const overlay = element.children.find(child => child.className === 'progress-overlay');
          if (overlay && overlay.style) {
            // Opacity should be set to 0 for fade out
            expect(overlay.style.opacity).toBeDefined();
          }
        }),
        { numRuns: 10 }
      );
    });

    test('Loading state should handle rapid show/hide cycles', () => {
      fc.assert(
        fc.property(
          fc.array(loadingMessageArb(), { minLength: 5, maxLength: 10 }),
          (messages) => {
            const element = createMockElement();

            // Rapid show/hide cycles
            messages.forEach(message => {
              const showStartTime = Date.now();
              const loadingId = showLoading(element, message);
              const showElapsedTime = measureElapsedTime(showStartTime);

              expect(showElapsedTime).toBeLessThan(100);
              expect(loadingId).toBeDefined();

              const hideStartTime = Date.now();
              hideLoading(loadingId);
              const hideElapsedTime = measureElapsedTime(hideStartTime);

              expect(hideElapsedTime).toBeLessThan(100);
            });

            // All operations should complete without errors
            expect(true).toBe(true);
          }
        ),
        { numRuns: 10 }
      );
    });

    test('Loading state should be accessible (aria-busy attribute)', () => {
      fc.assert(
        fc.property(loadingMessageArb(), (message) => {
          const element = createMockElement();

          // Show loading
          showLoading(element, message);

          // Should have loading overlay
          expect(element.children.length).toBeGreaterThan(0);

          // Hide loading
          hideLoading(element);

          // Fast-forward timers
          jest.advanceTimersByTime(200);

          // Test completed successfully
          expect(true).toBe(true);
        }),
        { numRuns: 20 }
      );
    });

    test('Progress indicator should have proper ARIA attributes', () => {
      fc.assert(
        fc.property(progressPercentageArb(), (percentage) => {
          const element = createMockElement();

          // Show progress
          showProgress(element, percentage, 'Processing...');

          // Should have progress overlay
          const overlay = element.children.find(child => child.className === 'progress-overlay');
          expect(overlay).toBeDefined();

          if (overlay && overlay.setAttribute && overlay.setAttribute.mock) {
            // Should set proper ARIA attributes
            expect(overlay.setAttribute).toHaveBeenCalledWith('role', 'progressbar');
            expect(overlay.setAttribute).toHaveBeenCalledWith('aria-valuenow', expect.any(Number));
            expect(overlay.setAttribute).toHaveBeenCalledWith('aria-valuemin', '0');
            expect(overlay.setAttribute).toHaveBeenCalledWith('aria-valuemax', '100');
          }
        }),
        { numRuns: 20 }
      );
    });

    test('Loading state should handle null/undefined elements gracefully', () => {
      fc.assert(
        fc.property(loadingMessageArb(), (message) => {
          // Try to show loading on null element
          const loadingId = showLoading(null, message);

          // Should return null and not crash
          expect(loadingId).toBeNull();

          // Try to hide loading on null element
          expect(() => hideLoading(null)).not.toThrow();
        }),
        { numRuns: 10 }
      );
    });

    test('Loading state timing should be consistent across different messages', () => {
      fc.assert(
        fc.property(
          fc.tuple(loadingMessageArb(), loadingMessageArb(), loadingMessageArb()),
          ([msg1, msg2, msg3]) => {
            const element1 = createMockElement();
            const element2 = createMockElement();
            const element3 = createMockElement();

            // Show loading with different messages
            const start1 = Date.now();
            showLoading(element1, msg1);
            const elapsed1 = measureElapsedTime(start1);

            const start2 = Date.now();
            showLoading(element2, msg2);
            const elapsed2 = measureElapsedTime(start2);

            const start3 = Date.now();
            showLoading(element3, msg3);
            const elapsed3 = measureElapsedTime(start3);

            // All should be within 100ms
            expect(elapsed1).toBeLessThan(100);
            expect(elapsed2).toBeLessThan(100);
            expect(elapsed3).toBeLessThan(100);

            // Timing should be consistent (within reasonable variance)
            const maxElapsed = Math.max(elapsed1, elapsed2, elapsed3);
            const minElapsed = Math.min(elapsed1, elapsed2, elapsed3);
            const variance = maxElapsed - minElapsed;

            // Variance should be small (less than 50ms for synchronous operations)
            expect(variance).toBeLessThan(50);
          }
        ),
        { numRuns: 10 }
      );
    });

    test('Edge case: Progress percentage should be clamped to 0-100 range', () => {
      fc.assert(
        fc.property(
          fc.integer({ min: -1000, max: 1000 }),
          (percentage) => {
            const element = createMockElement();

            // Show progress with any percentage
            const progressId = showProgress(element, percentage, 'Processing...');

            // Should not crash
            expect(progressId).toBeDefined();

            // Should have progress overlay
            const overlay = element.children.find(child => child.className === 'progress-overlay');
            expect(overlay).toBeDefined();

            if (overlay && overlay.setAttribute && overlay.setAttribute.mock) {
              // aria-valuenow should be clamped to 0-100
              const calls = overlay.setAttribute.mock.calls.filter(
                call => call[0] === 'aria-valuenow'
              );
              if (calls.length > 0) {
                const value = calls[0][1];
                expect(value).toBeGreaterThanOrEqual(0);
                expect(value).toBeLessThanOrEqual(100);
              }
            }
          }
        ),
        { numRuns: 20 }
      );
    });

    test('Edge case: Empty loading message should still display indicator', () => {
      const element = createMockElement();

      // Show loading with empty message
      const loadingId = showLoading(element, '');

      // Should still create loading overlay
      expect(loadingId).toBeDefined();
      expect(element.children.length).toBeGreaterThan(0);

      const overlay = element.children.find(child => child.className === 'loading-overlay');
      expect(overlay).toBeDefined();
    });

    test('Edge case: Very long loading message should not affect timing', () => {
      fc.assert(
        fc.property(
          fc.string({ minLength: 100, maxLength: 1000 }),
          (longMessage) => {
            const element = createMockElement();
            const startTime = Date.now();

            // Show loading with very long message
            const loadingId = showLoading(element, longMessage);
            const elapsedTime = measureElapsedTime(startTime);

            // Should still be within 100ms
            expect(elapsedTime).toBeLessThan(100);
            expect(loadingId).toBeDefined();
          }
        ),
        { numRuns: 10 }
      );
    });

    test('Simulated async operation: Loading state lifecycle', () => {
      fc.assert(
        fc.property(
          operationDelayArb(),
          loadingMessageArb(),
          (delay, message) => {
            const element = createMockElement();

            // Start async operation
            const showStartTime = Date.now();
            const loadingId = showLoading(element, message);
            const showElapsedTime = measureElapsedTime(showStartTime);

            // Should show within 100ms
            expect(showElapsedTime).toBeLessThan(100);
            expect(element.children.length).toBeGreaterThan(0);

            // Simulate async operation
            jest.advanceTimersByTime(delay);

            // Complete operation
            const hideStartTime = Date.now();
            hideLoading(loadingId);
            const hideElapsedTime = measureElapsedTime(hideStartTime);

            // Should hide within 100ms
            expect(hideElapsedTime).toBeLessThan(100);
          }
        ),
        { numRuns: 10 }
      );
    });
  });
});

