/**
 * UI Module - Handles UI interactions, tab management, time updates, and loading states
 */

// Tab management
let currentTab = 'home';

// Loading state tracking
const loadingStates = new Map();

// Toast tracking
let toastIdCounter = 0;
const activeToasts = new Map();

/**
 * Show a toast notification
 * @param {string} message - Message to display
 * @param {string} type - Toast type: 'success', 'error', 'warning', 'info'
 * @param {number} duration - Duration in milliseconds (0 = no auto-hide)
 * @returns {string} Toast ID for tracking
 */
function showToast(message, type = 'info', duration = 5000) {
  // Generate unique toast ID
  const toastId = `toast-${++toastIdCounter}`;

  // Get or create toast container
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    container.setAttribute('aria-live', 'polite');
    container.setAttribute('aria-atomic', 'true');
    document.body.appendChild(container);
  }

  // Create toast element
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.setAttribute('role', 'alert');
  toast.setAttribute('data-toast-id', toastId);

  // Create icon based on type
  const icon = document.createElement('div');
  icon.className = 'toast-icon';

  switch (type) {
  case 'success':
    icon.innerHTML = `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
          <polyline points="22,4 12,14.01 9,11.01"></polyline>
        </svg>
      `;
    break;
  case 'error':
    icon.innerHTML = `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="15" y1="9" x2="9" y2="15"></line>
          <line x1="9" y1="9" x2="15" y2="15"></line>
        </svg>
      `;
    break;
  case 'warning':
    icon.innerHTML = `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
          <line x1="12" y1="9" x2="12" y2="13"></line>
          <line x1="12" y1="17" x2="12.01" y2="17"></line>
        </svg>
      `;
    break;
  case 'info':
  default:
    icon.innerHTML = `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="12" y1="16" x2="12" y2="12"></line>
          <line x1="12" y1="8" x2="12.01" y2="8"></line>
        </svg>
      `;
    break;
  }

  // Create content
  const content = document.createElement('div');
  content.className = 'toast-content';

  const messageElement = document.createElement('div');
  messageElement.className = 'toast-message';
  messageElement.textContent = message;

  content.appendChild(messageElement);

  // Create close button
  const closeButton = document.createElement('div');
  closeButton.className = 'toast-close';
  closeButton.innerHTML = `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <line x1="18" y1="6" x2="6" y2="18"></line>
      <line x1="6" y1="6" x2="18" y2="18"></line>
    </svg>
  `;
  closeButton.setAttribute('aria-label', 'Close notification');
  closeButton.addEventListener('click', () => hideToast(toastId));

  // Assemble toast
  toast.appendChild(icon);
  toast.appendChild(content);
  toast.appendChild(closeButton);

  // Add to container
  container.appendChild(toast);

  // Trigger slide-in animation
  requestAnimationFrame(() => {
    toast.classList.add('toast-show');
  });

  // Track toast
  const toastData = {
    element: toast,
    type,
    message,
    createdAt: Date.now()
  };

  activeToasts.set(toastId, toastData);

  // Auto-hide after duration
  if (duration > 0) {
    toastData.timeout = setTimeout(() => {
      hideToast(toastId);
    }, duration);
  }

  return toastId;
}

/**
 * Hide a toast notification
 * @param {string} toastId - Toast ID to hide
 */
function hideToast(toastId) {
  const toastData = activeToasts.get(toastId);

  if (!toastData) {
    return;
  }

  const { element, timeout } = toastData;

  // Clear auto-hide timeout if exists
  if (timeout) {
    clearTimeout(timeout);
  }

  // Trigger slide-out animation
  element.classList.remove('toast-show');
  element.classList.add('toast-hide');

  // Remove from DOM after animation
  setTimeout(() => {
    if (element.parentNode) {
      element.parentNode.removeChild(element);
    }
    activeToasts.delete(toastId);
  }, 300);
}

/**
 * Show a specific tab and hide others
 * @param {string} tabName - Name of the tab to show
 */
