/**
 * Real-time Validation Feedback Module
 * Provides instant validation feedback for form inputs
 */

// Debounce timers for each input
const debounceTimers = new Map();

// Validation rules for different input types
const validationRules = {
  'search-input': {
    minLength: 0,
    maxLength: 100,
    pattern: null,
    required: false,
    errorMessage: 'Search query must be less than 100 characters'
  },
  'fir-search-input': {
    minLength: 0,
    maxLength: 100,
    pattern: null,
    required: false,
    errorMessage: 'Search query must be less than 100 characters'
  },
  'validation-input': {
    minLength: 0,
    maxLength: 500,
    pattern: null,
    required: false,
    errorMessage: 'Input must be less than 500 characters'
  }
};

/**
 * Debounce function to delay validation
 * @param {Function} func - Function to debounce
 * @param {number} delay - Delay in milliseconds
 * @param {string} key - Unique key for this debounce
 * @returns {Function} Debounced function
 */
function debounce(func, delay, key) {
  return function(...args) {
    // Clear existing timer
    if (debounceTimers.has(key)) {
      clearTimeout(debounceTimers.get(key));
    }

    // Set new timer
    const timer = setTimeout(() => {
      func.apply(this, args);
      debounceTimers.delete(key);
    }, delay);

    debounceTimers.set(key, timer);
  };
}

/**
 * Validate input value against rules
 * @param {HTMLInputElement} input - Input element
 * @param {Object} rules - Validation rules
 * @returns {Object} Validation result {valid, error}
 */
function validateInput(input, rules) {
  const value = input.value.trim();

  // Check required
  if (rules.required && !value) {
    return {
      valid: false,
      error: 'This field is required'
    };
  }

  // Skip other validations if empty and not required
  if (!value && !rules.required) {
    return { valid: true, error: null };
  }

  // Check min length
  if (rules.minLength && value.length < rules.minLength) {
    return {
      valid: false,
      error: `Minimum ${rules.minLength} characters required`
    };
  }

  // Check max length
  if (rules.maxLength && value.length > rules.maxLength) {
    return {
      valid: false,
      error: rules.errorMessage || `Maximum ${rules.maxLength} characters allowed`
    };
  }

  // Check pattern
  if (rules.pattern && !rules.pattern.test(value)) {
    return {
      valid: false,
      error: rules.errorMessage || 'Invalid format'
    };
  }

  return { valid: true, error: null };
}

/**
 * Show validation feedback on input
 * @param {HTMLInputElement} input - Input element
 * @param {boolean} valid - Whether input is valid
 * @param {string} error - Error message (if invalid)
 */
function showValidationFeedback(input, valid, error) {
  // Remove existing feedback
  removeValidationFeedback(input);

  // Add validation class
  if (valid) {
    input.classList.add('input-valid');
    input.classList.remove('input-invalid');
    input.setAttribute('aria-invalid', 'false');
  } else {
    input.classList.add('input-invalid');
    input.classList.remove('input-valid');
    input.setAttribute('aria-invalid', 'true');
  }

  // Add error message if invalid
  if (!valid && error) {
    const errorElement = document.createElement('div');
    errorElement.className = 'validation-error';
    errorElement.id = `${input.id}-error`;
    errorElement.textContent = error;
    errorElement.setAttribute('role', 'alert');

    // Insert after input
    input.parentNode.insertBefore(errorElement, input.nextSibling);

    // Link error to input for screen readers
    input.setAttribute('aria-describedby', errorElement.id);

    // Announce error to screen readers
    if (window.ScreenReader) {
      window.ScreenReader.announceError(error);
    }
  }

  // Add icon indicator
  addValidationIcon(input, valid);
}

/**
 * Remove validation feedback from input
 * @param {HTMLInputElement} input - Input element
 */
function removeValidationFeedback(input) {
  // Remove classes
  input.classList.remove('input-valid', 'input-invalid');

  // Remove error message
  const errorElement = document.getElementById(`${input.id}-error`);
  if (errorElement) {
    errorElement.remove();
  }

  // Remove icon
  const iconElement = input.parentNode.querySelector('.validation-icon');
  if (iconElement) {
    iconElement.remove();
  }

  // Remove ARIA attributes
  input.removeAttribute('aria-invalid');
  input.removeAttribute('aria-describedby');
}

