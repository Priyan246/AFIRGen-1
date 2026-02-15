# Error Recovery Implementation

## Overview

This document describes the error recovery mechanisms implemented in the AFIRGen frontend application as part of task 6.2.

## Requirements (5.1.7)

The implementation satisfies requirement 5.1.7: "Retry logic with exponential backoff"

## Implemented Features

### 1. Automatic Retry for Network Errors

**Location:** `js/api.js` - `retryWithBackoff()` function

**Behavior:**
- Automatically retries failed requests up to 3 times
- Uses exponential backoff: 1s, 2s, 4s delays between attempts
- Shows toast notification: "Retrying... (Attempt X/3)"
- Only retries on:
  - Network errors (connection failures, timeouts)
  - 5xx server errors (500, 502, 503)
  - 429 rate limit errors
- Does NOT retry on:
  - 4xx client errors (400, 401, 403, 404) except 429
  - These indicate client-side issues that won't be fixed by retrying

**Usage:**
All API functions are wrapped with `retryWithBackoff()`:
- `processFiles()` - File upload
- `validateStep()` - Step validation
- `regenerateStep()` - Content regeneration
- `getSessionStatus()` - Session status check
- `getFIR()` - FIR retrieval

**Example:**
```javascript
async function validateStep(sessionId, approved, userInput) {
  return retryWithBackoff(async () => {
    const response = await fetch(`${API_BASE}/validate`, {
      method: 'POST',
      headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({ session_id: sessionId, approved, user_input: userInput })
    });
    
    if (!response.ok) {
      await handleAPIError(response, 'validation');
      const error = new Error(`Validation error`);
      error.status = response.status;
      throw error;
    }
    
    return await response.json();
  });
}
```

### 2. "Reload Page" Button for Critical Errors

**Location:** `js/api.js` - `showCriticalErrorToast()` function

**Behavior:**
- Critical errors show a special toast with two buttons:
  - **"Reload Page"** - Triggers `window.location.reload()`
  - **"Dismiss"** - Closes the toast
- Critical errors do NOT auto-dismiss (user must take action)
- Critical errors are logged with additional context:
  - User agent
  - Current URL
  - Timestamp
  - Operation that failed

**Critical Error Types:**
1. **Network Errors:**
   - "Failed to fetch" - Cannot reach server
   
2. **API Errors:**
   - 401 Unauthorized - Authentication failed
   - 403 Forbidden - Access denied
   - 500 Internal Server Error
   - 502 Bad Gateway
   - 503 Service Unavailable

**Non-Critical Errors:**
These show regular toasts without reload button:
- Timeout errors
- Abort errors
- 400 Bad Request
- 404 Not Found
- 429 Too Many Requests

**Example Toast:**
```
┌─────────────────────────────────────────────┐
│ ⚠️ Unable to connect. Please check your     │
│    internet connection.                     │
│                                             │
│  [Reload Page]  [Dismiss]                  │
└─────────────────────────────────────────────┘
```

**CSS Styling:**
```css
.toast.critical-error {
    flex-direction: column;
    align-items: stretch;
}

.toast-actions {
    display: flex;
    gap: 0.75rem;
}

.toast-button {
    padding: 0.5rem 1rem;
    border: 1px solid rgba(255, 255, 255, 0.3);
    background: rgba(255, 255, 255, 0.1);
    color: white;
    cursor: pointer;
}
```

### 3. Error Logging to Console

**Location:** `js/api.js` - `handleNetworkError()` and `handleAPIError()` functions

**Network Error Logging:**
```javascript
console.error('Network error:', {
  message: error.message,
  operation: 'file upload',
  timestamp: '2024-01-15T10:30:45.123Z',
  stack: 'Error: Network failure\n    at processFiles...'
});
```

**API Error Logging:**
```javascript
console.error('API error:', {
  status: 500,
  statusText: 'Internal Server Error',
  operation: 'validation',
  timestamp: '2024-01-15T10:30:45.123Z',
  url: 'http://localhost:8000/api/validate'
});
```

**Critical Error Logging:**
```javascript
console.error('CRITICAL ERROR:', {
  message: 'Unable to connect. Please check your internet connection.',
  operation: 'file upload',
  timestamp: '2024-01-15T10:30:45.123Z',
  userAgent: 'Mozilla/5.0...',
  url: 'http://localhost:3000/index.html'
});
```

**Benefits:**
- Detailed error information for debugging
- Timestamps for tracking when errors occurred
- Operation context to understand what failed
- Stack traces for network errors
- User agent and URL for critical errors

## Error Flow Diagram

