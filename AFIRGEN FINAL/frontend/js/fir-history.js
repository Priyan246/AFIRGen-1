/**
 * FIR History Module
 * Handles FIR list fetching, caching, search, filter, and pagination
 */

import { setDB, getDB, getAllDB, STORES, queryDB } from './storage.js';

// Configuration
const ITEMS_PER_PAGE = 10;
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

// State
let currentPage = 1;
let totalPages = 1;
let allFIRs = [];
let filteredFIRs = [];
let currentFilter = 'all';
let currentSort = 'date-desc';
let searchQuery = '';
let isInitialized = false;

/**
 * Initialize FIR history feature
 */
async function initFIRHistory() {
    if (isInitialized) {
        console.log('[FIR History] Already initialized');
        return;
    }
    
    try {
        // Load FIR list from cache or fetch from API
        await loadFIRList();
        
        // Set up event listeners
        setupEventListeners();
        
        // Render initial list
        renderFIRList();
        
        isInitialized = true;
        console.log('[FIR History] Initialized successfully');
    } catch (error) {
        console.error('Error initializing FIR history:', error);
        showError('Failed to load FIR history');
    }
}

/**
 * Load FIR list from IndexedDB cache or fetch from API
 */
async function loadFIRList() {
    try {
        // Try to load from IndexedDB first
        const cachedFIRs = await getAllDB(STORES.FIR_HISTORY);
        
        if (cachedFIRs && cachedFIRs.length > 0) {
            allFIRs = cachedFIRs;
            applyFiltersAndSort();
            return;
        }
        
        // If no cache, fetch from API
        await fetchFIRList();
    } catch (error) {
        console.error('Error loading FIR list:', error);
        throw error;
    }
}

/**
 * Fetch FIR list from API
 */
async function fetchFIRList() {
    try {
        showLoading();
        
        // TODO: Replace with actual API endpoint when backend is ready
        // For now, use mock data
        const mockFIRs = generateMockFIRs();
        
        // Store in IndexedDB
        for (const fir of mockFIRs) {
            await setDB(STORES.FIR_HISTORY, fir.id, fir);
        }
        
        allFIRs = mockFIRs;
        applyFiltersAndSort();
        hideLoading();
    } catch (error) {
        hideLoading();
        console.error('Error fetching FIR list:', error);
        throw error;
    }
}

/**
 * Generate mock FIR data for testing
 * TODO: Remove when backend API is ready
 */
function generateMockFIRs() {
    const statuses = ['pending', 'investigating', 'closed'];
    const complainants = [
        'John Doe - Downtown Market',
        'Jane Smith - Parking Dispute',
        'Michael Johnson - Fraud Case',
        'Sarah Williams - Theft Report',
        'Robert Brown - Assault Case',
        'Emily Davis - Property Damage',
        'David Wilson - Harassment',
        'Lisa Anderson - Burglary',
        'James Taylor - Vandalism',
        'Mary Martinez - Missing Person'
    ];
    
    const firs = [];
    const currentYear = new Date().getFullYear();
    
    for (let i = 1; i <= 25; i++) {
        const date = new Date();
        date.setDate(date.getDate() - Math.floor(Math.random() * 90)); // Random date within last 90 days
        
        firs.push({
            id: `FIR-${currentYear}-${String(i).padStart(3, '0')}`,
            number: `${currentYear}/${String(i).padStart(3, '0')}`,
            complainant: complainants[i % complainants.length],
            status: statuses[Math.floor(Math.random() * statuses.length)],
            date: date.toISOString(),
            description: `Case description for FIR #${i}`,
            location: 'Moggapair West (V7)',
            officer: 'Officer Name'
        });
    }
    
    return firs;
}

/**
 * Apply filters and sorting to FIR list
 */
function applyFiltersAndSort() {
    // Start with all FIRs
    let result = [...allFIRs];
    
    // Apply search filter
    if (searchQuery) {
        const query = searchQuery.toLowerCase();
        result = result.filter(fir => 
            fir.number.toLowerCase().includes(query) ||
            fir.complainant.toLowerCase().includes(query) ||
            fir.date.toLowerCase().includes(query)
        );
    }
    
    // Apply status filter
    if (currentFilter !== 'all') {
        result = result.filter(fir => fir.status === currentFilter);
    }
    
    // Apply sorting
    result.sort((a, b) => {
        switch (currentSort) {
            case 'date-desc':
                return new Date(b.date) - new Date(a.date);
            case 'date-asc':
                return new Date(a.date) - new Date(b.date);
            case 'status':
                return a.status.localeCompare(b.status);
            default:
                return 0;
        }
    });
    
    filteredFIRs = result;
    totalPages = Math.ceil(filteredFIRs.length / ITEMS_PER_PAGE);
    currentPage = 1; // Reset to first page when filters change
}

/**
 * Render FIR list
 */
function renderFIRList() {
    const listContainer = document.getElementById('fir-list');
    const loadingEl = document.getElementById('fir-list-loading');
    const emptyEl = document.getElementById('fir-list-empty');
    
    if (!listContainer) return;
    
    // Clear existing items (except loading and empty states)
    const existingItems = listContainer.querySelectorAll('.fir-item');
    existingItems.forEach(item => item.remove());
    
    // Show empty state if no results
    if (filteredFIRs.length === 0) {
        emptyEl?.classList.remove('hidden');
        updatePagination();
        return;
    }
    
    emptyEl?.classList.add('hidden');
    
    // Calculate pagination
    const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
    const endIndex = Math.min(startIndex + ITEMS_PER_PAGE, filteredFIRs.length);
    const pageItems = filteredFIRs.slice(startIndex, endIndex);
    
    // Render items
    pageItems.forEach(fir => {
        const item = createFIRItem(fir);
        listContainer.appendChild(item);
    });
    
    updatePagination();
}

