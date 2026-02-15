/**
 * Keyboard Navigation Module - Handles keyboard accessibility
 * Implements keyboard event handlers, focus management, and focus trap for modals
 */

// Focus trap state
let focusTrapActive = false;
let focusableElements = [];
let firstFocusableElement = null;
let lastFocusableElement = null;
let previouslyFocusedElement = null;

/**
 * Get all focusable elements within a container
 * @param {HTMLElement} container - Container element
 * @returns {Array<HTMLElement>} Array of focusable elements
 */
function getFocusableElements(container) {
  const selector = [
    'a[href]',
    'button:not([disabled])',
    'input:not([disabled])',
    'textarea:not([disabled])',
    'select:not([disabled])',
    '[tabindex]:not([tabindex="-1"])',
    '[contenteditable="true"]'
  ].join(', ');

  return Array.from(container.querySelectorAll(selector))
    .filter(el => {
      // Filter out hidden elements
      return el.offsetParent !== null &&
             window.getComputedStyle(el).visibility !== 'hidden';
    });
}

/**
 * Activate focus trap in a container (typically a modal)
 * @param {HTMLElement} container - Container to trap focus within
 */
function activateFocusTrap(container) {
  if (!container) {
    console.warn('activateFocusTrap: Container not found');
    return;
  }

  // Store previously focused element to restore later
  previouslyFocusedElement = document.activeElement;

  // Get all focusable elements in container
  focusableElements = getFocusableElements(container);

  if (focusableElements.length === 0) {
    console.warn('activateFocusTrap: No focusable elements found');
    return;
  }

  firstFocusableElement = focusableElements[0];
  lastFocusableElement = focusableElements[focusableElements.length - 1];

  // Focus first element
  firstFocusableElement.focus();

  // Activate trap
  focusTrapActive = true;

  // Add event listener for Tab key
  document.addEventListener('keydown', handleFocusTrap);
}

/**
 * Deactivate focus trap and restore focus
 */
function deactivateFocusTrap() {
  focusTrapActive = false;

  // Remove event listener
  document.removeEventListener('keydown', handleFocusTrap);

  // Restore focus to previously focused element
  if (previouslyFocusedElement && previouslyFocusedElement.focus) {
    previouslyFocusedElement.focus();
  }

  // Clear state
  focusableElements = [];
  firstFocusableElement = null;
  lastFocusableElement = null;
  previouslyFocusedElement = null;
}

/**
 * Handle focus trap keyboard events
 * @param {KeyboardEvent} e - Keyboard event
 */
function handleFocusTrap(e) {
  if (!focusTrapActive) {
    return;
  }

  // Only trap Tab key
  if (e.key !== 'Tab') {
    return;
  }

  // Shift + Tab (backwards)
  if (e.shiftKey) {
    if (document.activeElement === firstFocusableElement) {
      e.preventDefault();
      lastFocusableElement.focus();
    }
  }
  // Tab (forwards)
  else {
    if (document.activeElement === lastFocusableElement) {
      e.preventDefault();
      firstFocusableElement.focus();
    }
  }
}

/**
 * Add keyboard event handlers to an element
 * @param {HTMLElement} element - Element to add handlers to
 * @param {Function} callback - Callback function to execute
 * @param {Object} options - Options for keyboard handling
 */
function addKeyboardHandler(element, callback, options = {}) {
  if (!element) {
    return;
  }

  const {
    keys = ['Enter', ' '], // Default: Enter and Space
    preventDefault = true
  } = options;

  element.addEventListener('keydown', (e) => {
    if (keys.includes(e.key)) {
      if (preventDefault) {
        e.preventDefault();
      }
      callback(e);
    }
  });
}

/**
 * Initialize keyboard navigation for navigation items
 */
function initializeNavKeyboard() {
  const navItems = document.querySelectorAll('.nav-item[data-tab]');

  navItems.forEach(item => {
    addKeyboardHandler(item, () => {
      const tabName = item.getAttribute('data-tab');
      if (window.showTab) {
        window.showTab(tabName);
      }
    });
  });
}

