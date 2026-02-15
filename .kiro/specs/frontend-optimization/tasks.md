# Implementation Plan: AFIRGen Frontend Optimization

## Overview

This implementation plan breaks down the frontend optimization into discrete, actionable tasks organized by priority. The plan follows a phased approach: Core Improvements (P0) → Performance (P1) → Features (P1) → Advanced Features (P2) → Polish (P2).

## Tasks

### Phase 1: Core Improvements (P0 - Critical)

- [ ] 1. Set up build tooling and project structure
  - [x] 1.1 Initialize npm project
    - Create package.json with dependencies
    - Install dev dependencies: terser, cssnano, html-minifier, eslint, prettier, jest
    - Configure npm scripts for build, test, lint
    - _Requirements: 5.6.6_
  
  - [x] 1.2 Configure ESLint and Prettier
    - Create .eslintrc.json with rules
    - Create .prettierrc.json with formatting rules
    - Add pre-commit hooks with husky
    - _Requirements: 5.6.1, 5.6.2_
  
  - [x] 1.3 Restructure project files
    - Rename base.html to index.html
    - Create css/, js/, lib/, assets/ directories
    - Split script.js into modules (api.js, ui.js, validation.js, etc.)
    - Split style.css into main.css and themes.css
    - _Requirements: 5.6.5_

- [ ] 2. Implement validation module
  - [x] 2.1 Create validation.js with file validation
    - Implement validateFile(file, options)
    - Implement validateFileType(file, allowedTypes)
    - Implement validateFileSize(file, maxSize)
    - Implement validateMimeType(file) with magic number check
    - Whitelist: .jpg, .jpeg, .png, .pdf, .wav, .mp3
    - Max size: 10MB
    - _Requirements: 5.3.2, 5.3.3_
  
  - [x] 2.2 Write property test for file validation
    - **Property 1: File Validation Before Upload**
    - **Validates: Requirements 5.3.2, 5.3.3**
    - Generate random files with various types, sizes, MIME types
    - Verify only valid files pass validation
  
  - [x] 2.3 Add input validation functions
    - Implement validateText(text, options)
    - Implement sanitizeInput(input)
    - Implement validateForm(formData)
    - Add length limits, format checks
    - _Requirements: 5.3.1_

- [ ] 3. Implement security module
  - [x] 3.1 Integrate DOMPurify library
    - Download dompurify.min.js to lib/
    - Create security.js wrapper
    - Implement sanitizeHTML(html) with DOMPurify
    - Implement sanitizeText(text) for plain text
    - Implement escapeHTML(str) for HTML entities
    - _Requirements: 5.3.1_
  
  - [x] 3.2 Write property test for input sanitization
    - **Property 2: Input Sanitization**
    - **Validates: Requirements 5.3.1**
    - Generate various XSS payloads
    - Verify all are sanitized and rendered safely
  
  - [x] 3.3 Add Content Security Policy
    - Update index.html with CSP meta tag
    - Configure CSP: default-src 'self', script-src, style-src, etc.
    - Test CSP with browser console
    - _Requirements: 5.3.6_

- [ ] 4. Implement UI module with loading states
  - [x] 4.1 Create ui.js with loading functions
    - Implement showLoading(element, message)
    - Implement hideLoading(element)
    - Implement showProgress(element, percentage)
    - Add spinner CSS animations
    - _Requirements: 5.2.1_
  
  - [x] 4.2 Write property test for loading state visibility
    - **Property 4: Loading State Visibility**
    - **Validates: Requirements 5.2.1**
    - Measure time between operation start and loading indicator display
    - Verify <100ms
  
  - [x] 4.3 Add loading states to all async operations
    - File upload: Show progress bar
    - API calls: Show spinner
    - FIR generation: Show processing message
    - _Requirements: 5.2.1, 5.2.2_

- [x] 5. Implement toast notification system
  - [x] 5.1 Create toast UI component
    - Add toast container to index.html
    - Style toast with CSS (success, error, warning, info)
    - Implement showToast(message, type, duration) in ui.js
    - Implement hideToast(toastId) in ui.js
    - Add slide-in animation
    - _Requirements: 5.2.3_
  
  - [x] 5.2 Write property test for toast notifications
    - **Property 8: Toast Notification Display**
    - **Validates: Requirements 5.2.3**
    - Trigger various actions
    - Verify toast appears within 200ms with correct message
  
  - [x] 5.3 Replace all alert() calls with toasts
    - Update error handling to use showToast()
    - Update success messages to use showToast()
    - Remove all alert() and confirm() calls
    - _Requirements: 5.2.3_

