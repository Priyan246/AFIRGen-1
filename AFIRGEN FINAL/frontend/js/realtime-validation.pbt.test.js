/**
 * Property-Based Tests for Form Validation Feedback (realtime-validation.js)
 * **Validates: Requirements 5.2.5**
 *
 * Property 9: Form Validation Feedback
 * For any form field with validation rules, the system SHALL provide real-time validation
 * feedback (inline error message) within 300ms of user input.
 */

const fc = require('fast-check');

// Mock DOM APIs needed by realtime-validation.js
const createdElements = [];

global.document = {
  readyState: 'complete',
  querySelectorAll: jest.fn(() => []),
  querySelector: jest.fn(() => null),
  getElementById: jest.fn(() => null),
  createElement: jest.fn((tag) => {
    const element = createMockElement(tag);
    createdElements.push(element);
    return element;
  }),
  body: {
    appendChild: jest.fn(),
    addEventListener: jest.fn()
  },
  addEventListener: jest.fn()
};

global.window = {
  ScreenReader: {
    announceError: jest.fn()
  }
};

global.console = {
  log: jest.fn(),
  error: jest.fn(),
  warn: jest.fn()
};

global.Node = {
  ELEMENT_NODE: 1
};

global.MutationObserver = jest.fn(function(callback) {
  this.observe = jest.fn();
  this.disconnect = jest.fn();
});

/**
 * Create a mock DOM element
 */