function showTab(tabName) {
  // First, remove active class from all tabs (triggers fade out)
  document.querySelectorAll('.main-container, .tab-content').forEach(tab => {
    tab.classList.remove('active');
  });

  // Wait for fade out transition, then hide and show
  setTimeout(() => {
    document.querySelectorAll('.main-container, .tab-content').forEach(tab => {
      tab.style.display = 'none';
    });

    // Show selected tab
    const targetTab = document.getElementById(`${tabName}-tab`);
    if (targetTab) {
      if (tabName === 'home') {
        targetTab.style.display = 'flex';
      } else {
        targetTab.style.display = 'block';
      }
      
      // Trigger reflow to ensure transition works
      targetTab.offsetHeight;
      
      // Add active class to trigger fade in
      targetTab.classList.add('active');
    }
  }, 300); // Match the CSS transition duration

  // Update nav items
  document.querySelectorAll('.nav-item').forEach(item => {
    item.classList.remove('active');
  });

  const activeNavItem = document.querySelector(`[data-tab="${tabName}"]`);
  if (activeNavItem) {
    activeNavItem.classList.add('active');
  }

  currentTab = tabName;
}

/**
 * Show loading indicator on an element
 * @param {HTMLElement|string} element - Element or selector to show loading on
 * @param {string} message - Optional loading message
 * @returns {string} Loading ID for tracking
 */