- [ ] 6. Implement enhanced error handling
  - [x] 6.1 Create error handling utilities
    - Implement handleNetworkError(error) in api.js
    - Implement handleAPIError(response) in api.js
    - Implement handleValidationError(errors) in validation.js
    - Map error codes to user-friendly messages
    - _Requirements: 5.2.3_
  
  - [x] 6.2 Add error recovery mechanisms
    - Implement automatic retry for network errors
    - Implement "Reload page" button for critical errors
    - Implement error logging to console
    - _Requirements: 5.1.7_
  
  - [x] 6.3 Update all error handling to use new system
    - Replace generic error messages with specific ones
    - Add error context (what operation failed)
    - Show actionable error messages
    - _Requirements: 5.2.3_

- [ ] 7. Implement basic accessibility features
  - [x] 7.1 Add ARIA labels to all interactive elements
    - Add aria-label to all buttons
    - Add aria-labelledby to all inputs
    - Add aria-hidden="true" to decorative icons
    - Add role attributes to landmarks
    - _Requirements: 5.4.2_
  
  - [x] 7.2 Implement keyboard navigation
    - Ensure logical tab order
    - Add keyboard event handlers (Enter, Space, Escape)
    - Implement focus trap in modals
    - Add visible focus indicators (2px outline)
    - _Requirements: 5.4.3_
  
  - [x] 7.3 Write property test for keyboard navigation
    - **Property 5: Keyboard Navigation**
    - **Validates: Requirements 5.4.3**
    - Navigate entire application using only keyboard
    - Verify all features accessible
  
  - [x] 7.4 Add skip links and semantic HTML
    - Add "Skip to main content" link
    - Use semantic HTML: <nav>, <main>, <aside>
    - Use <button> for buttons (not <div>)
    - _Requirements: 5.4.6_

- [x] 8. Checkpoint - Validate Phase 1
  - Run all unit tests and property tests
  - Run ESLint and fix any errors
  - Test file upload with validation
  - Test error handling with toasts
  - Test keyboard navigation
  - Verify ARIA labels with axe DevTools
  - Ensure all tests pass, ask the user if questions arise.

### Phase 2: Performance Optimizations (P1 - High Priority)

- [x] 9. Implement API client with retry and caching
  - [x] 9.1 Create api.js module
    - Implement APIClient class
    - Implement request(endpoint, options) method
    - Implement get(endpoint, params) method
    - Implement post(endpoint, body, isFormData) method
    - Add request timeout (30s)
    - _Requirements: 5.1.6, 5.1.7_
  
  - [x] 9.2 Add retry logic with exponential backoff
    - Implement retryRequest(fn, maxRetries, backoff)
    - Retry on network errors and 5xx responses
    - Exponential backoff: 1s, 2s, 4s
    - Max 3 retries
    - _Requirements: 5.1.7_
  
  - [x] 9.3 Write property test for API request retry
    - **Property 3: API Request Retry**
    - **Validates: Requirements 5.1.7**
    - Simulate network failures and 5xx responses
    - Verify retry logic executes correctly
  
  - [x] 9.4 Add response caching
    - Implement getCached(key) method
    - Implement setCached(key, data, ttl) method
    - Implement clearCache() method
    - Default TTL: 5 minutes
    - Cache in memory (Map object)
    - _Requirements: 5.1.6_
  
  - [x] 9.5 Migrate existing API calls to new client
    - Replace all fetch() calls with APIClient
    - Update error handling to use new system
    - Test all API endpoints
    - _Requirements: 5.1.6, 5.1.7_