```
┌─────────────────┐
│  API Request    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Try Request    │
└────────┬────────┘
         │
    ┌────┴────┐
    │ Success?│
    └────┬────┘
         │
    ┌────┴────────────────┐
    │                     │
   Yes                   No
    │                     │
    ▼                     ▼
┌─────────┐      ┌──────────────┐
│ Return  │      │ Check Error  │
│ Result  │      │    Type      │
└─────────┘      └──────┬───────┘
                        │
                   ┌────┴────────────────┐
                   │                     │
              Network/5xx            4xx (not 429)
                   │                     │
                   ▼                     ▼
           ┌──────────────┐      ┌──────────────┐
           │ Retry Count  │      │ Throw Error  │
           │   < Max?     │      │  (No Retry)  │
           └──────┬───────┘      └──────────────┘
                  │
             ┌────┴────┐
             │         │
            Yes       No
             │         │
             ▼         ▼
      ┌──────────┐  ┌──────────────┐
      │  Wait    │  │ Check if     │
      │ Backoff  │  │  Critical    │
      │  Delay   │  └──────┬───────┘
      └────┬─────┘         │
           │          ┌────┴────┐
           │          │         │
           │         Yes       No
           │          │         │
           │          ▼         ▼
           │   ┌──────────┐  ┌──────────┐
           │   │  Show    │  │  Show    │
           │   │ Critical │  │ Regular  │
           │   │  Toast   │  │  Toast   │
           │   │ + Reload │  └──────────┘
           │   └──────────┘
           │
           └──────► Retry Request
```

## Testing

### Unit Tests

**File:** `js/error-recovery.test.js`

**Test Coverage:**
- ✅ Retry succeeds on first attempt
- ✅ Retry succeeds after failures
- ✅ Exponential backoff timing
- ✅ Fails after max retries
- ✅ No retry on 4xx errors
- ✅ Retry on 429 rate limit
- ✅ Retry on 5xx errors
- ✅ Detailed error logging
- ✅ Critical error identification
- ✅ Reload button for critical errors
- ✅ No reload button for non-critical errors

**Test Results:**
```
Test Suites: 1 passed, 1 total
Tests:       17 passed, 17 total
```

### Manual Testing

**Test Page:** `test-error-recovery.html`

**Test Scenarios:**
1. Automatic retry with success on 2nd attempt
2. Automatic retry with failure on all attempts
3. No retry on 4xx errors
4. Retry on 429 rate limit
5. Critical network error with reload button
6. Critical 401 error with reload button
7. Critical 500 error with reload button
8. Non-critical timeout error (no reload button)
9. Non-critical 400 error (no reload button)
10. Non-critical 404 error (no reload button)
11. Error logging to console

**How to Test:**
1. Open `test-error-recovery.html` in browser
2. Open browser console (F12)
3. Click test buttons to trigger different error scenarios
4. Verify:
   - Retry toasts appear for retryable errors
   - Critical errors show reload button
   - Non-critical errors show regular toast
   - Console shows detailed error logs

## Integration with Existing Code

All API functions in `app.js` use the error recovery system:

**File Upload:**
```javascript
try {
  const data = await window.API.processFiles(letterFile, audioFile, updateProgress);
  // Success handling...
} catch (error) {
  // Error already handled by API module
  // Just clean up UI state
  window.hideLoading(loadingId);
}
```

**Validation:**
```javascript
try {
  const data = await window.API.validateStep(sessionId, approved, userInput);
  // Success handling...
} catch (error) {
  // Error already handled by API module
  window.hideLoading(validationLoadingId);
}
```

**Key Points:**
- API functions handle errors internally
- Retry logic is transparent to callers
- Toasts are shown automatically
- Callers only need to clean up UI state

## Configuration

**Retry Settings:**
```javascript
// In api.js
const MAX_RETRIES = 3;
const BASE_DELAY = 1000; // 1 second

// Delays: 1s, 2s, 4s
// Total max wait time: 7 seconds
```

**Toast Duration:**
```javascript
// Regular errors: 7 seconds
window.showToast(message, 'error', 7000);

// Retry notifications: 2 seconds
window.showToast('Retrying...', 'info', 2000);

// Critical errors: No auto-dismiss
// User must click "Reload Page" or "Dismiss"
```

## Future Enhancements

Potential improvements for future iterations:

1. **Configurable Retry Settings:**
   - Allow different retry counts per operation
   - Configurable backoff strategy (linear, exponential, jitter)

2. **Offline Queue:**
   - Queue failed requests when offline
   - Automatically retry when connection restored
   - Show pending operations count

3. **Error Analytics:**
   - Track error rates
   - Send error reports to backend
   - Alert on high error rates

4. **User Preferences:**
   - Allow users to disable auto-retry
   - Configurable toast duration
   - Option to always/never show reload button

5. **Advanced Recovery:**
   - Partial retry (resume file uploads)
   - Fallback to cached data
   - Alternative API endpoints

## Conclusion

The error recovery implementation provides:
- ✅ Automatic retry with exponential backoff
- ✅ Reload button for critical errors
- ✅ Comprehensive error logging
- ✅ User-friendly error messages
- ✅ Transparent integration with existing code
- ✅ Comprehensive test coverage

All requirements for task 6.2 have been successfully implemented and tested.
