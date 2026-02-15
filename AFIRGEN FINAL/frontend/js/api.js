/**
 * API Module - Handles all API communication with the backend
 */

/**
 * APIClient class - Centralized API communication with retry and caching
 */
class APIClient {
  constructor(baseURL = API_BASE, apiKey = API_KEY) {
    this.baseURL = baseURL;
    this.apiKey = apiKey;
    this.cache = new Map();
    this.defaultTimeout = 30000; // 30 seconds
  }

  /**
   * Make a generic request with timeout
   * @param {string} endpoint - API endpoint (relative to baseURL)
   * @param {Object} options - Fetch options
   * @returns {Promise<Response>} Fetch response
   */
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const timeout = options.timeout || this.defaultTimeout;

    // Add authentication headers
    const headers = {
      'X-API-Key': this.apiKey,
      ...options.headers
    };

    // Create abort controller for timeout
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

  /**
   * Make a GET request with optional caching
   * @param {string} endpoint - API endpoint
   * @param {Object} params - Query parameters
   * @param {Object} options - Additional options (includeCache: boolean, cacheTTL: number)
   * @returns {Promise<any>} Response data
   */
  async get(endpoint, params = {}, options = {}) {
    // Build query string
    const queryString = Object.keys(params).length > 0
      ? `?${new URLSearchParams(params).toString()}`
      : '';

    const fullEndpoint = endpoint + queryString;

    // Check cache if enabled (default: true for GET requests)
    const useCache = options.useCache !== false;
    if (useCache) {
      const cached = this.getCached(fullEndpoint);
      if (cached) {
        console.log(`Cache hit for ${fullEndpoint}`);
        return cached;
      }
    }

    // Wrap in retry logic
    const result = await this.retryRequest(async () => {
      const response = await this.request(fullEndpoint, {
        method: 'GET',
        ...options
      });

      if (!response.ok) {
        await handleAPIError(response, `GET ${endpoint}`);
        const error = new Error(`GET ${endpoint} failed with status ${response.status}`);
        error.status = response.status;
        throw error;
      }

      return await response.json();
    });

    // Cache the result if enabled
    if (useCache) {
      const cacheTTL = options.cacheTTL || 300000; // Default: 5 minutes
      this.setCached(fullEndpoint, result, cacheTTL);
    }

    return result;
  }

  /**
   * Make a POST request
   * @param {string} endpoint - API endpoint
   * @param {any} body - Request body (object or FormData)
   * @param {boolean} isFormData - Whether body is FormData
   * @param {Object} options - Additional options
   * @returns {Promise<any>} Response data
   */
  async post(endpoint, body, isFormData = false, options = {}) {
    // Wrap in retry logic
    return this.retryRequest(async () => {
      const requestOptions = {
        method: 'POST',
        ...options
      };

      if (isFormData) {
        requestOptions.body = body;
      } else {
        requestOptions.headers = {
          'Content-Type': 'application/json',
          ...options.headers
        };
        requestOptions.body = JSON.stringify(body);
      }

      const response = await this.request(endpoint, requestOptions);

      if (!response.ok) {
        await handleAPIError(response, `POST ${endpoint}`);
        const error = new Error(`POST ${endpoint} failed with status ${response.status}`);
        error.status = response.status;
        throw error;
      }

      return await response.json();
    });
  }

  /**
   * Get cached data
   * @param {string} key - Cache key
   * @returns {any|null} Cached data or null if not found/expired
   */
  getCached(key) {
    const cached = this.cache.get(key);
    if (!cached) {
      return null;
    }

    // Check if expired
    if (Date.now() > cached.expiry) {
      this.cache.delete(key);
      return null;
    }

    return cached.data;
  }

  /**
   * Set cached data
   * @param {string} key - Cache key
   * @param {any} data - Data to cache
   * @param {number} ttl - Time to live in milliseconds (default: 5 minutes)
   */
  setCached(key, data, ttl = 300000) {
    this.cache.set(key, {
      data,
      expiry: Date.now() + ttl
    });
  }

  /**
   * Clear all cached data
   */
  clearCache() {
    this.cache.clear();
  }
  /**
   * Clear all cached data
   */
  clearCache() {
    this.cache.clear();
  }

