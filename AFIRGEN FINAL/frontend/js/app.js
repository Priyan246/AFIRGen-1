/**
 * Main Application Module - Coordinates all modules and handles main application logic
 */

// State management
let letterFile = null;
let audioFile = null;
let hasFiles = false;
let isProcessing = false;
let sessionId = null;
let currentStep = null;
let isProcessingValidation = false;
let deferredPrompt = null;

/**
 * Update files state and UI
 */
function updateFilesState() {
  hasFiles = !!(letterFile || audioFile);
  const generateBtn = document.getElementById('generate-btn');
  const statusReady = document.getElementById('status-ready');
  const statusProcessing = document.getElementById('status-processing');

  if (generateBtn) {
    generateBtn.disabled = !hasFiles;
    generateBtn.setAttribute('aria-disabled', !hasFiles ? 'true' : 'false');
  }

  if (hasFiles && !isProcessing) {
    statusReady?.classList.remove('hidden');
    statusProcessing?.classList.add('hidden');
  } else {
    statusReady?.classList.add('hidden');
  }
}

/**
 * Generate mock FIR for fallback/testing
 * @param {string} content - Content to include in FIR
 * @param {string} filename - Source filename
 * @returns {string} Generated FIR content
 */
function generateMockFIR(content, filename) {
  const now = new Date();
  const firNumber = `FIR/${now.getFullYear()}/${String(Math.floor(Math.random() * 10000)).padStart(4, '0')}`;

  return `FIRST INFORMATION REPORT
${firNumber}

Date: ${now.toLocaleDateString('en-IN', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  })}
Time: ${now.toLocaleTimeString('en-IN', {
    hour: '2-digit',
    minute: '2-digit'
  })}

Police Station: Moongapair West (V7)

COMPLAINT DETAILS:
${filename ? `Source Document: ${filename}` : 'Source: Text Input'}

Based on the provided information:
${content.slice(0, 500)}${content.length > 500 ? '...' : ''}

PRELIMINARY ANALYSIS:
- Nature of Complaint: [To be determined by investigating officer]
- Priority Level: Medium
- Assigned Officer: [To be assigned]
- Status: Pending Investigation

This FIR has been automatically generated using AI assistance.
Further investigation and verification required by authorized personnel.

Generated on: ${now.toISOString()}`;
}

/**
 * Handle FIR generation
 */
async function handleGenerate() {
  if (!hasFiles || isProcessing) {
    return;
  }

  isProcessing = true;
  const generateBtn = document.getElementById('generate-btn');
  const statusReady = document.getElementById('status-ready');
  const statusProcessing = document.getElementById('status-processing');

  // Show loading spinner on button
  generateBtn.innerHTML = '<div class="spinner"></div>';
  statusReady?.classList.add('hidden');
  statusProcessing?.classList.remove('hidden');

  // Show loading overlay on main content
  const mainContent = document.querySelector('.main-content');
  const loadingId = window.showLoading(mainContent, 'Uploading files...');

  try {
    // Process files with progress tracking
    const data = await window.API.processFiles(letterFile, audioFile, (progress) => {
      // Update progress bar during upload
      window.showProgress(mainContent, progress, `Uploading files... ${Math.round(progress)}%`);
    });

    // Hide upload progress, show processing message
    window.hideLoading(loadingId);
    const processingId = window.showLoading(mainContent, 'Processing FIR generation...');

    sessionId = data.session_id;
    currentStep = data.current_step;

    // Hide processing loader before showing validation modal
    window.hideLoading(processingId);

    // Show validation modal with content
    window.showValidationModal(currentStep, data.content_for_validation);

    // Start polling status with loading indicator
    const pollingId = window.showLoading(mainContent, 'Waiting for validation...');

    window.API.pollSessionStatus(
      sessionId,
      (firData) => {
        window.hideLoading(pollingId);
        window.showToast('FIR generated successfully!', 'success');
        window.showResult({
          success: true,
          fir_content: firData.content,
          source_filename: `FIR #${firData.fir_number || 'Unknown'}`
        });
        updateFIRList();
      },
      (error) => {
        window.hideLoading(pollingId);
        // Use new error handling system with context
        window.API.handleNetworkError(error, 'session status polling');
      }
    );

  } catch (error) {
    window.hideLoading(loadingId);
    // Use new error handling system with specific context
    if (error.status && error.status >= 400) {
      // API error with status code - create mock response for handleAPIError
      const mockResponse = {
        status: error.status,
        statusText: error.message || 'Request failed',
        headers: { get: () => 'application/json' },
        json: async () => ({ error: error.message }),
        url: `${window.ENV?.API_BASE_URL || 'http://localhost:8000'}/process`
      };
      await window.API.handleAPIError(mockResponse, 'file upload and processing');
    } else {
      // Network or other error
      window.API.handleNetworkError(error, 'file upload and processing');
    }
  } finally {
    isProcessing = false;
    generateBtn.innerHTML = '<svg class="generate-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9,18 15,12 9,6"></polyline></svg>';
    statusProcessing?.classList.add('hidden');
    updateFilesState();
  }
}