- [ ] 10. Implement minification and bundling
  - [ ] 10.1 Create build scripts
    - Add npm script: build:css (cssnano)
    - Add npm script: build:js (terser)
    - Add npm script: build:html (html-minifier)
    - Add npm script: build (run all)
    - _Requirements: 5.6.6_
  
  - [ ] 10.2 Configure minification tools
    - Configure terser: mangle, compress, source maps
    - Configure cssnano: preset-default
    - Configure html-minifier: collapseWhitespace, removeComments
    - _Requirements: 5.6.6_
  
  - [ ] 10.3 Create dist/ output directory
    - Build minified files to dist/
    - Copy assets to dist/assets/
    - Generate source maps
    - _Requirements: 5.6.6, 5.6.7_
  
  - [ ] 10.4 Verify bundle sizes
    - Measure gzipped sizes
    - Verify main.css <50KB
    - Verify app.js <100KB
    - Verify total <500KB
    - _Requirements: 5.1.5_

- [ ] 11. Implement service worker for offline capability
  - [ ] 11.1 Create sw.js service worker
    - Implement install event (cache static assets)
    - Implement activate event (clean old caches)
    - Implement fetch event (cache-first for assets, network-first for API)
    - Define cache names and versions
    - _Requirements: 5.1.8, 5.5.6_
  
  - [ ] 11.2 Register service worker in app.js
    - Check if service worker supported
    - Register sw.js
    - Handle registration success/failure
    - _Requirements: 5.1.8_
  
  - [ ] 11.3 Write property test for offline mode
    - **Property 6: Offline Mode Functionality**
    - **Validates: Requirements 5.5.6**
    - Load application, go offline
    - Verify cached data accessible and operations queued
  
  - [ ] 11.4 Implement offline fallback page
    - Create offline.html
    - Show friendly message when offline
    - Cache offline.html in service worker
    - _Requirements: 5.5.6_

- [ ] 12. Optimize assets
  - [ ] 12.1 Optimize images
    - Convert images to WebP format
    - Compress images (quality 85)
    - Add lazy loading to images
    - Use responsive images (srcset)
    - _Requirements: 5.1.3_
  
  - [ ] 12.2 Optimize fonts
    - Use system fonts where possible
    - Subset custom fonts (only needed characters)
    - Preload critical fonts
    - Use font-display: swap
    - _Requirements: 5.1.3_
  
  - [ ] 12.3 Add resource hints
    - Add preconnect to API domain
    - Add dns-prefetch for CDN
    - Add prefetch for critical resources
    - _Requirements: 5.1.4_

- [ ] 13. Run performance tests
  - [ ] 13.1 Run Lighthouse audit
    - Run Lighthouse in Chrome DevTools
    - Verify performance score >90
    - Verify FCP <1s, TTI <3s
    - Fix any issues identified
    - _Requirements: 5.1.4_
  
  - [ ] 13.2 Test on 3G network
    - Use Chrome DevTools network throttling
    - Verify page load <2s on 3G
    - Verify app usable on slow connection
    - _Requirements: 5.1.1_
  
  - [ ] 13.3 Measure bundle sizes
    - Verify total bundle <500KB gzipped
    - Verify no single file >200KB
    - _Requirements: 5.1.5_

- [ ] 14. Checkpoint - Validate Phase 2
  - Run all tests (unit, property, E2E)
  - Run Lighthouse audit (score >90)
  - Verify bundle sizes <500KB
  - Test offline mode
  - Test on 3G network
  - Ensure all tests pass, ask the user if questions arise.

### Phase 3: New Features (P1 - High Priority)

- [ ] 15. Implement FIR history feature
  - [ ] 15.1 Create storage.js module
    - Implement setLocal(key, value, ttl) for LocalStorage
    - Implement getLocal(key) for LocalStorage
    - Implement setDB(store, key, value) for IndexedDB
    - Implement getDB(store, key) for IndexedDB
    - Implement getAllDB(store) for IndexedDB
    - _Requirements: 5.5.5_
  
  - [ ] 15.2 Create FIR history UI
    - Update sidebar to show dynamic FIR list
    - Add search input for FIR history
    - Add filter dropdown (status)
    - Add sort dropdown (date, status)
    - Add pagination or infinite scroll
    - _Requirements: 5.5.1_
  
  - [ ] 15.3 Implement FIR history data fetching
    - Create getFIRList() function in api.js
    - Fetch FIR list from backend (GET /fir/list)
    - Cache FIR list in IndexedDB
    - Refresh on page load and after new FIR
    - _Requirements: 5.5.1_
  
  - [ ] 15.4 Implement search and filter
    - Filter by FIR number, complainant, date
    - Filter by status (pending, investigating, closed)
    - Sort by date (newest first)
    - Update UI in real-time
    - _Requirements: 5.5.1_
  
  - [ ] 15.5 Test FIR history feature
    - Test with empty list
    - Test with 100+ FIRs
    - Test search functionality
    - Test filter functionality
    - Test pagination
    - _Requirements: 5.5.1_

