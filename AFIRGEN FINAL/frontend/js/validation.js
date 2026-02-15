/**
 * Validation Module - Handles file and input validation
 * Requirements: 5.3.2, 5.3.3
 */

// Magic number signatures for MIME type validation
const MAGIC_NUMBERS = {
  'image/jpeg': [
    [0xFF, 0xD8, 0xFF]
  ],
  'image/png': [
    [0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]
  ],
  'application/pdf': [
    [0x25, 0x50, 0x44, 0x46] // %PDF
  ],
  'audio/wav': [
    [0x52, 0x49, 0x46, 0x46] // RIFF
  ],
  'audio/mpeg': [
    [0xFF, 0xFB], // MP3 with MPEG-1 Layer 3
    [0xFF, 0xF3], // MP3 with MPEG-2 Layer 3
    [0xFF, 0xF2], // MP3 with MPEG-2.5 Layer 3
    [0x49, 0x44, 0x33] // ID3
  ]
};

/**
 * Validate file MIME type using magic number check
 * @param {File} file - File to validate
 * @returns {Promise<Object>} Validation result with success flag and detected MIME type
 */
async function validateMimeType(file) {
  if (!file) {
    return { success: false, error: 'No file provided' };
  }

  try {
    // Read first 8 bytes for magic number check
    const slice = file.slice(0, 8);
    const arrayBuffer = await slice.arrayBuffer();
    const bytes = new Uint8Array(arrayBuffer);

    // Check against known magic numbers
    for (const [mimeType, signatures] of Object.entries(MAGIC_NUMBERS)) {
      for (const signature of signatures) {
        let matches = true;
        for (let i = 0; i < signature.length; i++) {
          if (bytes[i] !== signature[i]) {
            matches = false;
            break;
          }
        }
        if (matches) {
          return { success: true, mimeType };
        }
      }
    }

    return {
      success: false,
      error: 'File type could not be verified. The file may be corrupted or of an unsupported type.'
    };
  } catch (error) {
    // Use new error handling system for file validation errors
    const validationError = handleValidationError(
      { error: `Failed to read file: ${error.message}` },
      'file type verification'
    );
    return {
      success: false,
      error: validationError.errors[0].message
    };
  }
}

/**
 * Validate file type by extension
 * @param {File} file - File to validate
 * @param {Array<string>} allowedTypes - Array of allowed file extensions (e.g., ['.jpg', '.png'])
 * @returns {Object} Validation result with success flag and error message
 */
function validateFileType(file, allowedTypes = ['.jpg', '.jpeg', '.png', '.pdf', '.wav', '.mp3']) {
  if (!file) {
    return { success: false, error: 'No file provided' };
  }

  const fileName = file.name.toLowerCase();
  const hasValidExtension = allowedTypes.some(type => fileName.endsWith(type.toLowerCase()));

  if (!hasValidExtension) {
    return {
      success: false,
      error: `File type not allowed. Allowed types: ${allowedTypes.join(', ')}`
    };
  }

  return { success: true };
}

/**
 * Validate file size
 * @param {File} file - File to validate
 * @param {number} maxSize - Maximum file size in bytes (default: 10MB)
 * @returns {Object} Validation result with success flag and error message
 */
function validateFileSize(file, maxSize = 10 * 1024 * 1024) {
  if (!file) {
    return { success: false, error: 'No file provided' };
  }

  if (file.size > maxSize) {
    const maxSizeMB = (maxSize / (1024 * 1024)).toFixed(2);
    const fileSizeMB = (file.size / (1024 * 1024)).toFixed(2);
    return {
      success: false,
      error: `File size (${fileSizeMB}MB) exceeds maximum allowed size of ${maxSizeMB}MB`
    };
  }

  return { success: true };
}

/**
 * Validate file type, size, and MIME type
 * @param {File} file - File to validate
 * @param {Object} options - Validation options
 * @param {number} options.maxSize - Maximum file size in bytes (default: 10MB)
 * @param {Array<string>} options.allowedTypes - Array of allowed file extensions
 * @param {boolean} options.checkMimeType - Whether to perform magic number check (default: true)
 * @returns {Promise<Object>} Validation result with success flag and error message
 */