  /**
   * Retry a request with exponential backoff
   * @param {Function} fn - Async function to retry
   * @param {number} maxRetries - Maximum number of retry attempts (default: 3)
   * @param {number} backoff - Base delay in milliseconds (default: 1000)
   * @returns {Promise<any>} Result of the function
   */
  async retryRequest(fn, maxRetries = 3, backoff = 1000) {
    let lastError;

    for (let attempt = 0; attempt < maxRetries; attempt++) {
      try {
        // Log retry attempt
        if (attempt > 0) {
          console.log(`Retry attempt ${attempt + 1}/${maxRetries}`);
          if (window.showToast) {
            window.showToast(`Retrying... (Attempt ${attempt + 1}/${maxRetries})`, 'info', 2000);
          }
        }

        return await fn();
      } catch (error) {
        lastError = error;
        console.error(`Attempt ${attempt + 1} failed:`, error.message);

        // Don't retry on client errors (4xx) except 429 (rate limit)
        if (error.status >= 400 && error.status < 500 && error.status !== 429) {
          throw error;
        }

        // Don't retry on timeout errors after first attempt
        if (error.name === 'TimeoutError' && attempt > 0) {
          throw error;
        }

        // If this was the last attempt, throw the error
        if (attempt === maxRetries - 1) {
          break;
        }

        // Calculate exponential backoff delay: backoff * 2^attempt
        const delay = backoff * Math.pow(2, attempt);
        console.log(`Waiting ${delay}ms before retry...`);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }

    // All retries failed
    throw lastError;
  }
}

// API Base URL - configurable via environment or defaults to localhost
const API_BASE = window.ENV?.API_BASE_URL || 'http://localhost:8000';
const API_KEY = window.ENV?.API_KEY || '';

/**
 * Create headers with API key for authentication
 * @param {Object} additionalHeaders - Additional headers to include
 * @returns {Object} Headers object
 */
function getAuthHeaders(additionalHeaders = {}) {
  const headers = {
    'X-API-Key': API_KEY,
    ...additionalHeaders
  };
  return headers;
}

/**
 * Retry a function with exponential backoff
 * @param {Function} fn - Async function to retry
 * @param {number} maxRetries - Maximum number of retry attempts (default: 3)
 * @param {number} baseDelay - Base delay in milliseconds (default: 1000)
 * @returns {Promise<any>} Result of the function
 */
async function retryWithBackoff(fn, maxRetries = 3, baseDelay = 1000) {
  let lastError;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      // Log retry attempt
      if (attempt > 0) {
        console.log(`Retry attempt ${attempt + 1}/${maxRetries}`);
        if (window.showToast) {
          window.showToast(`Retrying... (Attempt ${attempt + 1}/${maxRetries})`, 'info', 2000);
        }
      }

      return await fn();
    } catch (error) {
      lastError = error;
      console.error(`Attempt ${attempt + 1} failed:`, error.message);

      // Don't retry on client errors (4xx) except 429 (rate limit)
      if (error.status >= 400 && error.status < 500 && error.status !== 429) {
        throw error;
      }

      // If this was the last attempt, throw the error
      if (attempt === maxRetries - 1) {
        break;
      }

      // Calculate exponential backoff delay: baseDelay * 2^attempt
      const delay = baseDelay * Math.pow(2, attempt);
      console.log(`Waiting ${delay}ms before retry...`);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }

  // All retries failed
  throw lastError;
}

/**
 * Process files and start FIR generation
 * @param {File} letterFile - Letter/document file
 * @param {File} audioFile - Audio file
 * @param {Function} onProgress - Optional progress callback for file upload
 * @returns {Promise<Object>} Response data with session_id
 */
