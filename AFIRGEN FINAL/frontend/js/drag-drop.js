/**
 * Drag and Drop Module
 * Handles drag-and-drop file upload functionality
 */

/**
 * Initialize drag-and-drop for a file input
 * @param {string} dropZoneId - ID of the drop zone element
 * @param {string} inputId - ID of the file input element
 * @param {Function} onFileDrop - Callback function when file is dropped
 */
function initDragDrop(dropZoneId, inputId, onFileDrop) {
    const dropZone = document.getElementById(dropZoneId);
    const fileInput = document.getElementById(inputId);
    
    if (!dropZone || !fileInput) {
        console.error(`Drop zone or input not found: ${dropZoneId}, ${inputId}`);
        return;
    }
    
    // Prevent default drag behaviors on the entire document
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });
    
    // Highlight drop zone when item is dragged over it
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => highlight(dropZone), false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => unhighlight(dropZone), false);
    });
    
    // Handle dropped files
    dropZone.addEventListener('drop', (e) => handleDrop(e, fileInput, onFileDrop), false);
}

/**
 * Prevent default drag behaviors
 */
function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

/**
 * Highlight drop zone
 */
function highlight(element) {
    element.classList.add('drag-over');
}

/**
 * Remove highlight from drop zone
 */
function unhighlight(element) {
    element.classList.remove('drag-over');
}

/**
 * Handle file drop
 */
function handleDrop(e, fileInput, onFileDrop) {
    const dt = e.dataTransfer;
    const files = dt.files;
    
    if (files.length > 0) {
        const file = files[0]; // Only take the first file
        
        // Create a new FileList-like object
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);
        
        // Set the files on the input
        fileInput.files = dataTransfer.files;
        
        // Trigger change event on the input
        const event = new Event('change', { bubbles: true });
        fileInput.dispatchEvent(event);
        
        // Call the callback if provided
        if (onFileDrop && typeof onFileDrop === 'function') {
            onFileDrop(file);
        }
    }
}

/**
 * Validate dropped file
 * @param {File} file - The dropped file
 * @param {Object} options - Validation options
 * @returns {Object} Validation result
 */
async function validateDroppedFile(file, options = {}) {
    // Use the existing validation module if available
    if (window.Validation && window.Validation.validateFile) {
        return await window.Validation.validateFile(file, options);
    }
    
    // Basic validation fallback
    const {
        maxSize = 10 * 1024 * 1024, // 10MB default
        allowedTypes = []
    } = options;
    
    // Check file size
    if (file.size > maxSize) {
        return {
            success: false,
            error: `File size exceeds ${Math.round(maxSize / 1024 / 1024)}MB limit`
        };
    }
    
    // Check file type
    if (allowedTypes.length > 0) {
        const fileExt = '.' + file.name.split('.').pop().toLowerCase();
        if (!allowedTypes.includes(fileExt)) {
            return {
                success: false,
                error: `File type not allowed. Allowed types: ${allowedTypes.join(', ')}`
            };
        }
    }
    
    return { success: true };
}

/**
 * Show visual feedback for file drop
 * @param {HTMLElement} element - The element to show feedback on
 * @param {string} message - The message to display
 * @param {string} type - The type of feedback (success, error)
 */
function showDropFeedback(element, message, type = 'success') {
    // Create feedback element
    const feedback = document.createElement('div');
    feedback.className = `drop-feedback drop-feedback-${type}`;
    feedback.textContent = message;
    feedback.setAttribute('role', 'status');
    feedback.setAttribute('aria-live', 'polite');
    
    // Position it over the drop zone
    element.style.position = 'relative';
    feedback.style.position = 'absolute';
    feedback.style.top = '50%';
    feedback.style.left = '50%';
    feedback.style.transform = 'translate(-50%, -50%)';
    feedback.style.padding = '0.5rem 1rem';
    feedback.style.borderRadius = '0.375rem';
    feedback.style.fontSize = '0.875rem';
    feedback.style.fontWeight = '500';
    feedback.style.zIndex = '10';
    feedback.style.pointerEvents = 'none';
    
    if (type === 'success') {
        feedback.style.background = 'rgba(16, 185, 129, 0.9)';
        feedback.style.color = '#fff';
    } else {
        feedback.style.background = 'rgba(239, 68, 68, 0.9)';
        feedback.style.color = '#fff';
    }
    
    element.appendChild(feedback);
    
    // Animate in
    feedback.style.opacity = '0';
    feedback.style.transition = 'opacity 0.3s ease';
    setTimeout(() => {
        feedback.style.opacity = '1';
    }, 10);
    
    // Remove after 2 seconds
    setTimeout(() => {
        feedback.style.opacity = '0';
        setTimeout(() => {
            feedback.remove();
        }, 300);
    }, 2000);
}

// Export functions
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        initDragDrop,
        validateDroppedFile,
        showDropFeedback
    };
}

// Make functions available globally
if (typeof window !== 'undefined') {
    window.DragDrop = {
        init: initDragDrop,
        validate: validateDroppedFile,
        showFeedback: showDropFeedback
    };
}