/**
 * Initialize keyboard navigation for FIR list items
 */
function initializeFIRListKeyboard() {
  const firItems = document.querySelectorAll('.fir-item');

  firItems.forEach(item => {
    addKeyboardHandler(item, () => {
      // Trigger click event for consistency
      item.click();
    });
  });
}

/**
 * Initialize keyboard navigation for file upload labels
 */
function initializeFileUploadKeyboard() {
  const letterLabel = document.querySelector('label[for="letter-upload"]');
  const audioLabel = document.querySelector('label[for="audio-upload"]');

  if (letterLabel) {
    addKeyboardHandler(letterLabel, () => {
      const input = document.getElementById('letter-upload');
      if (input) {
        input.click();
      }
    });
  }

  if (audioLabel) {
    addKeyboardHandler(audioLabel, () => {
      const input = document.getElementById('audio-upload');
      if (input) {
        input.click();
      }
    });
  }
}

/**
 * Initialize keyboard navigation for modal
 */
function initializeModalKeyboard() {
  const modalOverlay = document.getElementById('modal-overlay');
  const modalClose = document.getElementById('modal-close');
  const closeBtn = document.getElementById('close-btn');

  // Escape key to close modal
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      if (modalOverlay && !modalOverlay.classList.contains('hidden')) {
        if (window.closeModal) {
          window.closeModal();
        }
        deactivateFocusTrap();
      }
    }
  });

  // Add keyboard handlers to close buttons
  if (modalClose) {
    addKeyboardHandler(modalClose, () => {
      if (window.closeModal) {
        window.closeModal();
      }
      deactivateFocusTrap();
    });
  }

  if (closeBtn) {
    addKeyboardHandler(closeBtn, () => {
      if (window.closeModal) {
        window.closeModal();
      }
      deactivateFocusTrap();
    });
  }
}

/**
 * Initialize keyboard navigation for copy button
 */
function initializeCopyButtonKeyboard() {
  const copyBtn = document.getElementById('copy-btn');

  if (copyBtn) {
    addKeyboardHandler(copyBtn, () => {
      copyBtn.click();
    });
  }
}

/**
 * Initialize keyboard navigation for toast close buttons
 */
function initializeToastKeyboard() {
  // Use event delegation for dynamically created toasts
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      const target = e.target;
      if (target.classList.contains('toast-close')) {
        e.preventDefault();
        target.click();
      }
    }
  });
}

/**
 * Enhance modal to activate focus trap when shown
 */
function enhanceModalFocusTrap() {
  const modalOverlay = document.getElementById('modal-overlay');

  if (!modalOverlay) {
    return;
  }

  // Create a MutationObserver to watch for modal visibility changes
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
        const isHidden = modalOverlay.classList.contains('hidden');

        if (!isHidden && !focusTrapActive) {
          // Modal opened - activate focus trap
          const modalContent = modalOverlay.querySelector('.modal-content');
          if (modalContent) {
            activateFocusTrap(modalContent);
          }
        } else if (isHidden && focusTrapActive) {
          // Modal closed - deactivate focus trap
          deactivateFocusTrap();
        }
      }
    });
  });

  // Start observing
  observer.observe(modalOverlay, {
    attributes: true,
    attributeFilter: ['class']
  });
}

/**
 * Initialize all keyboard navigation features
 */
function initializeKeyboardNavigation() {
  // Initialize keyboard handlers for all interactive elements
  initializeNavKeyboard();
  initializeFIRListKeyboard();
  initializeFileUploadKeyboard();
  initializeModalKeyboard();
  initializeCopyButtonKeyboard();
  initializeToastKeyboard();

  // Enhance modal with focus trap
  enhanceModalFocusTrap();

  console.log('Keyboard navigation initialized');
}

// Export functions for use in other modules
window.KeyboardNav = {
  initialize: initializeKeyboardNavigation,
  activateFocusTrap,
  deactivateFocusTrap,
  addKeyboardHandler,
  getFocusableElements
};

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeKeyboardNavigation);
} else {
  initializeKeyboardNavigation();
}