- [ ] 16. Implement dark mode
  - [ ] 16.1 Create themes.css with dark mode styles
    - Define CSS custom properties for colors
    - Create .dark-mode class with dark colors
    - Ensure contrast ratio >4.5:1 for text
    - Add smooth transition (0.3s)
    - _Requirements: 5.5.4_
  
  - [ ] 16.2 Write property test for dark mode consistency
    - **Property 7: Dark Mode Consistency**
    - **Validates: Requirements 5.4.7**
    - Enable dark mode
    - Measure contrast ratios for all text and UI elements
  
  - [ ] 16.3 Add dark mode toggle button
    - Add toggle button to navbar
    - Implement toggleDarkMode() function
    - Toggle .dark-mode class on <body>
    - Persist preference in LocalStorage
    - _Requirements: 5.5.4_
  
  - [ ] 16.4 Test dark mode
    - Test all pages in dark mode
    - Verify contrast ratios
    - Test toggle persistence
    - Test smooth transition
    - _Requirements: 5.5.4_

- [ ] 17. Implement drag-and-drop file upload
  - [ ] 17.1 Create drag-and-drop zone
    - Add drop zone UI to file upload area
    - Style drop zone with dashed border
    - Add hover state for drag-over
    - _Requirements: 5.2.4_
  
  - [ ] 17.2 Implement drag-and-drop handlers
    - Add dragover event listener
    - Add dragleave event listener
    - Add drop event listener
    - Prevent default browser behavior
    - Validate dropped files
    - _Requirements: 5.2.4_
  
  - [ ] 17.3 Add visual feedback
    - Highlight drop zone on drag-over
    - Show file preview after drop
    - Show error if invalid file
    - _Requirements: 5.2.4_
  
  - [ ] 17.4 Test drag-and-drop
    - Test with valid files
    - Test with invalid files
    - Test with multiple files
    - Test on different browsers
    - _Requirements: 5.2.4_

- [ ] 18. Checkpoint - Validate Phase 3
  - Test FIR history with various data
  - Test dark mode on all pages
  - Test drag-and-drop file upload
  - Run accessibility tests
  - Run performance tests
  - Ensure all tests pass, ask the user if questions arise.

### Phase 4: Advanced Features (P2 - Nice to Have)

- [ ] 19. Implement PDF export
  - [ ] 19.1 Integrate jsPDF library
    - Download jspdf.min.js to lib/
    - Create pdf.js module
    - Implement generatePDF(firData, options)
    - Implement downloadPDF(pdf, filename)
    - Implement printPDF(pdf)
    - _Requirements: 5.5.2_
  
  - [ ] 19.2 Write property test for PDF export
    - **Property 10: PDF Export Completeness**
    - **Validates: Requirements 5.5.2**
    - Generate PDFs from various FIR data
    - Verify all fields present and formatting correct
  
  - [ ] 19.3 Design PDF layout
    - A4 portrait format
    - Header: FIR number, date
    - Body: All FIR fields
    - Footer: Page number, generated timestamp
    - Professional formatting
    - _Requirements: 5.5.2_
  
  - [ ] 19.4 Add PDF export button to modal
    - Add "Export PDF" button to FIR modal
    - Trigger PDF generation on click
    - Download PDF automatically
    - Show success toast
    - _Requirements: 5.5.2_
  
  - [ ] 19.5 Test PDF export
    - Test with various FIR data
    - Verify all fields included
    - Verify formatting correct
    - Test download functionality
    - _Requirements: 5.5.2_

- [ ] 20. Implement PWA features
  - [ ] 20.1 Create manifest.json
    - Define app name, short name
    - Add icons (192x192, 512x512)
    - Set start_url, display, theme_color
    - _Requirements: 5.5.8_
  
  - [ ] 20.2 Add manifest to index.html
    - Link manifest.json in <head>
    - Add theme-color meta tag
    - Add apple-touch-icon
    - _Requirements: 5.5.8_
  
  - [ ] 20.3 Implement install prompt
    - Listen for beforeinstallprompt event
    - Show "Add to Home Screen" button
    - Trigger install prompt on button click
    - Hide button after install
    - _Requirements: 5.5.8_
  
  - [ ] 20.4 Test PWA installation
    - Test on Chrome (desktop and mobile)
    - Test on Safari (iOS)
    - Verify app installs correctly
    - Verify app works offline
    - _Requirements: 5.5.8_