async function validateFile(file, options = {}) {
  const {
    maxSize = 10 * 1024 * 1024, // 10MB default
    allowedTypes = ['.jpg', '.jpeg', '.png', '.pdf', '.wav', '.mp3'],
    checkMimeType = true
  } = options;

  if (!file) {
    return { success: false, error: 'No file provided' };
  }

  // Check file size
  const sizeResult = validateFileSize(file, maxSize);
  if (!sizeResult.success) {
    return sizeResult;
  }

  // Check file type by extension
  const typeResult = validateFileType(file, allowedTypes);
  if (!typeResult.success) {
    return typeResult;
  }

  // Check MIME type with magic number validation
  if (checkMimeType) {
    const mimeResult = await validateMimeType(file);
    if (!mimeResult.success) {
      return mimeResult;
    }
  }

  return { success: true };
}

/**
 * Validate text input with format checks
 * @param {string} text - Text to validate
 * @param {Object} options - Validation options
 * @param {number} options.minLength - Minimum length (default: 1)
 * @param {number} options.maxLength - Maximum length (default: 10000)
 * @param {boolean} options.required - Whether field is required (default: true)
 * @param {string} options.format - Format to validate: 'email', 'phone', 'alphanumeric', 'numeric', 'alpha'
 * @param {RegExp} options.pattern - Custom regex pattern to match
 * @param {boolean} options.noSpecialChars - Disallow special characters (default: false)
 * @returns {Object} Validation result with success flag and error message
 */
function validateText(text, options = {}) {
  const {
    minLength = 1,
    maxLength = 10000,
    required = true,
    format = null,
    pattern = null,
    noSpecialChars = false
  } = options;

  // Check if required
  if (required && (!text || text.trim().length === 0)) {
    return { success: false, error: 'Text is required' };
  }

  // If not required and empty, return success
  if (!required && (!text || text.trim().length === 0)) {
    return { success: true };
  }

  // Check length constraints
  if (text && text.length < minLength) {
    return {
      success: false,
      error: `Text must be at least ${minLength} characters`
    };
  }

  if (text && text.length > maxLength) {
    return {
      success: false,
      error: `Text must not exceed ${maxLength} characters`
    };
  }

  // Check for special characters if not allowed
  if (noSpecialChars && text) {
    const specialCharsRegex = /[<>'"&;]/;
    if (specialCharsRegex.test(text)) {
      return {
        success: false,
        error: 'Text contains invalid special characters'
      };
    }
  }

  // Format validation
  if (format && text) {
    switch (format) {
    case 'email':
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(text)) {
        return { success: false, error: 'Invalid email format' };
      }
      break;

    case 'phone':
      // Accepts formats: +1234567890, 123-456-7890, (123) 456-7890, etc.
      const phoneRegex = /^[\d\s\-\+\(\)]+$/;
      const digitsOnly = text.replace(/\D/g, '');
      if (!phoneRegex.test(text) || digitsOnly.length < 10 || digitsOnly.length > 15) {
        return { success: false, error: 'Invalid phone number format' };
      }
      break;

    case 'alphanumeric':
      const alphanumericRegex = /^[a-zA-Z0-9\s]+$/;
      if (!alphanumericRegex.test(text)) {
        return { success: false, error: 'Text must contain only letters and numbers' };
      }
      break;

    case 'numeric':
      const numericRegex = /^[0-9]+$/;
      if (!numericRegex.test(text)) {
        return { success: false, error: 'Text must contain only numbers' };
      }
      break;

    case 'alpha':
      const alphaRegex = /^[a-zA-Z\s]+$/;
      if (!alphaRegex.test(text)) {
        return { success: false, error: 'Text must contain only letters' };
      }
      break;

    default:
      return { success: false, error: `Unknown format: ${format}` };
    }
  }

  // Custom pattern validation
  if (pattern && text) {
    if (!pattern.test(text)) {
      return {
        success: false,
        error: 'Text does not match required format'
      };
    }
  }

  return { success: true };
}

