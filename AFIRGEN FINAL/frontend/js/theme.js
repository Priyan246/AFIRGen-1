/**
 * Theme Module
 * Handles dark mode / light mode toggle and persistence
 */

const THEME_KEY = 'afirgen-theme';
const THEME_DARK = 'dark';
const THEME_LIGHT = 'light';

/**
 * Initialize theme system
 */
function initTheme() {
    // Load saved theme preference or use system preference
    const savedTheme = getSavedTheme();
    const systemPreference = getSystemPreference();
    const initialTheme = savedTheme || systemPreference;
    
    // Apply initial theme
    applyTheme(initialTheme);
    
    // Set up toggle button
    setupToggleButton();
    
    // Listen for system preference changes
    watchSystemPreference();
}

/**
 * Get saved theme from localStorage
 */
function getSavedTheme() {
    try {
        return localStorage.getItem(THEME_KEY);
    } catch (error) {
        console.error('Error reading theme preference:', error);
        return null;
    }
}

/**
 * Save theme to localStorage
 */
function saveTheme(theme) {
    try {
        localStorage.setItem(THEME_KEY, theme);
    } catch (error) {
        console.error('Error saving theme preference:', error);
    }
}

/**
 * Get system color scheme preference
 */
function getSystemPreference() {
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
        return THEME_LIGHT;
    }
    return THEME_DARK;
}

/**
 * Watch for system preference changes
 */
function watchSystemPreference() {
    if (!window.matchMedia) return;
    
    const mediaQuery = window.matchMedia('(prefers-color-scheme: light)');
    
    // Modern browsers
    if (mediaQuery.addEventListener) {
        mediaQuery.addEventListener('change', (e) => {
            // Only apply system preference if user hasn't set a preference
            if (!getSavedTheme()) {
                applyTheme(e.matches ? THEME_LIGHT : THEME_DARK);
            }
        });
    }
    // Older browsers
    else if (mediaQuery.addListener) {
        mediaQuery.addListener((e) => {
            if (!getSavedTheme()) {
                applyTheme(e.matches ? THEME_LIGHT : THEME_DARK);
            }
        });
    }
}

/**
 * Apply theme to document
 */
function applyTheme(theme) {
    const body = document.body;
    
    if (theme === THEME_LIGHT) {
        body.classList.add('light-mode');
    } else {
        body.classList.remove('light-mode');
    }
    
    // Update aria-label on toggle button
    updateToggleButtonLabel(theme);
}

/**
 * Toggle between dark and light mode
 */
function toggleTheme() {
    const body = document.body;
    const isLightMode = body.classList.contains('light-mode');
    const newTheme = isLightMode ? THEME_DARK : THEME_LIGHT;
    
    // Apply new theme
    applyTheme(newTheme);
    
    // Save preference
    saveTheme(newTheme);
    
    // Show toast notification
    if (window.showToast) {
        const message = isLightMode ? 'Dark mode enabled' : 'Light mode enabled';
        window.showToast(message, 'info', 2000);
    }
}

/**
 * Set up toggle button event listener
 */
function setupToggleButton() {
    const toggleBtn = document.getElementById('theme-toggle');
    
    if (toggleBtn) {
        toggleBtn.addEventListener('click', toggleTheme);
        
        // Also support keyboard activation
        toggleBtn.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                toggleTheme();
            }
        });
    }
}

/**
 * Update toggle button aria-label
 */
function updateToggleButtonLabel(theme) {
    const toggleBtn = document.getElementById('theme-toggle');
    
    if (toggleBtn) {
        const label = theme === THEME_LIGHT 
            ? 'Switch to dark mode' 
            : 'Switch to light mode';
        toggleBtn.setAttribute('aria-label', label);
    }
}

/**
 * Get current theme
 */
function getCurrentTheme() {
    return document.body.classList.contains('light-mode') ? THEME_LIGHT : THEME_DARK;
}

// Export functions
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        initTheme,
        toggleTheme,
        getCurrentTheme,
        applyTheme
    };
}

// Make functions available globally
if (typeof window !== 'undefined') {
    window.Theme = {
        init: initTheme,
        toggle: toggleTheme,
        getCurrent: getCurrentTheme,
        apply: applyTheme
    };
}
