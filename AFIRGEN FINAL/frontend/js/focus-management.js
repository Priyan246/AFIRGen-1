/**
 * Focus Management Module
 * Handles focus trapping in modals and focus restoration
 */

// Store the element that triggered the modal
let lastFocusedElement = null;

// Store active focus trap
let activeFocusTrap = null;

/**
 * Get all focusable elements within a container
 * @param {HTMLElement} container - Container element
 * @returns {Array<HTMLElement>} Array of focusable elements
 */
function getFocusableElements(container) {
  const focusableSelectors = [
    'a[href]',
    'button:not([disabled])',
    'textarea:not([disabled])',
    'input:not([disabled])',
    'select:not([disabled])',
    '[tabindex]:not([tabindex="-1"])'
  ].join(', ');

  return Array.from(container.querySelectorAll(focusableSelectors));
}

/**
 * Trap focus within a container (for modals)
 * @param {HTMLElement} container - Container to trap focus in
 */
function trapFocus(container) {
  // Store the currently focused element
  lastFocusedElement = document.activeElement;

  // Get all focusable elements
  const focusableElements = getFocusableElements(container);

  if (focusableElements.length === 0) {
    console.warn('[FocusManagement] No focusable elements found in container');
    return;
  }

  const firstElement = focusableElements[0];
  const lastElement = focusableElements[focusableElements.length - 1];

  // Focus trap handler
  const handleKeyDown = (e) => {
    if (e.key !== 'Tab') {
      return;
    }

    // Shift + Tab (backwards)
    if (e.shiftKey) {
      if (document.activeElement === firstElement) {
        e.preventDefault();
        lastElement.focus();
      }
    }
    // Tab (forwards)
    else {
      if (document.activeElement === lastElement) {
        e.preventDefault();
        firstElement.focus();
      }
    }
  };

  // Add event listener
  container.addEventListener('keydown', handleKeyDown);

  // Store trap info for cleanup
  activeFocusTrap = {
    container,
    handler: handleKeyDown
  };

  // Move focus to first element
  setTimeout(() => {
    firstElement.focus();
  }, 100);

  console.log('[FocusManagement] Focus trap activated');
}

/**
 * Release focus trap and restore focus to previous element
 */
function releaseFocusTrap() {
  if (!activeFocusTrap) {
    return;
  }

  // Remove event listener
  activeFocusTrap.container.removeEventListener('keydown', activeFocusTrap.handler);
  activeFocusTrap = null;

  // Restore focus to previous element
  if (lastFocusedElement && typeof lastFocusedElement.focus === 'function') {
    setTimeout(() => {
      lastFocusedElement.focus();
    }, 100);
  }

  lastFocusedElement = null;

  console.log('[FocusManagement] Focus trap released');
}

/**
 * Move focus to a specific element
 * @param {HTMLElement|string} element - Element or selector
 */
function moveFocusTo(element) {
  const targetElement = typeof element === 'string' 
    ? document.querySelector(element) 
    : element;

  if (!targetElement) {
    console.warn('[FocusManagement] Target element not found');
    return;
  }

  // Make element focusable if it's not already
  if (!targetElement.hasAttribute('tabindex')) {
    targetElement.setAttribute('tabindex', '-1');
  }

  setTimeout(() => {
    targetElement.focus();
  }, 100);
}

/**
 * Initialize focus management for modals
 */
function initializeFocusManagement() {
  console.log('[FocusManagement] Initializing focus management');

  // Handle modal open events
  const modalOverlay = document.getElementById('modal-overlay');
  if (modalOverlay) {
    // Use MutationObserver to detect when modal becomes visible
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.attributeName === 'class') {
          const isHidden = modalOverlay.classList.contains('hidden');
          
          if (!isHidden && !activeFocusTrap) {
            // Modal opened - trap focus
            const modalContent = modalOverlay.querySelector('.modal-content');
            if (modalContent) {
              trapFocus(modalContent);
            }
          } else if (isHidden && activeFocusTrap) {
            // Modal closed - release focus
            releaseFocusTrap();
          }
        }
      });
    });

    observer.observe(modalOverlay, {
      attributes: true,
      attributeFilter: ['class']
    });
  }

  // Handle Escape key to close modal
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && activeFocusTrap) {
      const closeBtn = document.getElementById('modal-close') || document.getElementById('close-btn');
      if (closeBtn) {
        closeBtn.click();
      }
    }
  });

  console.log('[FocusManagement] Focus management initialized');
}

// Expose functions to window
window.FocusManagement = {
  trapFocus,
  releaseFocusTrap,
  moveFocusTo,
  getFocusableElements,
  initialize: initializeFocusManagement
};

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeFocusManagement);
} else {
  initializeFocusManagement();
}