- [ ] 21. Implement advanced accessibility features
  - [ ] 21.1 Add ARIA live regions
    - Add aria-live="polite" to toast container
    - Add aria-live="assertive" to status messages
    - Add aria-busy="true" to loading states
    - _Requirements: 5.4.2_
  
  - [ ] 21.2 Implement focus management
    - Focus trap in modals
    - Return focus to trigger after modal close
    - Move focus to first element in modal on open
    - _Requirements: 5.4.5_
  
  - [ ] 21.3 Add screen reader announcements
    - Announce status changes
    - Announce errors immediately
    - Announce success after completion
    - _Requirements: 5.4.4_
  
  - [ ] 21.4 Test with screen readers
    - Test with NVDA (Windows)
    - Test with VoiceOver (macOS/iOS)
    - Verify all content accessible
    - Verify announcements work
    - _Requirements: 5.4.4_

- [ ] 22. Implement real-time validation feedback
  - [ ] 22.1 Add input event listeners
    - Listen for input events on all form fields
    - Debounce validation (300ms)
    - Show inline error messages
    - Highlight invalid fields
    - _Requirements: 5.2.5_
  
  - [ ] 22.2 Write property test for form validation feedback
    - **Property 9: Form Validation Feedback**
    - **Validates: Requirements 5.2.5**
    - Enter invalid data in form fields
    - Measure time to error message display
  
  - [ ] 22.3 Style validation feedback
    - Red border for invalid fields
    - Green border for valid fields
    - Inline error message below field
    - Icon indicator (✓ or ✗)
    - _Requirements: 5.2.5_
  
  - [ ] 22.4 Test validation feedback
    - Test with various invalid inputs
    - Verify error messages appear <300ms
    - Verify error messages are helpful
    - Test on all form fields
    - _Requirements: 5.2.5_

- [ ] 23. Checkpoint - Validate Phase 4
  - Test PDF export with various FIRs
  - Test PWA installation
  - Test advanced accessibility features
  - Test real-time validation
  - Run Lighthouse audit (all categories >90)
  - Ensure all tests pass, ask the user if questions arise.

### Phase 5: Polish and Testing (P2 - Nice to Have)

- [ ] 24. Add animations and transitions
  - [ ] 24.1 Add page transitions
    - Fade in on page load
    - Slide in for modals
    - Slide in for toasts
    - _Requirements: 5.2.8_
  
  - [ ] 24.2 Add micro-interactions
    - Button hover effects
    - Input focus effects
    - Card hover effects
    - Loading animations
    - _Requirements: 5.2.8_
  
  - [ ] 24.3 Optimize animations for performance
    - Use CSS transforms (not position)
    - Use will-change for animated elements
    - Reduce motion for users with prefers-reduced-motion
    - _Requirements: 5.2.8_

- [ ] 25. Implement print styles
  - [ ] 25.1 Create print.css
    - Hide navigation and sidebar
    - Optimize layout for printing
    - Use print-friendly colors
    - Add page breaks
    - _Requirements: 5.5.3_
  
  - [ ] 25.2 Add print button
    - Add "Print" button to FIR modal
    - Trigger window.print() on click
    - _Requirements: 5.5.3_
  
  - [ ] 25.3 Test print functionality
    - Test print preview
    - Verify layout correct
    - Test on different browsers
    - _Requirements: 5.5.3_

- [ ] 26. Write comprehensive unit tests
  - [ ] 26.1 Write tests for api.js
    - Test request() method
    - Test retry logic
    - Test caching
    - Test error handling
    - _Requirements: 5.6.3_
  
  - [ ] 26.2 Write tests for validation.js
    - Test file validation
    - Test input validation
    - Test form validation
    - _Requirements: 5.6.3_
  
  - [ ] 26.3 Write tests for security.js
    - Test sanitizeHTML()
    - Test sanitizeText()
    - Test XSS prevention
    - _Requirements: 5.6.3_
  
  - [ ] 26.4 Write tests for ui.js
    - Test showToast()
    - Test showLoading()
    - Test showModal()
    - _Requirements: 5.6.3_
  
  - [ ] 26.5 Write tests for storage.js
    - Test LocalStorage operations
    - Test IndexedDB operations
    - _Requirements: 5.6.3_
  
  - [ ] 26.6 Verify test coverage >80%
    - Run coverage report
    - Add tests for uncovered code
    - _Requirements: 5.6.3_