/**
 * Sanitize user input to prevent XSS attacks
 * @param {string} input - Input to sanitize
 * @param {Object} options - Sanitization options
 * @param {boolean} options.stripTags - Remove all HTML tags (default: true)
 * @param {boolean} options.escapeQuotes - Escape quotes (default: true)
 * @param {boolean} options.trimWhitespace - Trim leading/trailing whitespace (default: true)
 * @returns {string} Sanitized input
 */
function sanitizeInput(input, options = {}) {
  const {
    stripTags = true,
    escapeQuotes = true,
    trimWhitespace = true
  } = options;

  if (!input) {
    return '';
  }

  let sanitized = input;

  // Trim whitespace if requested
  if (trimWhitespace) {
    sanitized = sanitized.trim();
  }

  // Strip or escape HTML tags
  if (stripTags) {
    // Use DOM API to escape HTML entities
    const div = document.createElement('div');
    div.textContent = sanitized;
    sanitized = div.innerHTML;
  }

  // Additional escaping for quotes if needed
  if (escapeQuotes) {
    sanitized = sanitized
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // Remove control characters (except newlines and tabs)
  sanitized = sanitized.replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, '');

  // Remove null bytes
  sanitized = sanitized.replace(/\0/g, '');

  return sanitized;
}

/**
 * Validate form data with comprehensive field validation
 * @param {FormData|Object} formData - Form data to validate
 * @param {Object} rules - Validation rules for each field
 * @returns {Object} Validation result with success flag and errors array
 *
 * @example
 * const rules = {
 *   email: { required: true, format: 'email' },
 *   phone: { required: false, format: 'phone' },
 *   name: { required: true, minLength: 2, maxLength: 50 }
 * };
 * const result = validateForm(formData, rules);
 */
function validateForm(formData, rules = {}) {
  const errors = [];
  const fieldValues = {};

  // Convert FormData to object if needed
  if (formData instanceof FormData) {
    for (const [key, value] of formData.entries()) {
      fieldValues[key] = value;
    }
  } else {
    Object.assign(fieldValues, formData);
  }

  // If no rules provided, just check that form is not empty
  if (Object.keys(rules).length === 0) {
    if (Object.keys(fieldValues).length === 0) {
      errors.push({ field: 'form', message: 'Form is empty' });
    }
  } else {
    // Validate each field according to rules
    for (const [fieldName, fieldRules] of Object.entries(rules)) {
      const value = fieldValues[fieldName];

      // Validate the field using validateText
      const result = validateText(value, fieldRules);

      if (!result.success) {
        errors.push({
          field: fieldName,
          message: result.error
        });
      }
    }
  }

  if (errors.length > 0) {
    return { success: false, errors };
  }

  return { success: true };
}

// Export functions for use in other modules
window.Validation = {
  validateFile,
  validateFileType,
  validateFileSize,
  validateMimeType,
  validateText,
  sanitizeInput,
  validateForm,
  handleValidationError
};

/**
 * Validation error code to user-friendly message mapping
 */
const VALIDATION_ERROR_MESSAGES = {
  'FILE_TYPE_INVALID': 'The file type is not supported.',
  'FILE_SIZE_EXCEEDED': 'The file is too large.',
  'FILE_MIME_INVALID': 'The file type could not be verified.',
  'TEXT_REQUIRED': 'This field is required.',
  'TEXT_TOO_SHORT': 'The text is too short.',
  'TEXT_TOO_LONG': 'The text is too long.',
  'TEXT_INVALID_FORMAT': 'The text format is invalid.',
  'TEXT_SPECIAL_CHARS': 'The text contains invalid characters.',
  'FORM_EMPTY': 'The form cannot be empty.',
  'FORM_INVALID': 'Some fields contain invalid data.'
};