async function processFiles(letterFile, audioFile, onProgress) {
  const formData = new FormData();

  if (letterFile) {
    if (letterFile.type.startsWith('image/')) {
      formData.append('image', letterFile);
    } else {
      const text = await letterFile.text();
      formData.append('text', text);
    }
  }

  if (audioFile) {
    formData.append('audio', audioFile);
  }

  // Wrap in retry logic
  return retryWithBackoff(async () => {
    // Create XMLHttpRequest for progress tracking
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();

      // Track upload progress
      if (onProgress) {
        xhr.upload.addEventListener('progress', (e) => {
          if (e.lengthComputable) {
            const percentComplete = (e.loaded / e.total) * 100;
            onProgress(percentComplete);
          }
        });
      }

      // Handle completion
      xhr.addEventListener('load', async () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const data = JSON.parse(xhr.responseText);
            if (!data.success) {
              reject(new Error(data.error));
            } else {
              resolve(data);
            }
          } catch (error) {
            reject(new Error('Failed to parse response'));
          }
        } else {
          // Use new error handling system for API errors
          const mockResponse = {
            status: xhr.status,
            statusText: xhr.statusText || 'Request failed',
            headers: { get: () => 'application/json' },
            json: async () => {
              try {
                return JSON.parse(xhr.responseText);
              } catch {
                return { error: xhr.responseText };
              }
            },
            url: `${API_BASE}/process`
          };
          const errorResult = await handleAPIError(mockResponse, 'file upload');
          const error = new Error(errorResult.message);
          error.status = xhr.status;
          reject(error);
        }
      });

      // Handle errors
      xhr.addEventListener('error', () => {
        const error = new Error('Network error occurred during file upload');
        handleNetworkError(error, 'file upload');
        reject(error);
      });

      xhr.addEventListener('abort', () => {
        const error = new Error('Upload aborted');
        handleNetworkError(error, 'file upload');
        reject(error);
      });

      // Open and send request
      xhr.open('POST', `${API_BASE}/process`);

      // Set headers
      const headers = getAuthHeaders();
      Object.keys(headers).forEach(key => {
        xhr.setRequestHeader(key, headers[key]);
      });

      xhr.send(formData);
    });
  });
}

/**
 * Validate current step content
 * @param {string} sessionId - Session ID
 * @param {boolean} approved - Whether content is approved
 * @param {string} userInput - User corrections or input
 * @returns {Promise<Object>} Validation response
 */
async function validateStep(sessionId, approved, userInput) {
  return retryWithBackoff(async () => {
    const response = await fetch(`${API_BASE}/validate`, {
      method: 'POST',
      headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({
        session_id: sessionId,
        approved,
        user_input: userInput
      })
    });

    if (!response.ok) {
      // Use new error handling system
      await handleAPIError(response, 'validation');
      const errorText = await response.text();
      const error = new Error(`Validation error: ${errorText}`);
      error.status = response.status;
      throw error;
    }

    const data = await response.json();
    if (!data.success) {
      // Use validation error handler for validation-specific errors
      const validationError = window.Validation.handleValidationError(
        data.message || 'Validation failed',
        'step validation'
      );
      throw new Error(validationError.message);
    }

    return data;
  });
}

/**
 * Regenerate content for current step
 * @param {string} sessionId - Session ID
 * @param {string} step - Current step name
 * @param {string} userInput - User corrections or input
 * @returns {Promise<Object>} Regeneration response
 */
async function regenerateStep(sessionId, step, userInput) {
  return retryWithBackoff(async () => {
    const response = await fetch(`${API_BASE}/regenerate/${sessionId}`, {
      method: 'POST',
      headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({
        step: step,
        user_input: userInput
      })
    });

    if (!response.ok) {
      // Use new error handling system
      await handleAPIError(response, 'content regeneration');
      const errorText = await response.text();
      const error = new Error(`Regeneration error: ${errorText}`);
      error.status = response.status;
      throw error;
    }

    const data = await response.json();

    if (!data.success) {
      // Use validation error handler for regeneration errors
      const validationError = window.Validation.handleValidationError(
        data.message || 'Regeneration failed',
        'content regeneration'
      );
      throw new Error(validationError.message);
    }

    return data;
  });
}

/**
 * Get session status
 * @param {string} sessionId - Session ID
 * @returns {Promise<Object>} Session status
 */
async function getSessionStatus(sessionId) {
  return retryWithBackoff(async () => {
    const response = await fetch(`${API_BASE}/session/${sessionId}/status`, {
      headers: getAuthHeaders()
    });

    if (!response.ok) {
      // Use new error handling system
      await handleAPIError(response, 'session status check');
      const errorText = await response.text();
      const error = new Error(`Status error: ${errorText}`);
      error.status = response.status;
      throw error;
    }

    return await response.json();
  });
}

/**
 * Get FIR by number
 * @param {string} firNumber - FIR number
 * @returns {Promise<Object>} FIR data
 */
async function getFIR(firNumber) {
  return retryWithBackoff(async () => {
    const response = await fetch(`${API_BASE}/fir/${firNumber}`, {
      headers: getAuthHeaders()
    });

    if (!response.ok) {
      // Use new error handling system
      await handleAPIError(response, 'FIR retrieval');
      const errorText = await response.text();
      const error = new Error(`FIR fetch error: ${errorText}`);
      error.status = response.status;
      throw error;
    }

    return await response.json();
  });
}