function showLoading(element, message = 'Loading...') {
  const targetElement = typeof element === 'string' ? document.querySelector(element) : element;

  if (!targetElement) {
    console.warn('showLoading: Element not found');
    return null;
  }

  // Generate unique loading ID
  const loadingId = `loading-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

  // Create loading overlay
  const loadingOverlay = document.createElement('div');
  loadingOverlay.className = 'loading-overlay';
  loadingOverlay.setAttribute('data-loading-id', loadingId);

  // Create spinner
  const spinner = document.createElement('div');
  spinner.className = 'loading-spinner';

  // Create message
  const messageElement = document.createElement('div');
  messageElement.className = 'loading-message';
  messageElement.textContent = message;

  // Assemble loading UI
  loadingOverlay.appendChild(spinner);
  loadingOverlay.appendChild(messageElement);

  // Store original position style
  const originalPosition = window.getComputedStyle(targetElement).position;
  if (originalPosition === 'static') {
    targetElement.style.position = 'relative';
  }

  // Add loading overlay to element
  targetElement.appendChild(loadingOverlay);

  // Track loading state
  loadingStates.set(loadingId, {
    element: targetElement,
    overlay: loadingOverlay,
    originalPosition,
    startTime: Date.now()
  });

  // Set aria-busy for accessibility
  targetElement.setAttribute('aria-busy', 'true');

  return loadingId;
}

/**
 * Hide loading indicator from an element
 * @param {HTMLElement|string} element - Element, selector, or loading ID
 */
function hideLoading(element) {
  let targetElement;
  let loadingId;

  // Handle different input types
  if (typeof element === 'string') {
    // Check if it's a loading ID
    if (loadingStates.has(element)) {
      loadingId = element;
      const state = loadingStates.get(loadingId);
      targetElement = state.element;
    } else {
      // It's a selector
      targetElement = document.querySelector(element);
    }
  } else {
    targetElement = element;
  }

  if (!targetElement) {
    console.warn('hideLoading: Element not found');
    return;
  }

  // Find and remove loading overlay
  const overlays = targetElement.querySelectorAll('.loading-overlay');
  overlays.forEach(overlay => {
    const overlayId = overlay.getAttribute('data-loading-id');

    // If we have a specific loading ID, only remove that one
    if (loadingId && overlayId !== loadingId) {
      return;
    }

    // Remove overlay with fade out
    overlay.style.opacity = '0';
    setTimeout(() => {
      if (overlay.parentNode) {
        overlay.parentNode.removeChild(overlay);
      }
    }, 200);

    // Clean up loading state
    if (overlayId && loadingStates.has(overlayId)) {
      const state = loadingStates.get(overlayId);

      // Restore original position if needed
      if (state.originalPosition === 'static') {
        targetElement.style.position = '';
      }

      loadingStates.delete(overlayId);
    }
  });

  // Remove aria-busy if no more loading overlays
  if (targetElement.querySelectorAll('.loading-overlay').length === 0) {
    targetElement.removeAttribute('aria-busy');
  }
}

/**
 * Show progress indicator on an element
 * @param {HTMLElement|string} element - Element or selector to show progress on
 * @param {number} percentage - Progress percentage (0-100)
 * @param {string} message - Optional progress message
 * @returns {string} Progress ID for tracking
 */
function showProgress(element, percentage, message = '') {
  const targetElement = typeof element === 'string' ? document.querySelector(element) : element;

  if (!targetElement) {
    console.warn('showProgress: Element not found');
    return null;
  }

  // Clamp percentage between 0 and 100
  const clampedPercentage = Math.max(0, Math.min(100, percentage));

  // Check if progress bar already exists
  let progressOverlay = targetElement.querySelector('.progress-overlay');
  let progressId;

  if (!progressOverlay) {
    // Generate unique progress ID
    progressId = `progress-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

    // Create progress overlay
    progressOverlay = document.createElement('div');
    progressOverlay.className = 'progress-overlay';
    progressOverlay.setAttribute('data-progress-id', progressId);

    // Create progress bar container
    const progressContainer = document.createElement('div');
    progressContainer.className = 'progress-container';

    // Create progress bar
    const progressBar = document.createElement('div');
    progressBar.className = 'progress-bar';

    // Create progress fill
    const progressFill = document.createElement('div');
    progressFill.className = 'progress-fill';

    // Create progress text
    const progressText = document.createElement('div');
    progressText.className = 'progress-text';

    // Create progress message
    const progressMessage = document.createElement('div');
    progressMessage.className = 'progress-message';

    // Assemble progress UI
    progressBar.appendChild(progressFill);
    progressContainer.appendChild(progressBar);
    progressContainer.appendChild(progressText);
    progressOverlay.appendChild(progressContainer);
    progressOverlay.appendChild(progressMessage);

    // Store original position style
    const originalPosition = window.getComputedStyle(targetElement).position;
    if (originalPosition === 'static') {
      targetElement.style.position = 'relative';
    }

    // Add progress overlay to element
    targetElement.appendChild(progressOverlay);

    // Track progress state
    loadingStates.set(progressId, {
      element: targetElement,
      overlay: progressOverlay,
      originalPosition,
      startTime: Date.now()
    });

    // Set aria-busy for accessibility
    targetElement.setAttribute('aria-busy', 'true');
  } else {
    progressId = progressOverlay.getAttribute('data-progress-id');
  }

  // Update progress
  const progressFill = progressOverlay.querySelector('.progress-fill');
  const progressText = progressOverlay.querySelector('.progress-text');
  const progressMessage = progressOverlay.querySelector('.progress-message');

  if (progressFill) {
    progressFill.style.width = `${clampedPercentage}%`;
  }

  if (progressText) {
    progressText.textContent = `${Math.round(clampedPercentage)}%`;
  }

  if (progressMessage && message) {
    progressMessage.textContent = message;
  }

  // Update aria-valuenow for accessibility
  progressOverlay.setAttribute('role', 'progressbar');
  progressOverlay.setAttribute('aria-valuenow', clampedPercentage);
  progressOverlay.setAttribute('aria-valuemin', '0');
  progressOverlay.setAttribute('aria-valuemax', '100');

  // Auto-hide when complete
  if (clampedPercentage >= 100) {
    setTimeout(() => {
      hideLoading(progressId);
    }, 500);
  }

  return progressId;
}

/**
 * Update the current time display
 */
function updateTime() {
  const now = new Date();
  const timeString = now.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: true
  });
  const timeElement = document.getElementById('current-time');
  if (timeElement) {
    timeElement.textContent = timeString;
  }
}

/**
 * Close the modal overlay
 */
function closeModal() {
  const modalOverlay = document.getElementById('modal-overlay');
  if (modalOverlay) {
    modalOverlay.classList.add('hidden');
  }
}