/**
 * Add validation icon indicator
 * @param {HTMLInputElement} input - Input element
 * @param {boolean} valid - Whether input is valid
 */
function addValidationIcon(input, valid) {
  // Skip for file inputs
  if (input.type === 'file') {
    return;
  }

  // Create icon element
  const icon = document.createElement('span');
  icon.className = `validation-icon ${valid ? 'icon-valid' : 'icon-invalid'}`;
  icon.setAttribute('aria-hidden', 'true');
  icon.textContent = valid ? '✓' : '✗';

  // Insert after input
  input.parentNode.insertBefore(icon, input.nextSibling);
}

/**
 * Handle input event with debounced validation
 * @param {Event} event - Input event
 */
function handleInputEvent(event) {
  const input = event.target;
  const rules = validationRules[input.id];

  if (!rules) {
    return;
  }

  // Create debounced validation function
  const debouncedValidate = debounce(() => {
    const result = validateInput(input, rules);
    showValidationFeedback(input, result.valid, result.error);
  }, 300, input.id);

  // Call debounced validation
  debouncedValidate();
}

/**
 * Handle blur event (immediate validation)
 * @param {Event} event - Blur event
 */
function handleBlurEvent(event) {
  const input = event.target;
  const rules = validationRules[input.id];

  if (!rules) {
    return;
  }

  // Validate immediately on blur
  const result = validateInput(input, rules);
  showValidationFeedback(input, result.valid, result.error);
}

/**
 * Handle focus event (clear validation)
 * @param {Event} event - Focus event
 */
function handleFocusEvent(event) {
  const input = event.target;

  // Don't clear validation feedback on focus
  // Just ensure it's visible
}

/**
 * Attach validation listeners to an input
 * @param {HTMLInputElement} input - Input element
 */
function attachValidationListeners(input) {
  // Skip if no rules defined
  if (!validationRules[input.id]) {
    return;
  }

  // Add event listeners
  input.addEventListener('input', handleInputEvent);
  input.addEventListener('blur', handleBlurEvent);
  input.addEventListener('focus', handleFocusEvent);

  console.log(`[RealtimeValidation] Attached listeners to ${input.id}`);
}

/**
 * Initialize real-time validation for all inputs
 */
function initializeRealtimeValidation() {
  console.log('[RealtimeValidation] Initializing real-time validation');

  // Find all inputs with validation rules
  Object.keys(validationRules).forEach(inputId => {
    const input = document.getElementById(inputId);
    if (input) {
      attachValidationListeners(input);
    }
  });

  // Watch for dynamically added inputs (like validation-input in modals)
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      mutation.addedNodes.forEach((node) => {
        if (node.nodeType === Node.ELEMENT_NODE) {
          // Check if the node itself is an input
          if (node.id && validationRules[node.id]) {
            attachValidationListeners(node);
          }

          // Check for inputs within the node
          Object.keys(validationRules).forEach(inputId => {
            const input = node.querySelector ? node.querySelector(`#${inputId}`) : null;
            if (input) {
              attachValidationListeners(input);
            }
          });
        }
      });
    });
  });

  observer.observe(document.body, {
    childList: true,
    subtree: true
  });

  console.log('[RealtimeValidation] Real-time validation initialized');
}

/**
 * Add custom validation rule
 * @param {string} inputId - Input element ID
 * @param {Object} rules - Validation rules
 */
function addValidationRule(inputId, rules) {
  validationRules[inputId] = rules;

  // Attach listeners if input already exists
  const input = document.getElementById(inputId);
  if (input) {
    attachValidationListeners(input);
  }
}

/**
 * Validate all inputs in a form
 * @param {HTMLFormElement} form - Form element
 * @returns {boolean} Whether all inputs are valid
 */
function validateForm(form) {
  let allValid = true;

  const inputs = form.querySelectorAll('input, textarea, select');
  inputs.forEach(input => {
    const rules = validationRules[input.id];
    if (rules) {
      const result = validateInput(input, rules);
      showValidationFeedback(input, result.valid, result.error);
      if (!result.valid) {
        allValid = false;
      }
    }
  });

  return allValid;
}

// Expose functions to window
window.RealtimeValidation = {
  initialize: initializeRealtimeValidation,
  addValidationRule,
  validateForm,
  validateInput,
  showValidationFeedback,
  removeValidationFeedback
};

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeRealtimeValidation);
} else {
  initializeRealtimeValidation();
}