/**
 * Poll session status until completion or error
 * @param {string} sessionId - Session ID
 * @param {Function} onComplete - Callback when session completes
 * @param {Function} onError - Callback when session errors
 * @returns {number} Interval ID for clearing
 */
function pollSessionStatus(sessionId, onComplete, onError) {
  const interval = setInterval(async () => {
    if (!sessionId) {
      clearInterval(interval);
      return;
    }

    try {
      const status = await getSessionStatus(sessionId);

      if (status.status === 'completed') {
        const firNumber = status.validation_history?.at(-1)?.content?.fir_number || '';
        if (firNumber) {
          const firData = await getFIR(firNumber);
          onComplete(firData);
        }
        clearInterval(interval);
      } else if (status.status === 'error') {
        const error = new Error('Session processing failed');
        handleNetworkError(error, 'session processing');
        onError(error);
        clearInterval(interval);
      }
    } catch (error) {
      // Log but don't show toast for polling errors (they're background operations)
      console.error('Status poll error:', error);
      // Only call onError for critical failures
      if (error.message && error.message.includes('Failed to fetch')) {
        handleNetworkError(error, 'session status polling');
        onError(error);
        clearInterval(interval);
      }
    }
  }, 5000);

  return interval;
}

// Create default API client instance
const apiClient = new APIClient();

// Export functions and classes for use in other modules
window.API = {
  APIClient,
  apiClient,
  getAuthHeaders,
  processFiles,
  validateStep,
  regenerateStep,
  getSessionStatus,
  getFIR,
  pollSessionStatus,
  retryWithBackoff,
  handleNetworkError,
  handleAPIError
};

/**
 * Error code to user-friendly message mapping
 */
const ERROR_MESSAGES = {
  // Network errors
  'NETWORK_ERROR': 'Unable to connect to the server. Please check your internet connection.',
  'TIMEOUT': 'The request took too long to complete. Please try again.',
  'ABORT': 'The request was cancelled.',

  // API errors
  '400': 'Invalid request. Please check your input and try again.',
  '401': 'Authentication failed. Please refresh the page and try again.',
  '403': 'Access denied. You do not have permission to perform this action.',
  '404': 'The requested resource was not found.',
  '429': 'Too many requests. Please wait a moment and try again.',
  '500': 'Server error. Please try again later.',
  '502': 'Server is temporarily unavailable. Please try again later.',
  '503': 'Service is temporarily unavailable. Please try again later.',

  // Operation-specific errors
  'UPLOAD_FAILED': 'File upload failed. Please check your file and try again.',
  'VALIDATION_FAILED': 'Validation failed. Please review your input.',
  'REGENERATION_FAILED': 'Content regeneration failed. Please try again.',
  'SESSION_NOT_FOUND': 'Session not found. Please start a new FIR generation.',
  'FIR_NOT_FOUND': 'FIR not found. Please check the FIR number and try again.'
};

/**
 * Handle network errors with user-friendly messages
 * @param {Error} error - Network error object
 * @param {string} operation - Operation that failed (e.g., 'file upload', 'validation')
 * @returns {Object} Error details with user-friendly message
 */
function handleNetworkError(error, operation = 'request') {
  // Log detailed error information
  console.error('Network error:', {
    message: error.message,
    operation,
    timestamp: new Date().toISOString(),
    stack: error.stack
  });

  let errorCode = 'NETWORK_ERROR';
  let message = ERROR_MESSAGES.NETWORK_ERROR;
  let suggestion = 'Please check your internet connection and try again.';
  let isCritical = false;

  // Determine specific error type
  if (error.message.includes('timeout') || error.message.includes('Timeout')) {
    errorCode = 'TIMEOUT';
    message = ERROR_MESSAGES.TIMEOUT;
    suggestion = 'The server is taking longer than expected. Please try again.';
  } else if (error.message.includes('abort') || error.message.includes('Abort')) {
    errorCode = 'ABORT';
    message = ERROR_MESSAGES.ABORT;
    suggestion = 'You can try the operation again if needed.';
  } else if (error.message.includes('Failed to fetch')) {
    isCritical = true;
    suggestion = 'Unable to reach the server. Please check your connection.';
  }

  // Show toast notification with reload button for critical errors
  if (window.showToast) {
    if (isCritical) {
      showCriticalErrorToast(`${message} ${suggestion}`, operation);
    } else {
      window.showToast(`${message} ${suggestion}`, 'error', 7000);
    }
  }

  return {
    success: false,
    errorCode,
    message,
    suggestion,
    operation,
    isCritical,
    originalError: error.message,
    timestamp: new Date().toISOString()
  };
}