- [ ] 27. Write E2E tests
  - [ ] 27.1 Set up Playwright
    - Install Playwright
    - Configure playwright.config.js
    - Create tests/ directory
    - _Requirements: 5.6.4_
  
  - [ ] 27.2 Write critical flow tests
    - Test: Upload file → Generate FIR → Validate → Complete
    - Test: Search FIR history → View details
    - Test: Export FIR to PDF
    - Test: Toggle dark mode
    - Test: Offline mode → Queue operation → Sync
    - _Requirements: 5.6.4_
  
  - [ ] 27.3 Run E2E tests
    - Run tests on Chrome, Firefox, Safari
    - Verify all tests pass
    - Fix any failures
    - _Requirements: 5.6.4_

- [ ] 28. Run final accessibility audit
  - [ ] 28.1 Run Lighthouse accessibility audit
    - Verify score >90
    - Fix any issues
    - _Requirements: 5.4.8_
  
  - [ ] 28.2 Run axe DevTools scan
    - Scan all pages
    - Fix any critical/serious issues
    - _Requirements: 5.4.8_
  
  - [ ] 28.3 Test with screen readers
    - Test with NVDA
    - Test with VoiceOver
    - Verify all content accessible
    - _Requirements: 5.4.4_
  
  - [ ] 28.4 Test keyboard navigation
    - Navigate entire app with keyboard only
    - Verify all features accessible
    - Verify focus indicators visible
    - _Requirements: 5.4.3_

- [ ] 29. Run final performance audit
  - [ ] 29.1 Run Lighthouse performance audit
    - Verify score >90
    - Verify FCP <1s, TTI <3s
    - Fix any issues
    - _Requirements: 5.1.4_
  
  - [ ] 29.2 Test on slow network
    - Test on 3G network
    - Verify page load <2s
    - Verify app usable
    - _Requirements: 5.1.1_
  
  - [ ] 29.3 Verify bundle sizes
    - Verify total <500KB gzipped
    - Verify no regressions
    - _Requirements: 5.1.5_

- [ ] 30. Create documentation
  - [ ] 30.1 Write README.md
    - Project overview
    - Setup instructions
    - Build instructions
    - Deployment instructions
    - _Requirements: 5.6.5_
  
  - [ ] 30.2 Write API documentation
    - Document all modules
    - Document all functions
    - Add JSDoc comments
    - _Requirements: 5.6.5_
  
  - [ ] 30.3 Write user guide
    - How to use the application
    - Feature descriptions
    - Troubleshooting
    - _Requirements: 5.6.5_

- [ ] 31. Final checkpoint - Production readiness
  - All tests passing (unit, property, E2E)
  - Lighthouse score >90 (all categories)
  - Bundle size <500KB gzipped
  - WCAG 2.1 AA compliance verified
  - Documentation complete
  - Code reviewed and approved
  - Ensure all tests pass, ask the user if questions arise.

### Phase 6: Deployment

- [ ] 32. Update Dockerfile
  - Update Dockerfile to copy dist/ instead of current files
  - Configure nginx to serve minified files
  - Add gzip compression in nginx
  - Test Docker build
  - _Requirements: 5.6.6_

- [ ] 33. Deploy to staging
  - Build production bundle
  - Deploy to staging environment
  - Run smoke tests
  - Verify all features work
  - _Requirements: 5.6.6_

- [ ] 34. Deploy to production
  - Build production bundle
  - Deploy to production environment
  - Monitor for errors
  - Verify all features work
  - Announce deployment
  - _Requirements: 5.6.6_

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation throughout implementation
- Property tests validate universal correctness properties
- Unit tests verify individual functions work correctly
- E2E tests validate complete user flows
- Accessibility tests ensure WCAG 2.1 AA compliance
- Performance tests ensure Lighthouse score >90
- Estimated timeline: 21-32 days (4-6 weeks) as per requirements document