/**
 * Show result modal with success or error content
 * @param {Object} result - Result object with success flag and content
 */
function showResult(result) {
  const modalIcon = document.getElementById('modal-icon');
  const modalTitleText = document.getElementById('modal-title-text');
  const successContent = document.getElementById('success-content');
  const errorContent = document.getElementById('error-content');
  const sourceFilename = document.getElementById('source-filename');
  const firContent = document.getElementById('fir-content');
  const errorText = document.getElementById('error-text');
  const modalTimestamp = document.getElementById('modal-timestamp');
  const saveBtn = document.getElementById('save-btn');
  const modalOverlay = document.getElementById('modal-overlay');

  if (result.success) {
    modalIcon.innerHTML = '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22,4 12,14.01 9,11.01"></polyline>';
    modalIcon.style.color = '#34d399';
    modalTitleText.textContent = 'FIR Generated Successfully';
    successContent.classList.remove('hidden');
    errorContent.classList.add('hidden');
    saveBtn.classList.remove('hidden');

    sourceFilename.textContent = `Source: ${result.source_filename || 'Text Input'}`;
    firContent.textContent = result.fir_content;

    if (result.processed_at) {
      modalTimestamp.textContent = `Processed at: ${new Date(result.processed_at).toLocaleString()}`;
    }
  } else {
    modalIcon.innerHTML = '<line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line>';
    modalIcon.style.color = '#f87171';
    modalTitleText.textContent = 'Generation Failed';
    successContent.classList.add('hidden');
    errorContent.classList.remove('hidden');
    saveBtn.classList.add('hidden');

    errorText.textContent = result.error || 'An unknown error occurred during FIR generation.';
    modalTimestamp.textContent = '';
  }

  modalOverlay.classList.remove('hidden');
}

/**
 * Show validation modal for user approval/regeneration
 * @param {string} step - Current validation step
 * @param {*} content - Content to display for validation
 */
function showValidationModal(step, content) {
  const modalTitleText = document.getElementById('modal-title-text');
  const firContent = document.getElementById('fir-content');
  const modalOverlay = document.getElementById('modal-overlay');

  modalTitleText.textContent = `Validate ${step.replace('_', ' ').toUpperCase()}`;
  firContent.innerHTML = formatContentForDisplay(content);

  // Clear previous buttons
  const actions = document.querySelector('.modal-actions');
  actions.innerHTML = '';

  // Add input field for corrections
  const inputField = document.createElement('input');
  inputField.id = 'validation-input';
  inputField.placeholder = 'Optional corrections or additional input';
  inputField.style.width = '100%';
  inputField.style.marginBottom = '10px';

  // Add buttons
  const approveBtn = document.createElement('button');
  approveBtn.className = 'btn-primary';
  approveBtn.textContent = 'Approve';
  approveBtn.onclick = () => window.handleValidation(true, inputField.value);

  const regenerateBtn = document.createElement('button');
  regenerateBtn.className = 'btn-secondary';
  regenerateBtn.textContent = 'Regenerate';
  regenerateBtn.onclick = () => window.handleRegenerate(inputField.value);

  actions.append(inputField, approveBtn, regenerateBtn);
  modalOverlay.classList.remove('hidden');
}

/**
 * Format content for display in modal
 * @param {*} content - Content to format
 * @returns {string} Formatted HTML string
 */
function formatContentForDisplay(content) {
  if (typeof content === 'object') {
    if (content.violations) {
      return `<strong>Violations:</strong><ul>${content.violations.map(v => `<li>${v.section}: ${v.text}</li>`).join('')}</ul><strong>Summary:</strong> ${content.summary || ''}`;
    }
    return `<pre>${JSON.stringify(content, null, 2)}</pre>`;
  }
  return content;
}

/**
 * Initialize UI event handlers
 */
