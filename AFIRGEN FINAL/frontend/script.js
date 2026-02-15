
        // Tab management
        let currentTab = 'home';

        function showTab(tabName) {
            // Hide all tabs
            document.querySelectorAll('.main-container, .tab-content').forEach(tab => {
                tab.classList.remove('active');
                tab.style.display = 'none';
            });

            // Show selected tab
            const targetTab = document.getElementById(`${tabName}-tab`);
            if (targetTab) {
                if (tabName === 'home') {
                    targetTab.style.display = 'flex';
                } else {
                    targetTab.style.display = 'block';
                    targetTab.classList.add('active');
                }
            }

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

        // Initialize tab functionality
        document.addEventListener('DOMContentLoaded', () => {
            // Add click handlers to nav items
            document.querySelectorAll('.nav-item[data-tab]').forEach(item => {
                item.addEventListener('click', () => {
                    const tabName = item.getAttribute('data-tab');
                    showTab(tabName);
                });
            });

            // Show home tab by default
            showTab('home');
        });

        // State management
        let letterFile = null;
        let audioFile = null;
        let hasFiles = false;
        let isProcessing = false;

        // DOM elements
        const letterUpload = document.getElementById('letter-upload');
        const audioUpload = document.getElementById('audio-upload');
        const letterText = document.getElementById('letter-text');
        const audioText = document.getElementById('audio-text');
        const generateBtn = document.getElementById('generate-btn');
        const statusReady = document.getElementById('status-ready');
        const statusProcessing = document.getElementById('status-processing');
        const modalOverlay = document.getElementById('modal-overlay');
        const modalClose = document.getElementById('modal-close');
        const closeBtnModal = document.getElementById('close-btn');
        const copyBtn = document.getElementById('copy-btn');
        const searchInput = document.getElementById('search-input');

        // Update time
        function updateTime() {
            const now = new Date();
            const timeString = now.toLocaleDateString("en-US", {
                month: "short",
                day: "numeric",
                year: "numeric",
                hour: "2-digit",
                minute: "2-digit",
                hour12: true
            });
            document.getElementById('current-time').textContent = timeString;
        }

        // Initialize time and update every minute
        updateTime();
        setInterval(updateTime, 60000);

        // File upload handlers
        letterUpload.addEventListener('change', (e) => {
            letterFile = e.target.files[0] || null;
            letterText.textContent = letterFile ? letterFile.name : 'Upload Letter';
            updateFilesState();
        });

        audioUpload.addEventListener('change', (e) => {
            audioFile = e.target.files[0] || null;
            audioText.textContent = audioFile ? audioFile.name : 'Upload Audio';
            updateFilesState();
        });

        function updateFilesState() {
            hasFiles = !!(letterFile || audioFile);
            generateBtn.disabled = !hasFiles;
            
            if (hasFiles && !isProcessing) {
                statusReady.classList.remove('hidden');
                statusProcessing.classList.add('hidden');
            } else {
                statusReady.classList.add('hidden');
            }
        }

        // Mock FIR generation function
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

        // Generate FIR handler
        generateBtn.addEventListener('click', async () => {
            if (!hasFiles || isProcessing) return;

            isProcessing = true;
            generateBtn.innerHTML = '<div class="spinner"></div>';
            statusReady.classList.add('hidden');
            statusProcessing.classList.remove('hidden');

            try {
                // Simulate processing time
                await new Promise(resolve => setTimeout(resolve, 2000));

                const fileToProcess = letterFile || audioFile;
                let content = '';
                let filename = '';

                if (fileToProcess) {
                    filename = fileToProcess.name;
                    
                    if (fileToProcess.type.startsWith('audio/')) {
                        content = `Audio file uploaded: ${filename}. [Audio transcription would be processed here using speech-to-text AI]`;
                    } else if (fileToProcess.type.startsWith('image/')) {
                        content = `Image file uploaded: ${filename}. [Image OCR processing would be performed here to extract text]`;
                    } else {
                        const reader = new FileReader();
                        content = await new Promise((resolve, reject) => {
                            reader.onload = (e) => resolve(e.target.result);
                            reader.onerror = reject;
                            reader.readAsText(fileToProcess);
                        });
                    }
                }

                if (!content || content.trim().length < 10) {
                    throw new Error('Content too short or empty');
                }

                const firContent = generateMockFIR(content, filename);
                
                showResult({
                    success: true,
                    fir_content: firContent,
                    source_filename: filename || 'text_input',
                    processed_at: new Date().toISOString()
                });

            } catch (error) {
                console.error('Processing error:', error);
                showResult({
                    success: false,
                    error: error.message || 'Internal server error during processing'
                });
            } finally {
                isProcessing = false;
                generateBtn.innerHTML = '<svg class="generate-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9,18 15,12 9,6"></polyline></svg>';
                statusProcessing.classList.add('hidden');
                updateFilesState();
            }
        });

        // Show result modal
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

        // Close modal handlers
        modalClose.addEventListener('click', closeModal);
        closeBtnModal.addEventListener('click', closeModal);
        modalOverlay.addEventListener('click', (e) => {
            if (e.target === modalOverlay) {
                closeModal();
            }
        });

        function closeModal() {
            modalOverlay.classList.add('hidden');
        }

        // Copy to clipboard
        copyBtn.addEventListener('click', async () => {
            const content = document.getElementById('fir-content').textContent;
            if (content) {
                try {
                    await navigator.clipboard.writeText(content);
                    const copyText = document.getElementById('copy-text');
                    copyText.textContent = 'Copied!';
                    setTimeout(() => {
                        copyText.textContent = 'Copy';
                    }, 2000);
                } catch (err) {
                    console.error('Failed to copy:', err);
                }
            }
        });

        // Search functionality (placeholder)
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

        // FIR item click handlers
        document.querySelectorAll('.fir-item').forEach(item => {
            item.addEventListener('click', () => {
                console.log('Selected FIR:', item.querySelector('.fir-number').textContent);
                // In a full app, this would show FIR details
            });
        });
        // Existing code up to DOM elements... (keep your updateTime, file handlers, etc.)

// API Base URL - configurable via environment or defaults to localhost
const API_BASE = window.ENV?.API_BASE_URL || 'http://localhost:8000';
const API_KEY = window.ENV?.API_KEY || '';

// Helper function to create headers with API key
function getAuthHeaders(additionalHeaders = {}) {
    const headers = {
        'X-API-Key': API_KEY,
        ...additionalHeaders
    };
    return headers;
}

// State variables
let sessionId = null;
let currentStep = null;
let isProcessingValidation = false;

// Updated generate handler: Start processing with /process
generateBtn.addEventListener('click', async () => {
    if (!hasFiles || isProcessing) return;

    isProcessing = true;
    generateBtn.innerHTML = '<div class="spinner"></div>';
    statusReady.classList.add('hidden');
    statusProcessing.classList.remove('hidden');

    try {
        const formData = new FormData();
        if (letterFile) {
            if (letterFile.type.startsWith('image/')) {
                formData.append('image', letterFile);
            } else {
                const text = await letterFile.text();
                formData.append('text', text);  // Send as text param
            }
        }
        if (audioFile) {
            formData.append('audio', audioFile);
        }

        const response = await fetch(`${API_BASE}/process`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: formData
        });

        if (!response.ok) throw new Error(`API error: ${await response.text()}`);

        const data = await response.json();
        if (!data.success) throw new Error(data.error);

        sessionId = data.session_id;
        currentStep = data.current_step;

        // Show validation modal with content
        showValidationModal(currentStep, data.content_for_validation);

        // Start polling status
        pollSessionStatus();

    } catch (error) {
        showResult({ success: false, error: error.message || 'Failed to start processing' });
    } finally {
        isProcessing = false;
        generateBtn.innerHTML = '<svg class="generate-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9,18 15,12 9,6"></polyline></svg>';
        statusProcessing.classList.add('hidden');
        updateFilesState();
    }
});