/**
 * Create FIR item element
 */
function createFIRItem(fir) {
    const item = document.createElement('div');
    item.className = 'fir-item';
    item.setAttribute('role', 'listitem');
    item.setAttribute('tabindex', '0');
    item.setAttribute('data-fir-id', fir.id);
    item.setAttribute('aria-label', `FIR #${fir.number}, ${fir.complainant}, Status: ${fir.status}`);
    
    const statusClass = `status-${fir.status}`;
    
    item.innerHTML = `
        <div class="fir-number">FIR #${fir.number}</div>
        <div class="fir-complainant">${escapeHTML(fir.complainant)}</div>
        <div class="fir-status ${statusClass}">${capitalizeFirst(fir.status)}</div>
    `;
    
    // Add click handler
    item.addEventListener('click', () => handleFIRClick(fir));
    item.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            handleFIRClick(fir);
        }
    });
    
    return item;
}

/**
 * Handle FIR item click
 */
function handleFIRClick(fir) {
    // TODO: Implement FIR detail view
    console.log('FIR clicked:', fir);
    
    // For now, show a toast
    if (window.showToast) {
        window.showToast(`Viewing FIR #${fir.number}`, 'info');
    }
}

/**
 * Update pagination controls
 */
function updatePagination() {
    const paginationEl = document.getElementById('fir-pagination');
    const prevBtn = document.getElementById('fir-prev-page');
    const nextBtn = document.getElementById('fir-next-page');
    const pageInfo = document.getElementById('fir-page-info');
    
    if (!paginationEl) return;
    
    // Show/hide pagination
    if (totalPages <= 1) {
        paginationEl.classList.add('hidden');
        return;
    }
    
    paginationEl.classList.remove('hidden');
    
    // Update buttons
    if (prevBtn) {
        prevBtn.disabled = currentPage === 1;
    }
    
    if (nextBtn) {
        nextBtn.disabled = currentPage === totalPages;
    }
    
    // Update page info
    if (pageInfo) {
        pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
    }
}

/**
 * Set up event listeners
 */
function setupEventListeners() {
    // Search input
    const searchInput = document.getElementById('fir-search-input');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                searchQuery = e.target.value;
                applyFiltersAndSort();
                renderFIRList();
            }, 300); // Debounce 300ms
        });
    }
    
    // Status filter
    const statusFilter = document.getElementById('fir-status-filter');
    if (statusFilter) {
        statusFilter.addEventListener('change', (e) => {
            currentFilter = e.target.value;
            applyFiltersAndSort();
            renderFIRList();
        });
    }
    
    // Sort select
    const sortSelect = document.getElementById('fir-sort-select');
    if (sortSelect) {
        sortSelect.addEventListener('change', (e) => {
            currentSort = e.target.value;
            applyFiltersAndSort();
            renderFIRList();
        });
    }
    
    // Pagination buttons
    const prevBtn = document.getElementById('fir-prev-page');
    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            if (currentPage > 1) {
                currentPage--;
                renderFIRList();
            }
        });
    }
    
    const nextBtn = document.getElementById('fir-next-page');
    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            if (currentPage < totalPages) {
                currentPage++;
                renderFIRList();
            }
        });
    }
}

/**
 * Show loading state
 */
function showLoading() {
    const loadingEl = document.getElementById('fir-list-loading');
    const emptyEl = document.getElementById('fir-list-empty');
    
    if (loadingEl) {
        loadingEl.classList.remove('hidden');
    }
    if (emptyEl) {
        emptyEl.classList.add('hidden');
    }
}

/**
 * Hide loading state
 */
function hideLoading() {
    const loadingEl = document.getElementById('fir-list-loading');
    if (loadingEl) {
        loadingEl.classList.add('hidden');
    }
}

/**
 * Show error message
 */
function showError(message) {
    if (window.showToast) {
        window.showToast(message, 'error');
    } else {
        console.error(message);
    }
}

/**
 * Refresh FIR list from API
 */
async function refreshFIRList() {
    try {
        await fetchFIRList();
        renderFIRList();
        
        if (window.showToast) {
            window.showToast('FIR list refreshed', 'success');
        }
    } catch (error) {
        showError('Failed to refresh FIR list');
    }
}

/**
 * Add new FIR to list
 */
async function addFIR(fir) {
    try {
        // Store in IndexedDB
        await setDB(STORES.FIR_HISTORY, fir.id, fir);
        
        // Add to local array
        allFIRs.unshift(fir); // Add to beginning
        
        // Re-apply filters and render
        applyFiltersAndSort();
        renderFIRList();
    } catch (error) {
        console.error('Error adding FIR:', error);
        throw error;
    }
}

// Utility functions
function escapeHTML(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function capitalizeFirst(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

// Export functions
export {
    initFIRHistory,
    refreshFIRList,
    addFIR,
    loadFIRList,
    renderFIRList
};


// Make functions available globally for non-module scripts
if (typeof window !== 'undefined') {
    window.initFIRHistory = initFIRHistory;
    window.refreshFIRList = refreshFIRList;
    window.addFIR = addFIR;
}
