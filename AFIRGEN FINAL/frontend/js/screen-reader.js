/**
 * Screen Reader Announcements Module
 * Provides accessible announcements for screen reader users
 */

// Store announcement regions
let politeRegion = null;
let assertiveRegion = null;

/**
 * Create ARIA live regions for announcements
 */
function createLiveRegions() {
  // Create polite announcement region (non-interrupting)
  politeRegion = document.createElement('div');
  politeRegion.id = 'sr-polite-announcer';
  politeRegion.className = 'sr-only';
  politeRegion.setAttribute('role', 'status');
  politeRegion.setAttribute('aria-live', 'polite');
  politeRegion.setAttribute('aria-atomic', 'true');
  document.body.appendChild(politeRegion);

  // Create assertive announcement region (interrupting)
  assertiveRegion = document.createElement('div');
  assertiveRegion.id = 'sr-assertive-announcer';
  assertiveRegion.className = 'sr-only';
  assertiveRegion.setAttribute('role', 'alert');
  assertiveRegion.setAttribute('aria-live', 'assertive');
  assertiveRegion.setAttribute('aria-atomic', 'true');
  document.body.appendChild(assertiveRegion);

  console.log('[ScreenReader] Live regions created');
}

/**
 * Announce a message to screen readers
 * @param {string} message - Message to announce
 * @param {string} priority - 'polite' or 'assertive' (default: 'polite')
 */
function announce(message, priority = 'polite') {
  if (!message) {
    return;
  }

  const region = priority === 'assertive' ? assertiveRegion : politeRegion;

  if (!region) {
    console.warn('[ScreenReader] Live region not initialized');
    return;
  }

  // Clear previous announcement
  region.textContent = '';

  // Add new announcement after a brief delay to ensure screen readers detect the change
  setTimeout(() => {
    region.textContent = message;
    console.log(`[ScreenReader] Announced (${priority}): ${message}`);
  }, 100);

  // Clear announcement after it's been read (5 seconds)
  setTimeout(() => {
    region.textContent = '';
  }, 5000);
}

/**
 * Announce status changes (non-interrupting)
 * @param {string} message - Status message
 */
function announceStatus(message) {
  announce(message, 'polite');
}

/**
 * Announce errors (interrupting)
 * @param {string} message - Error message
 */
function announceError(message) {
  announce(`Error: ${message}`, 'assertive');
}

/**
 * Announce success (non-interrupting)
 * @param {string} message - Success message
 */
function announceSuccess(message) {
  announce(`Success: ${message}`, 'polite');
}

/**
 * Announce loading state
 * @param {string} message - Loading message
 */
function announceLoading(message) {
  announce(`Loading: ${message}`, 'polite');
}

/**
 * Announce completion
 * @param {string} message - Completion message
 */
function announceComplete(message) {
  announce(`Complete: ${message}`, 'polite');
}

/**
 * Initialize screen reader announcements
 */
function initializeScreenReader() {
  console.log('[ScreenReader] Initializing screen reader support');

  // Create live regions
  createLiveRegions();

  // Integrate with existing UI functions
  integrateWithUI();

  console.log('[ScreenReader] Screen reader support initialized');
}

/**
 * Integrate screen reader announcements with existing UI functions
 */
function integrateWithUI() {
  // Intercept toast notifications to add screen reader announcements
  const originalShowToast = window.showToast;
  if (originalShowToast) {
    window.showToast = function(message, type = 'info', duration = 3000) {
      // Call original function
      originalShowToast(message, type, duration);

      // Add screen reader announcement
      if (type === 'error') {
        announceError(message);
      } else if (type === 'success') {
        announceSuccess(message);
      } else {
        announceStatus(message);
      }
    };
  }

  // Intercept loading states
  const originalShowLoading = window.showLoading;
  if (originalShowLoading) {
    window.showLoading = function(element, message = 'Loading...') {
      const loadingId = originalShowLoading(element, message);
      announceLoading(message);
      return loadingId;
    };
  }

  const originalHideLoading = window.hideLoading;
  if (originalHideLoading) {
    window.hideLoading = function(element) {
      originalHideLoading(element);
      announceComplete('Loading complete');
    };
  }

  // Intercept modal open/close
  const modalOverlay = document.getElementById('modal-overlay');
  if (modalOverlay) {
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.attributeName === 'class') {
          const isHidden = modalOverlay.classList.contains('hidden');
          const modalTitle = document.getElementById('modal-title-text');
          
          if (!isHidden && modalTitle) {
            announceStatus(`Dialog opened: ${modalTitle.textContent}`);
          } else if (isHidden) {
            announceStatus('Dialog closed');
          }
        }
      });
    });

    observer.observe(modalOverlay, {
      attributes: true,
      attributeFilter: ['class']
    });
  }
}

// Expose functions to window
window.ScreenReader = {
  announce,
  announceStatus,
  announceError,
  announceSuccess,
  announceLoading,
  announceComplete,
  initialize: initializeScreenReader
};

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeScreenReader);
} else {
  initializeScreenReader();
}