/**
 * Handle API errors with user-friendly messages
 * @param {Response} response - Fetch API response object
 * @param {string} operation - Operation that failed (e.g., 'file upload', 'validation')
 * @returns {Promise<Object>} Error details with user-friendly message
 */
async function handleAPIError(response, operation = 'request') {
  // Log detailed error information
  console.error('API error:', {
    status: response.status,
    statusText: response.statusText,
    operation,
    timestamp: new Date().toISOString(),
    url: response.url
  });

  const statusCode = response.status.toString();
  const message = ERROR_MESSAGES[statusCode] || 'An unexpected error occurred.';
  let suggestion = 'Please try again.';
  let details = '';
  let isCritical = false;

  // Try to extract error details from response
  try {
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      const data = await response.json();
      if (data.error) {
        details = data.error;
      } else if (data.message) {
        details = data.message;
      }
    } else {
      details = await response.text();
    }
  } catch (e) {
    console.warn('Could not parse error response:', e);
  }

  // Provide specific suggestions based on status code
  switch (statusCode) {
  case '400':
    suggestion = 'Please review your input and ensure all required fields are filled correctly.';
    break;
  case '401':
    suggestion = 'Please refresh the page to re-authenticate.';
    isCritical = true;
    break;
  case '403':
    suggestion = 'Please contact support if you believe you should have access.';
    isCritical = true;
    break;
  case '404':
    suggestion = 'Please verify the information and try again.';
    break;
  case '429':
    suggestion = 'Please wait a few moments before trying again.';
    break;
  case '500':
  case '502':
  case '503':
    suggestion = 'Our servers are experiencing issues. Please try again in a few minutes.';
    isCritical = true;
    break;
  }

  // Customize message based on operation
  const operationContext = operation ? ` during ${operation}` : '';
  const fullMessage = `${message}${operationContext ? ` ${operationContext}` : ''}`;

  // Show toast notification with reload button for critical errors
  if (window.showToast) {
    const toastMessage = details ? `${fullMessage}: ${details}` : `${fullMessage} ${suggestion}`;
    if (isCritical) {
      showCriticalErrorToast(toastMessage, operation);
    } else {
      window.showToast(toastMessage, 'error', 7000);
    }
  }

  return {
    success: false,
    errorCode: statusCode,
    message: fullMessage,
    suggestion,
    details,
    operation,
    isCritical,
    status: response.status,
    statusText: response.statusText,
    timestamp: new Date().toISOString()
  };
}

/**
 * Show critical error toast with reload button
 * @param {string} message - Error message
 * @param {string} operation - Operation that failed
 */
function showCriticalErrorToast(message, operation) {
  // Log critical error
  console.error('CRITICAL ERROR:', {
    message,
    operation,
    timestamp: new Date().toISOString(),
    userAgent: navigator.userAgent,
    url: window.location.href
  });

  // Create custom toast with reload button
  const toastContainer = document.getElementById('toast-container');
  if (!toastContainer) {
    console.error('Toast container not found');
    return;
  }

  const toast = document.createElement('div');
  toast.className = 'toast toast-error critical-error';
  toast.setAttribute('role', 'alert');
  toast.setAttribute('aria-live', 'assertive');

  const messageDiv = document.createElement('div');
  messageDiv.className = 'toast-message';
  messageDiv.textContent = message;

  const buttonContainer = document.createElement('div');
  buttonContainer.className = 'toast-actions';

  const reloadButton = document.createElement('button');
  reloadButton.className = 'toast-button';
  reloadButton.textContent = 'Reload Page';
  reloadButton.onclick = () => {
    console.log('User initiated page reload after critical error');
    window.location.reload();
  };

  const dismissButton = document.createElement('button');
  dismissButton.className = 'toast-button toast-button-secondary';
  dismissButton.textContent = 'Dismiss';
  dismissButton.onclick = () => {
    toast.remove();
  };

  buttonContainer.appendChild(reloadButton);
  buttonContainer.appendChild(dismissButton);

  toast.appendChild(messageDiv);
  toast.appendChild(buttonContainer);
  toastContainer.appendChild(toast);

  // Slide in animation
  setTimeout(() => toast.classList.add('show'), 10);

  // Don't auto-dismiss critical errors
}