function initializeUI() {
  // Add click handlers to nav items
  document.querySelectorAll('.nav-item[data-tab]').forEach(item => {
    item.addEventListener('click', () => {
      const tabName = item.getAttribute('data-tab');
      showTab(tabName);
    });
  });

  // Show home tab by default
  showTab('home');

  // Initialize time and update every minute
  updateTime();
  setInterval(updateTime, 60000);

  // Modal close handlers
  const modalClose = document.getElementById('modal-close');
  const closeBtnModal = document.getElementById('close-btn');
  const modalOverlay = document.getElementById('modal-overlay');

  if (modalClose) {
    modalClose.addEventListener('click', closeModal);
  }
  if (closeBtnModal) {
    closeBtnModal.addEventListener('click', closeModal);
  }
  if (modalOverlay) {
    modalOverlay.addEventListener('click', (e) => {
      if (e.target === modalOverlay) {
        closeModal();
      }
    });
  }

  // Copy to clipboard handler
  const copyBtn = document.getElementById('copy-btn');
  if (copyBtn) {
    copyBtn.addEventListener('click', async () => {
      const content = document.getElementById('fir-content').textContent;
      if (content) {
        try {
          await navigator.clipboard.writeText(content);
          window.showToast('FIR content copied to clipboard', 'success', 3000);
          const copyText = document.getElementById('copy-text');
          copyText.textContent = 'Copied!';
          setTimeout(() => {
            copyText.textContent = 'Copy';
          }, 2000);
        } catch (err) {
          console.error('Failed to copy:', err);
          // Use new error handling system with specific context
          const error = new Error('Clipboard access failed');
          window.API.handleNetworkError(error, 'clipboard copy');
        }
      }
    });
  }

  // PDF Export handler
  const exportPdfBtn = document.getElementById('export-pdf-btn');
  if (exportPdfBtn) {
    exportPdfBtn.addEventListener('click', () => {
      // Check if PDF export is available
      if (!window.PDFExport || !window.PDFExport.isAvailable()) {
        window.showToast('PDF export library not loaded. Please refresh the page.', 'error', 5000);
        return;
      }

      // Get FIR data from modal
      const firContent = document.getElementById('fir-content').textContent;
      const sourceFilename = document.getElementById('source-filename').textContent;
      const timestamp = document.getElementById('modal-timestamp').textContent;

      if (!firContent) {
        window.showToast('No FIR content to export', 'warning');
        return;
      }

      // Extract FIR number from source filename
      const firNumberMatch = sourceFilename.match(/FIR #([^\s]+)/);
      const firNumber = firNumberMatch ? firNumberMatch[1] : null;

      // Create FIR data object
      const firData = {
        number: firNumber,
        content: firContent,
        fir_content: firContent,
        date: new Date().toISOString(),
        policeStation: 'Moggapair West (V7)',
        status: 'generated'
      };

      // Export as PDF
      try {
        window.PDFExport.export(firData, {
          download: true,
          print: false
        });
      } catch (error) {
        console.error('PDF export failed:', error);
        window.showToast('Failed to export PDF', 'error');
      }
    });
  }

  // Search functionality
  const searchInput = document.getElementById('search-input');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      const searchTerm = e.target.value.toLowerCase();
      const firItems = document.querySelectorAll('.fir-item');

      firItems.forEach(item => {
        const firNumber = item.querySelector('.fir-number').textContent.toLowerCase();
        const complainant = item.querySelector('.fir-complainant').textContent.toLowerCase();

        if (firNumber.includes(searchTerm) || complainant.includes(searchTerm)) {
          item.style.display = 'block';
        } else {
          item.style.display = searchTerm ? 'none' : 'block';
        }
      });
    });
  }

  // FIR item click handlers
  document.querySelectorAll('.fir-item').forEach(item => {
    item.addEventListener('click', () => {
      console.log('Selected FIR:', item.querySelector('.fir-number').textContent);
    });
  });
}

// Export functions for use in other modules
window.showTab = showTab;
window.updateTime = updateTime;
window.closeModal = closeModal;
window.showResult = showResult;
window.showValidationModal = showValidationModal;
window.formatContentForDisplay = formatContentForDisplay;
window.initializeUI = initializeUI;
window.showLoading = showLoading;
window.hideLoading = hideLoading;
window.showProgress = showProgress;
window.showToast = showToast;
window.hideToast = hideToast;