/**
 * Handle validation approval/rejection
 * @param {boolean} approved - Whether content is approved
 * @param {string} userInput - User corrections or input
 */
async function handleValidation(approved, userInput) {
  if (isProcessingValidation) {
    return;
  }
  isProcessingValidation = true;

  // Show loading spinner on modal
  const modalBody = document.querySelector('.modal-body');
  const validationLoadingId = window.showLoading(modalBody, 'Processing validation...');

  try {
    const data = await window.API.validateStep(sessionId, approved, userInput);

    currentStep = data.current_step;

    window.hideLoading(validationLoadingId);

    if (data.completed) {
      window.showToast('Validation approved! FIR completed.', 'success');
      window.showResult({
        success: true,
        fir_content: data.content.fir_content,
        source_filename: `FIR #${data.content.fir_number}`
      });
      updateFIRList();
      window.closeModal();
    } else {
      window.showToast('Moving to next validation step', 'info');
      window.showValidationModal(currentStep, data.content);
    }
  } catch (error) {
    window.hideLoading(validationLoadingId);
    // Use new error handling system with specific operation context
    if (error.status && error.status >= 400) {
      // API error with status code
      const mockResponse = {
        status: error.status,
        statusText: error.message || 'Validation failed',
        headers: { get: () => 'application/json' },
        json: async () => ({ error: error.message }),
        url: `${window.ENV?.API_BASE_URL || 'http://localhost:8000'}/validate`
      };
      await window.API.handleAPIError(mockResponse, 'step validation');
    } else {
      // Network or other error
      window.API.handleNetworkError(error, 'step validation');
    }
  } finally {
    isProcessingValidation = false;
  }
}

/**
 * Handle content regeneration
 * @param {string} userInput - User corrections or input
 */
async function handleRegenerate(userInput) {
  if (isProcessingValidation) {
    return;
  }
  isProcessingValidation = true;

  // Show loading spinner on modal
  const modalBody = document.querySelector('.modal-body');
  const regenerateLoadingId = window.showLoading(modalBody, 'Regenerating content...');

  try {
    const data = await window.API.regenerateStep(sessionId, currentStep, userInput);

    window.hideLoading(regenerateLoadingId);

    if (data.success) {
      window.showToast('Content regenerated successfully', 'success');
      window.showValidationModal(currentStep, data.content);
    }
  } catch (error) {
    window.hideLoading(regenerateLoadingId);
    // Use new error handling system with specific operation context
    if (error.status && error.status >= 400) {
      // API error with status code
      const mockResponse = {
        status: error.status,
        statusText: error.message || 'Regeneration failed',
        headers: { get: () => 'application/json' },
        json: async () => ({ error: error.message }),
        url: `${window.ENV?.API_BASE_URL || 'http://localhost:8000'}/regenerate`
      };
      await window.API.handleAPIError(mockResponse, 'content regeneration');
    } else {
      // Network or other error
      window.API.handleNetworkError(error, 'content regeneration');
    }
  } finally {
    isProcessingValidation = false;
  }
}

/**
 * Update FIR list in sidebar (placeholder for future implementation)
 */
async function updateFIRList() {
  // Placeholder: Implement when backend provides list endpoint
  console.log('FIR list update requested');
}

/**
 * Initialize PWA install prompt
 */
function initializePWAInstall() {
  // Listen for beforeinstallprompt event
  window.addEventListener('beforeinstallprompt', (e) => {
    // Prevent the mini-infobar from appearing on mobile
    e.preventDefault();
    
    // Store the event for later use
    deferredPrompt = e;
    
    console.log('[App] PWA install prompt available');
    
    // Show install button/toast to user
    window.showToast(
      'Install AFIRGen for offline access and better experience!',
      'info',
      10000
    );
  });

  // Listen for app installed event
  window.addEventListener('appinstalled', () => {
    console.log('[App] PWA installed successfully');
    deferredPrompt = null;
    
    window.showToast(
      'AFIRGen installed successfully!',
      'success',
      5000
    );
  });
}

/**
 * Trigger PWA install prompt
 */
async function promptPWAInstall() {
  if (!deferredPrompt) {
    console.log('[App] No install prompt available');
    window.showToast(
      'App is already installed or not installable',
      'info',
      3000
    );
    return;
  }

  // Show the install prompt
  deferredPrompt.prompt();

  // Wait for the user's response
  const { outcome } = await deferredPrompt.userChoice;
  
  console.log(`[App] User response to install prompt: ${outcome}`);
  
  if (outcome === 'accepted') {
    window.showToast('Installing AFIRGen...', 'success', 3000);
  } else {
    window.showToast('Installation cancelled', 'info', 3000);
  }

  // Clear the deferred prompt
  deferredPrompt = null;
}

/**
 * Initialize application
 */