// New: Show modal for validation steps (extend your existing modal)
function showValidationModal(step, content) {
    document.getElementById('modal-title-text').textContent = `Validate ${step.replace('_', ' ').toUpperCase()}`;
    document.getElementById('fir-content').innerHTML = formatContentForDisplay(content);  // Custom formatter below

    // Clear previous buttons
    const actions = document.querySelector('.modal-actions');
    actions.innerHTML = '';  // Clear existing buttons (keep Close/Save if needed)

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
    approveBtn.onclick = () => handleValidation(true, inputField.value);

    const regenerateBtn = document.createElement('button');
    regenerateBtn.className = 'btn-secondary';
    regenerateBtn.textContent = 'Regenerate';
    regenerateBtn.onclick = () => handleRegenerate(inputField.value);

    actions.append(inputField, approveBtn, regenerateBtn);

    modalOverlay.classList.remove('hidden');
}

// Helper: Format content nicely (e.g., for violations list)
function formatContentForDisplay(content) {
    if (typeof content === 'object') {
        if (content.violations) {
            return `<strong>Violations:</strong><ul>${content.violations.map(v => `<li>${v.section}: ${v.text}</li>`).join('')}</ul><strong>Summary:</strong> ${content.summary || ''}`;
        }
        return `<pre>${JSON.stringify(content, null, 2)}</pre>`;
    }
    return content;
}