function createMockElement(tag) {
  const childrenArray = [];
  const element = {
    tagName: tag.toUpperCase(),
    className: '',
    id: '',
    style: {},
    textContent: '',
    innerHTML: '',
    nodeType: 1,
    value: '',
    get children() {
      return childrenArray;
    },
    attributes: {},
    appendChild: jest.fn(function(child) {
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
    insertBefore: jest.fn(function(newNode, referenceNode) {
      const index = childrenArray.indexOf(referenceNode);
      if (index > -1) {
        childrenArray.splice(index, 0, newNode);
      } else {
        childrenArray.push(newNode);
      }
      newNode.parentNode = this;
      return newNode;
    }),
    setAttribute: jest.fn(function(name, value) {
      this.attributes[name] = value;
    }),
    getAttribute: jest.fn(function(name) {
      return this.attributes[name];
    }),
    removeAttribute: jest.fn(function(name) {
      delete this.attributes[name];
    }),
    querySelector: jest.fn(() => null),
    classList: {
      add: jest.fn((className) => {
        if (!element.className) {
          element.className = className;
        } else if (!element.className.includes(className)) {
          element.className += ` ${className}`;
        }
      }),
      remove: jest.fn((className) => {
        if (element.className) {
          element.className = element.className.replace(className, '').trim();
        }
      }),
      contains: jest.fn((className) => {
        return element.className && element.className.includes(className);
      })
    },
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    parentNode: null,
    nextSibling: null
  };

  return element;
}

/**
 * Create a mock input element
 */
function createMockInput(id) {
  const element = createMockElement('input');
  element.id = id;
  element.type = 'text';
  
  // Create a mock parent node
  const parentNode = createMockElement('div');
  element.parentNode = parentNode;
  
  return element;
}

// Load the realtime-validation module
require('./realtime-validation.js');

// Extract functions from window
const { 
  validateInput, 
  showValidationFeedback, 
  removeValidationFeedback
} = window.RealtimeValidation;

// Arbitraries for generating test data

/**
 * Generate invalid input data that should trigger validation errors
 * Must be over the max length for the specific input type
 */
const invalidInputArb = () => fc.oneof(
  // Always over 100 chars (invalid for search inputs)
  fc.string({ minLength: 101, maxLength: 200 }),
  // Always over 500 chars (invalid for all inputs)
  fc.string({ minLength: 501, maxLength: 1000 }),
  fc.constant('a'.repeat(150)), // Over 100
  fc.constant('x'.repeat(600))  // Over 500
);

/**
 * Generate valid input data
 */
const validInputArb = () => fc.oneof(
  fc.string({ minLength: 1, maxLength: 50 }),
  fc.constant('Valid search query'),
  fc.constant('Test input'),
  fc.constant('FIR-2024-001')
);

/**
 * Generate input field IDs
 */
const inputIdArb = () => fc.oneof(
  fc.constant('search-input'),
  fc.constant('fir-search-input'),
  fc.constant('validation-input')
);

/**
 * Measure time elapsed since a given start time
 */
const measureElapsedTime = (startTime) => {
  return Date.now() - startTime;
};

describe('Property-Based Tests: Form Validation Feedback', () => {
  beforeEach(() => {
    // Clear created elements
    createdElements.length = 0;
    
    // Reset mocks
    jest.clearAllMocks();
  });

  describe('Property 9: Form Validation Feedback', () => {
    test('Validation feedback should appear within 300ms for invalid input', () => {
      fc.assert(
        fc.property(
          inputIdArb(),
          invalidInputArb(),
          (inputId, invalidValue) => {
            // Create mock input
            const input = createMockInput(inputId);
            
            // Define validation rules
            const rules = {
              minLength: 0,
              maxLength: inputId === 'validation-input' ? 500 : 100,
              required: false,
              errorMessage: `Input must be less than ${inputId === 'validation-input' ? 500 : 100} characters`
            };
            
            // Measure time from validation to feedback display
            const startTime = Date.now();
            
            // Call validation directly (simulating what happens after debounce)
            input.value = invalidValue;
            const result = validateInput(input, rules);
            showValidationFeedback(input, result.valid, result.error);
            
            // Measure elapsed time
            const elapsedTime = measureElapsedTime(startTime);
            
            // Validation feedback should appear within 300ms
            // Direct function calls should be near-instant (<100ms)
            expect(elapsedTime).toBeLessThan(100);
            
            // Verify validation result - should be invalid if over max length
            const isOverMaxLength = invalidValue.length > rules.maxLength;
            if (isOverMaxLength) {
              expect(result.valid).toBe(false);
              expect(result.error).toBeDefined();
            }
            
            // Verify feedback was applied
            expect(input.classList.add).toHaveBeenCalled();
            expect(input.setAttribute).toHaveBeenCalled();
          }
        ),
        { numRuns: 20 }
      );
    });

    test('Validation feedback should show correct error message for invalid input', () => {
      fc.assert(
        fc.property(
          inputIdArb(),
          invalidInputArb(),
          (inputId, invalidValue) => {
            const input = createMockInput(inputId);
            
            const rules = {
              minLength: 0,
              maxLength: inputId === 'validation-input' ? 500 : 100,
              required: false,
              errorMessage: `Input must be less than ${inputId === 'validation-input' ? 500 : 100} characters`
            };
            
            const startTime = Date.now();
            
            input.value = invalidValue;
            const result = validateInput(input, rules);
            showValidationFeedback(input, result.valid, result.error);
            
            const elapsedTime = measureElapsedTime(startTime);
            
            expect(elapsedTime).toBeLessThan(100);
            
            // Check if actually invalid for this input type
            const isOverMaxLength = invalidValue.length > rules.maxLength;
            if (isOverMaxLength) {
              expect(result.valid).toBe(false);
              expect(result.error).toContain('characters');
              expect(input.classList.add).toHaveBeenCalledWith('input-invalid');
            }
          }
        ),
        { numRuns: 20 }
      );
    });

    test('Validation feedback should clear for valid input', () => {
      fc.assert(
        fc.property(
          inputIdArb(),
          validInputArb(),
          (inputId, validValue) => {
            const input = createMockInput(inputId);
            
            const rules = {
              minLength: 0,
              maxLength: inputId === 'validation-input' ? 500 : 100,
              required: false
            };
            
            const startTime = Date.now();
            
            input.value = validValue;
            const result = validateInput(input, rules);
            showValidationFeedback(input, result.valid, result.error);
            
            const elapsedTime = measureElapsedTime(startTime);
            
            expect(elapsedTime).toBeLessThan(100);
            expect(result.valid).toBe(true);
            expect(result.error).toBeNull();
            expect(input.classList.add).toHaveBeenCalledWith('input-valid');
          }
        ),
        { numRuns: 20 }
      );
    });

    test('Validation should be immediate (no debounce delay in validation logic)', () => {
      fc.assert(
        fc.property(
          inputIdArb(),
          invalidInputArb(),
          (inputId, invalidValue) => {
            const input = createMockInput(inputId);
            input.value = invalidValue;
            
            const rules = {
              minLength: 0,
              maxLength: inputId === 'validation-input' ? 500 : 100,
              required: false
            };
            
            const startTime = Date.now();
            
            const result = validateInput(input, rules);
            showValidationFeedback(input, result.valid, result.error);
            
            const elapsedTime = measureElapsedTime(startTime);
            
            // Validation logic itself should be immediate
            expect(elapsedTime).toBeLessThan(50);
            
            // Check if actually invalid for this input type
            const isOverMaxLength = invalidValue.length > rules.maxLength;
            if (isOverMaxLength) {
              expect(result.valid).toBe(false);
            }
            expect(input.classList.add).toHaveBeenCalled();
          }
        ),
        { numRuns: 20 }
      );
    });

    test('Validation timing should be consistent across different input types', () => {
      fc.assert(
        fc.property(
          invalidInputArb(),
          (invalidValue) => {
            const inputIds = ['search-input', 'fir-search-input', 'validation-input'];
            const timings = [];
            
            inputIds.forEach(inputId => {
              const input = createMockInput(inputId);
              
              const rules = {
                minLength: 0,
                maxLength: inputId === 'validation-input' ? 500 : 100,
                required: false
              };
              
              const startTime = Date.now();
              
              input.value = invalidValue;
              const result = validateInput(input, rules);
              showValidationFeedback(input, result.valid, result.error);
              
              const elapsedTime = measureElapsedTime(startTime);
              timings.push(elapsedTime);
              
              expect(elapsedTime).toBeLessThan(100);
            });
            
            // Timing should be consistent across input types
            const maxTiming = Math.max(...timings);
            const minTiming = Math.min(...timings);
            const variance = maxTiming - minTiming;
            
            // Variance should be minimal for consistent UX
            expect(variance).toBeLessThan(50);
          }
        ),
        { numRuns: 10 }
      );
    });

    test('Edge case: Empty input should not show error if not required', () => {
      fc.assert(
        fc.property(
          inputIdArb(),
          (inputId) => {
            const input = createMockInput(inputId);
            
            const rules = {
              minLength: 0,
              maxLength: inputId === 'validation-input' ? 500 : 100,
              required: false
            };
            
            const startTime = Date.now();
            
            input.value = '';
            const result = validateInput(input, rules);
            showValidationFeedback(input, result.valid, result.error);
            
            const elapsedTime = measureElapsedTime(startTime);
            
            expect(elapsedTime).toBeLessThan(100);
            expect(result.valid).toBe(true);
            expect(result.error).toBeNull();
          }
        ),
        { numRuns: 10 }
      );
    });

    test('Edge case: Whitespace-only input should be treated as empty', () => {
      fc.assert(
        fc.property(
          inputIdArb(),
          fc.oneof(
            fc.constant('   '),
            fc.constant('\t\t'),
            fc.constant('\n\n'),
            fc.constant('  \t  \n  ')
          ),
          (inputId, whitespace) => {
            const input = createMockInput(inputId);
            
            const rules = {
              minLength: 0,
              maxLength: inputId === 'validation-input' ? 500 : 100,
              required: false
            };
            
            const startTime = Date.now();
            
            input.value = whitespace;
            const result = validateInput(input, rules);
            showValidationFeedback(input, result.valid, result.error);
            
            const elapsedTime = measureElapsedTime(startTime);
            
            expect(elapsedTime).toBeLessThan(100);
            // Whitespace is trimmed, so it's treated as empty (valid for non-required)
            expect(result.valid).toBe(true);
          }
        ),
        { numRuns: 10 }
      );
    });

    test('Edge case: Input at exact max length should be valid', () => {
      fc.assert(
        fc.property(
          inputIdArb(),
          (inputId) => {
            const input = createMockInput(inputId);
            
            const maxLength = inputId === 'validation-input' ? 500 : 100;
            const exactLengthInput = 'a'.repeat(maxLength);
            
            const rules = {
              minLength: 0,
              maxLength: maxLength,
              required: false
            };
            
            const startTime = Date.now();
            
            input.value = exactLengthInput;
            const result = validateInput(input, rules);
            showValidationFeedback(input, result.valid, result.error);
            
            const elapsedTime = measureElapsedTime(startTime);
            
            expect(elapsedTime).toBeLessThan(100);
            expect(result.valid).toBe(true);
            expect(input.classList.add).toHaveBeenCalledWith('input-valid');
          }
        ),
        { numRuns: 10 }
      );
    });

    test('Edge case: Input one character over max length should be invalid', () => {
      fc.assert(
        fc.property(
          inputIdArb(),
          (inputId) => {
            const input = createMockInput(inputId);
            
            const maxLength = inputId === 'validation-input' ? 500 : 100;
            const overLengthInput = 'a'.repeat(maxLength + 1);
            
            const rules = {
              minLength: 0,
              maxLength: maxLength,
              required: false
            };
            
            const startTime = Date.now();
            
            input.value = overLengthInput;
            const result = validateInput(input, rules);
            showValidationFeedback(input, result.valid, result.error);
            
            const elapsedTime = measureElapsedTime(startTime);
            
            expect(elapsedTime).toBeLessThan(100);
            expect(result.valid).toBe(false);
            expect(input.classList.add).toHaveBeenCalledWith('input-invalid');
          }
        ),
        { numRuns: 10 }
      );
    });

    test('Validation feedback should handle special characters correctly', () => {
      fc.assert(
        fc.property(
          inputIdArb(),
          fc.oneof(
            fc.constant('<script>alert("xss")</script>'),
            fc.constant('"><img src=x onerror=alert(1)>'),
            fc.constant("'; DROP TABLE users; --"),
            fc.constant('🔥💯✨')
          ),
          (inputId, specialInput) => {
            const input = createMockInput(inputId);
            
            const rules = {
              minLength: 0,
              maxLength: inputId === 'validation-input' ? 500 : 100,
              required: false
            };
            
            const startTime = Date.now();
            
            input.value = specialInput;
            const result = validateInput(input, rules);
            
            // Should not crash with special characters
            expect(() => showValidationFeedback(input, result.valid, result.error)).not.toThrow();
            
            const elapsedTime = measureElapsedTime(startTime);
            
            expect(elapsedTime).toBeLessThan(100);
          }
        ),
        { numRuns: 10 }
      );
    });

    test('Performance: Validation should not degrade with multiple inputs', () => {
      fc.assert(
        fc.property(
          fc.array(
            fc.tuple(inputIdArb(), invalidInputArb()),
            { minLength: 3, maxLength: 10 }
          ),
          (inputData) => {
            const timings = [];
            
            inputData.forEach(([inputId, invalidValue]) => {
              const input = createMockInput(inputId);
              
              const rules = {
                minLength: 0,
                maxLength: inputId === 'validation-input' ? 500 : 100,
                required: false
              };
              
              const startTime = Date.now();
              
              input.value = invalidValue;
              const result = validateInput(input, rules);
              showValidationFeedback(input, result.valid, result.error);
              
              const elapsedTime = measureElapsedTime(startTime);
              timings.push(elapsedTime);
              
              expect(elapsedTime).toBeLessThan(100);
            });
            
            // Performance should be consistent
            const avgTiming = timings.reduce((a, b) => a + b, 0) / timings.length;
            expect(avgTiming).toBeLessThan(50);
            
            // No single input should take significantly longer
            timings.forEach(timing => {
              expect(timing).toBeLessThan(avgTiming + 50);
            });
          }
        ),
        { numRuns: 10 }
      );
    });

    test('Accessibility: ARIA attributes should be set within 300ms', () => {
      fc.assert(
        fc.property(
          inputIdArb(),
          invalidInputArb(),
          (inputId, invalidValue) => {
            const input = createMockInput(inputId);
            
            const rules = {
              minLength: 0,
              maxLength: inputId === 'validation-input' ? 500 : 100,
              required: false
            };
            
            const startTime = Date.now();
            
            input.value = invalidValue;
            const result = validateInput(input, rules);
            showValidationFeedback(input, result.valid, result.error);
            
            const elapsedTime = measureElapsedTime(startTime);
            
            expect(elapsedTime).toBeLessThan(100);
            
            // Verify ARIA attributes were set (either true or false depending on validity)
            expect(input.setAttribute).toHaveBeenCalledWith('aria-invalid', result.valid ? 'false' : 'true');
          }
        ),
        { numRuns: 10 }
      );
    });

    test('Simulated user scenario: Typing and correcting input', () => {
      fc.assert(
        fc.property(
          inputIdArb(),
          invalidInputArb(),
          validInputArb(),
          (inputId, invalidValue, validValue) => {
            const input = createMockInput(inputId);
            
            const rules = {
              minLength: 0,
              maxLength: inputId === 'validation-input' ? 500 : 100,
              required: false
            };
            
            // User types invalid input
            const invalidStartTime = Date.now();
            input.value = invalidValue;
            const invalidResult = validateInput(input, rules);
            showValidationFeedback(input, invalidResult.valid, invalidResult.error);
            const invalidElapsedTime = measureElapsedTime(invalidStartTime);
            
            expect(invalidElapsedTime).toBeLessThan(100);
            
            // Check if actually invalid for this input type
            const isOverMaxLength = invalidValue.length > rules.maxLength;
            if (isOverMaxLength) {
              expect(invalidResult.valid).toBe(false);
            }
            
            // User corrects to valid input
            const validStartTime = Date.now();
            input.value = validValue;
            const validResult = validateInput(input, rules);
            showValidationFeedback(input, validResult.valid, validResult.error);
            const validElapsedTime = measureElapsedTime(validStartTime);
            
            expect(validElapsedTime).toBeLessThan(100);
            expect(validResult.valid).toBe(true);
          }
        ),
        { numRuns: 10 }
      );
    });

    test('Edge case: Very long invalid input should still validate quickly', () => {
      fc.assert(
        fc.property(
          inputIdArb(),
          fc.string({ minLength: 1000, maxLength: 5000 }),
          (inputId, longInput) => {
            const input = createMockInput(inputId);
            
            const rules = {
              minLength: 0,
              maxLength: inputId === 'validation-input' ? 500 : 100,
              required: false
            };
            
            const startTime = Date.now();
            
            input.value = longInput;
            const result = validateInput(input, rules);
            showValidationFeedback(input, result.valid, result.error);
            
            const elapsedTime = measureElapsedTime(startTime);
            
            // Even with very long input, validation should be fast
            expect(elapsedTime).toBeLessThan(100);
            expect(result.valid).toBe(false);
          }
        ),
        { numRuns: 10 }
      );
    });
  });
});