function initializeApp() {
  // Initialize theme (must be first to avoid flash)
  if (window.Theme) {
    window.Theme.init();
  }

  // Initialize UI module
  window.initializeUI();

  // Initialize FIR history
  if (window.initFIRHistory) {
    window.initFIRHistory().catch(error => {
      console.error('Failed to initialize FIR history:', error);
    });
  }

  // Initialize drag-and-drop
  if (window.DragDrop) {
    window.DragDrop.init('letter-drop-zone', 'letter-upload');
    window.DragDrop.init('audio-drop-zone', 'audio-upload');
  }

  // Initialize PWA install prompt
  initializePWAInstall();

  // File upload handlers
  const letterUpload = document.getElementById('letter-upload');
  const audioUpload = document.getElementById('audio-upload');
  const letterText = document.getElementById('letter-text');
  const audioText = document.getElementById('audio-text');
  const generateBtn = document.getElementById('generate-btn');

  if (letterUpload) {
    letterUpload.addEventListener('change', async (e) => {
      const file = e.target.files[0] || null;

      if (file) {
        // Validate file
        const validationResult = await window.Validation.validateFile(file, {
          maxSize: 10 * 1024 * 1024, // 10MB
          allowedTypes: ['.jpg', '.jpeg', '.png', '.pdf', '.txt', '.doc', '.docx'],
          checkMimeType: true
        });

        if (!validationResult.success) {
          // Use new validation error handling system
          window.Validation.handleValidationError(
            { error: validationResult.error },
            'letter file upload'
          );
          e.target.value = ''; // Clear the input
          letterFile = null;
          if (letterText) {
            letterText.textContent = 'Upload Letter';
          }
        } else {
          letterFile = file;
          if (letterText) {
            letterText.textContent = file.name;
          }
          window.showToast(`Letter file uploaded: ${file.name}`, 'success', 3000);
        }
      } else {
        letterFile = null;
        if (letterText) {
          letterText.textContent = 'Upload Letter';
        }
      }

      updateFilesState();
    });
  }

  if (audioUpload) {
    audioUpload.addEventListener('change', async (e) => {
      const file = e.target.files[0] || null;

      if (file) {
        // Validate file
        const validationResult = await window.Validation.validateFile(file, {
          maxSize: 10 * 1024 * 1024, // 10MB
          allowedTypes: ['.mp3', '.wav', '.m4a', '.ogg'],
          checkMimeType: true
        });

        if (!validationResult.success) {
          // Use new validation error handling system
          window.Validation.handleValidationError(
            { error: validationResult.error },
            'audio file upload'
          );
          e.target.value = ''; // Clear the input
          audioFile = null;
          if (audioText) {
            audioText.textContent = 'Upload Audio';
          }
        } else {
          audioFile = file;
          if (audioText) {
            audioText.textContent = file.name;
          }
          window.showToast(`Audio file uploaded: ${file.name}`, 'success', 3000);
        }
      } else {
        audioFile = null;
        if (audioText) {
          audioText.textContent = 'Upload Audio';
        }
      }

      updateFilesState();
    });
  }

  if (generateBtn) {
    generateBtn.addEventListener('click', handleGenerate);
  }

  // Load initial FIR list
  updateFIRList();

  // Register service worker for offline capability
  registerServiceWorker();
}

/**
 * Register service worker for offline capability
 */
async function registerServiceWorker() {
  // Check if service workers are supported
  if (!('serviceWorker' in navigator)) {
    console.log('[App] Service workers are not supported in this browser');
    return;
  }

  try {
    // Register the service worker
    const registration = await navigator.serviceWorker.register('/sw.js', {
      scope: '/'
    });

    console.log('[App] Service worker registered successfully:', registration.scope);

    // Handle updates
    registration.addEventListener('updatefound', () => {
      const newWorker = registration.installing;
      console.log('[App] Service worker update found');

      newWorker.addEventListener('statechange', () => {
        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
          // New service worker available
          console.log('[App] New service worker available');
          
          // Show toast notification about update
          window.showToast(
            'A new version is available. Refresh to update.',
            'info',
            10000
          );
        }
      });
    });

    // Check for updates periodically (every hour)
    setInterval(() => {
      registration.update();
    }, 60 * 60 * 1000);

  } catch (error) {
    console.error('[App] Service worker registration failed:', error);
    // Don't show error to user - offline capability is optional
  }

  // Listen for service worker messages
  navigator.serviceWorker.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'CACHE_UPDATED') {
      console.log('[App] Cache updated:', event.data.url);
    }
  });

  // Handle online/offline events
  window.addEventListener('online', () => {
    console.log('[App] Back online');
    window.showToast('Connection restored', 'success', 3000);
  });

  window.addEventListener('offline', () => {
    console.log('[App] Gone offline');
    window.showToast('You are offline. Some features may be limited.', 'warning', 5000);
  });
}

// Expose functions to window for use in other modules
window.handleValidation = handleValidation;
window.handleRegenerate = handleRegenerate;
window.updateFIRList = updateFIRList;
window.promptPWAInstall = promptPWAInstall;

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeApp);
} else {
  initializeApp();
}