// Handle validation/approval
async function handleValidation(approved, userInput) {
    if (isProcessingValidation) return;
    isProcessingValidation = true;

    try {
        const response = await fetch(`${API_BASE}/validate`, {
            method: 'POST',
            headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({ session_id: sessionId, approved, user_input: userInput })
        });

        if (!response.ok) throw new Error(`Validation error: ${await response.text()}`);

        const data = await response.json();
        if (!data.success) throw new Error(data.message);

        currentStep = data.current_step;

        if (data.completed) {
            showResult({ success: true, fir_content: data.content.fir_content, source_filename: `FIR #${data.content.fir_number}` });
            updateFIRList();  // Refresh sidebar
            modalOverlay.classList.add('hidden');
        } else {
            showValidationModal(currentStep, data.content);
        }
    } catch (error) {
        showResult({ success: false, error: error.message });
    } finally {
        isProcessingValidation = false;
    }
}

// Handle regeneration
async function handleRegenerate(userInput) {
    if (isProcessingValidation) return;
    isProcessingValidation = true;

    try {
        const response = await fetch(`${API_BASE}/regenerate/${sessionId}`, {
            method: 'POST',
            headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({ step: currentStep, user_input: userInput })
        });

        if (!response.ok) throw new Error(`Regeneration error: ${await response.text()}`);

        const data = await response.json();
        if (data.success) {
            showValidationModal(currentStep, data.content);
        }
    } catch (error) {
        showResult({ success: false, error: error.message });
    } finally {
        isProcessingValidation = false;
    }
}

// Poll session status every 5 seconds
function pollSessionStatus() {
    const interval = setInterval(async () => {
        if (!sessionId) {
            clearInterval(interval);
            return;
        }

        try {
            const response = await fetch(`${API_BASE}/session/${sessionId}/status`, {
                headers: getAuthHeaders()
            });
            const status = await response.json();

            if (status.status === 'completed') {
                const firResponse = await fetch(`${API_BASE}/fir/${status.validation_history?.at(-1)?.content?.fir_number || ''}`, {
                    headers: getAuthHeaders()
                });
                const firData = await firResponse.json();
                showResult({ success: true, fir_content: firData.content });
                updateFIRList();
                clearInterval(interval);
            } else if (status.status === 'error') {
                showResult({ success: false, error: 'Session error occurred' });
                clearInterval(interval);
            }
        } catch (error) {
            console.error('Status poll error:', error);
        }
    }, 5000);
}

// New: Update sidebar FIR list (fetch from backend, e.g., add a /list-firs endpoint in file 1 if needed)
async function updateFIRList() {
    // For now, mock or extend file 1 with a GET /list-firs endpoint returning array of FIRs
    // Example: const response = await fetch(`${API_BASE}/list-firs`); const firs = await response.json();
    // Then populate .fir-list
    // Placeholder: Keep your static list or fetch dynamically
}

// Existing closeModal, copy, etc. (keep them)

// Add to startup: Load initial FIR list
document.addEventListener('DOMContentLoaded', () => {
    // ... existing code
    updateFIRList();
});