/**
 * Handle validation errors with user-friendly messages
 * @param {Object|Array} errors - Validation error(s) from validation functions
 * @param {string} context - Context where validation failed (e.g., 'file upload', 'form submission')
 * @returns {Object} Error details with user-friendly messages
 */
function handleValidationError(errors, context = 'validation') {
  console.warn('Validation error:', errors);

  // Normalize errors to array format
  let errorList = [];

  if (Array.isArray(errors)) {
    errorList = errors;
  } else if (errors && typeof errors === 'object') {
    if (errors.errors && Array.isArray(errors.errors)) {
      // Form validation result format
      errorList = errors.errors;
    } else if (errors.error) {
      // Single error format
      errorList = [{ message: errors.error }];
    } else {
      // Generic object format
      errorList = [errors];
    }
  } else if (typeof errors === 'string') {
    // String error message
    errorList = [{ message: errors }];
  }

  // Map errors to user-friendly messages
  const mappedErrors = errorList.map(error => {
    const message = error.message || error.error || 'Validation failed';
    const field = error.field || '';
    let suggestion = '';
    let errorCode = 'VALIDATION_ERROR';

    // Determine error code and suggestion based on message content
    if (message.includes('file type') || message.includes('File type')) {
      errorCode = 'FILE_TYPE_INVALID';
      suggestion = 'Please upload a file in one of these formats: JPG, PNG, PDF, WAV, or MP3.';
    } else if (message.includes('file size') || message.includes('File size')) {
      errorCode = 'FILE_SIZE_EXCEEDED';
      suggestion = 'Please upload a file smaller than 10MB.';
    } else if (message.includes('MIME type') || message.includes('could not be verified')) {
      errorCode = 'FILE_MIME_INVALID';
      suggestion = 'The file may be corrupted. Please try a different file.';
    } else if (message.includes('required')) {
      errorCode = 'TEXT_REQUIRED';
      suggestion = field ? `Please enter a value for ${field}.` : 'Please fill in all required fields.';
    } else if (message.includes('too short') || message.includes('at least')) {
      errorCode = 'TEXT_TOO_SHORT';
      suggestion = 'Please enter more text to meet the minimum length requirement.';
    } else if (message.includes('too long') || message.includes('exceed')) {
      errorCode = 'TEXT_TOO_LONG';
      suggestion = 'Please shorten your text to meet the maximum length requirement.';
    } else if (message.includes('format') || message.includes('invalid')) {
      errorCode = 'TEXT_INVALID_FORMAT';
      suggestion = 'Please check the format and try again.';
    } else if (message.includes('special characters')) {
      errorCode = 'TEXT_SPECIAL_CHARS';
      suggestion = 'Please remove any special characters like <, >, &, or quotes.';
    } else if (message.includes('empty')) {
      errorCode = 'FORM_EMPTY';
      suggestion = 'Please fill in at least one field.';
    }

    return {
      field,
      message,
      suggestion,
      errorCode
    };
  });

  // Create summary message
  const errorCount = mappedErrors.length;
  let summaryMessage = '';

  if (errorCount === 1) {
    const error = mappedErrors[0];
    summaryMessage = error.field
      ? `${error.field}: ${error.message}`
      : error.message;
  } else {
    summaryMessage = `${errorCount} validation errors found`;
  }

  // Add context if provided
  const contextMessage = context ? ` during ${context}` : '';
  const fullMessage = `${summaryMessage}${contextMessage}`;

  // Show toast notification with first error
  if (window.showToast && mappedErrors.length > 0) {
    const firstError = mappedErrors[0];
    const toastMessage = firstError.suggestion
      ? `${firstError.message}. ${firstError.suggestion}`
      : firstError.message;

    window.showToast(toastMessage, 'warning', 6000);
  }

  return {
    success: false,
    errorCode: 'VALIDATION_ERROR',
    message: fullMessage,
    errors: mappedErrors,
    context,
    count: errorCount
  };
}

