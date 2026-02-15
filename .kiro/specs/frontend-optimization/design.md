# AFIRGen Frontend Optimization - Design Document

## 1. Overview

This design document outlines the architecture, components, and implementation strategy for optimizing the AFIRGen frontend application. The frontend is a static HTML/CSS/JS application that provides the user interface for the FIR generation system.

### 1.1 Current State Assessment

**Existing Features:**
- ✅ File upload (letter/image and audio)
- ✅ FIR generation workflow with validation
- ✅ Session status polling
- ✅ Tab navigation (Home, About, Resources)
- ✅ Basic search functionality
- ✅ Modal displays for results
- ✅ Environment configuration (config.js)
- ✅ API integration with backend

**Identified Issues:**
- ⚠️ No loading states or progress indicators
- ⚠️ No request caching or retry logic
- ⚠️ Large bundle size (not minified)
- ⚠️ Poor error handling (generic alerts)
- ⚠️ No toast notifications
- ⚠️ No drag-and-drop file upload
- ⚠️ Missing ARIA labels and accessibility features
- ⚠️ No client-side input sanitization
- ⚠️ No file validation before upload
- ⚠️ API key visible in config.js
- ⚠️ No FIR history/list view
- ⚠️ No PDF export or print functionality
- ⚠️ No dark mode
- ⚠️ No offline mode or PWA features

### 1.2 Design Goals

1. **Performance**: Page load <2s, TTI <3s, Lighthouse score >90
2. **User Experience**: Loading states, toast notifications, drag-and-drop, real-time validation
3. **Security**: Input sanitization, file validation, API key protection, CSP
4. **Accessibility**: WCAG 2.1 AA compliance, keyboard navigation, screen reader support
5. **Features**: FIR history, PDF export, dark mode, offline mode
6. **Code Quality**: Minified bundles, ESLint, unit tests, documentation

## 2. Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Browser                                 │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Service Worker                            │  │
│  │  - Offline caching                                     │  │
│  │  - Background sync                                     │  │
│  │  - Push notifications                                  │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Frontend Application                      │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐  │  │
│  │  │   UI Layer  │  │ State Mgmt  │  │  API Client  │  │  │
│  │  │  - HTML     │  │ - Session   │  │  - Fetch     │  │  │
│  │  │  - CSS      │  │ - FIR Data  │  │  - Retry     │  │  │
│  │  │  - JS       │  │ - UI State  │  │  - Cache     │  │  │
│  │  └─────────────┘  └─────────────┘  └──────────────┘  │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐  │  │
│  │  │ Validation  │  │  Security   │  │  Storage     │  │  │
│  │  │ - Input     │  │  - Sanitize │  │  - LocalStor │  │  │
│  │  │ - File      │  │  - CSP      │  │  - IndexedDB │  │  │
│  │  └─────────────┘  └─────────────┘  └──────────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   AFIRGen Backend API                        │
│  - /process, /validate, /regenerate, /session, /fir         │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Module Structure

```
frontend/
├── index.html              # Main HTML (renamed from base.html)
├── manifest.json           # PWA manifest
├── sw.js                   # Service worker
├── css/
│   ├── main.css           # Core styles
│   ├── themes.css         # Dark/light themes
│   └── print.css          # Print styles
├── js/
│   ├── app.js             # Main application logic
│   ├── api.js             # API client with retry/cache
│   ├── state.js           # State management
│   ├── validation.js      # Input/file validation
│   ├── security.js        # Sanitization utilities
│   ├── ui.js              # UI helpers (toast, loading)
│   ├── storage.js         # LocalStorage/IndexedDB wrapper
│   ├── pdf.js             # PDF export functionality
│   └── config.js          # Environment configuration
├── lib/
│   ├── dompurify.min.js   # HTML sanitization
│   └── jspdf.min.js       # PDF generation
└── assets/
    ├── icons/             # PWA icons
    └── fonts/             # Local fonts
```

## 3. Components and Interfaces

### 3.1 API Client Module (api.js)

**Purpose:** Handle all HTTP requests with retry logic, caching, and error handling

**Interface:**
```javascript
class APIClient {
  constructor(baseURL, apiKey)
  
  // Core methods
  async request(endpoint, options)
  async get(endpoint, params)
  async post(endpoint, body, isFormData)
  
  // Retry logic
  async retryRequest(fn, maxRetries, backoff)
  
  // Caching
  getCached(key)
  setCached(key, data, ttl)
  clearCache()
}
```

**Features:**
- Exponential backoff retry (3 attempts, 1s/2s/4s delays)
- Response caching with TTL (5 minutes default)
- Automatic error handling and logging
- Request timeout (30s default)
- CORS handling

### 3.2 Validation Module (validation.js)

**Purpose:** Client-side input and file validation

**Interface:**
```javascript
// File validation
function validateFile(file, options)
function validateFileType(file, allowedTypes)
function validateFileSize(file, maxSize)
function validateMimeType(file)

// Input validation
function validateText(text, options)
function sanitizeInput(input)
function validateForm(formData)
```

**Validation Rules:**
- File types: .jpg, .jpeg, .png, .pdf, .wav, .mp3 (whitelist)
- Max file size: 10MB
- MIME type validation (magic number check)
- Text input: XSS prevention, length limits
- Form validation: Required fields, format checks

### 3.3 Security Module (security.js)

**Purpose:** Client-side security measures

**Interface:**
```javascript
// Sanitization
function sanitizeHTML(html)
function sanitizeText(text)
function escapeHTML(str)

// CSP
function enforceCSP()
function reportCSPViolation(violation)

// API key protection
function getAPIKey()  // From secure storage, not exposed
```

**Features:**
- DOMPurify integration for HTML sanitization
- XSS prevention
- Content Security Policy enforcement
- API key stored in secure cookie (HttpOnly, Secure, SameSite)

### 3.4 UI Module (ui.js)

**Purpose:** UI helpers for loading states, toasts, modals

**Interface:**
```javascript
// Toast notifications
function showToast(message, type, duration)
function hideToast(toastId)

// Loading states
function showLoading(element, message)
function hideLoading(element)
function showProgress(element, percentage)

// Modals
function showModal(title, content, actions)
function hideModal(modalId)

// Skeleton screens
function showSkeleton(element)
function hideSkeleton(element)
```

**Toast Types:**
- success (green)
- error (red)
- warning (yellow)
- info (blue)

### 3.5 Storage Module (storage.js)

**Purpose:** Wrapper for LocalStorage and IndexedDB

**Interface:**
```javascript
// LocalStorage (for small data)
function setLocal(key, value, ttl)
function getLocal(key)
function removeLocal(key)

// IndexedDB (for large data, offline mode)
function setDB(store, key, value)
function getDB(store, key)
function getAllDB(store)
function deleteDB(store, key)
```

**Storage Strategy:**
- LocalStorage: User preferences, session data, small cache
- IndexedDB: FIR history, offline queue, large cache

### 3.6 PDF Export Module (pdf.js)

**Purpose:** Generate PDF from FIR data

**Interface:**
```javascript
function generatePDF(firData, options)
function downloadPDF(pdf, filename)
function printPDF(pdf)
```

**Features:**
- Professional formatting
- Include all FIR fields
- Header/footer with metadata
- Page numbers
- Watermark (optional)

## 4. Correctness Properties

### Property 1: File Validation Before Upload
*For any* file selected by the user, the system SHALL validate file type, size, and MIME type before allowing upload, rejecting invalid files with descriptive error messages.

**Validates: Requirements 5.3.2, 5.3.3**

**Test Strategy:** Generate random files with various types, sizes, and MIME types, verify only valid files pass validation.

### Property 2: Input Sanitization
*For any* user input (text fields, search, validation input), the system SHALL sanitize the input to prevent XSS attacks before rendering or sending to backend.

**Validates: Requirements 5.3.1**

**Test Strategy:** Generate various XSS payloads, verify all are sanitized and rendered safely.

### Property 3: API Request Retry
*For any* failed API request due to network error or 5xx response, the system SHALL retry the request up to 3 times with exponential backoff before showing error to user.

**Validates: Requirements 5.1.7**

**Test Strategy:** Simulate network failures and 5xx responses, verify retry logic executes correctly.

### Property 4: Loading State Visibility
*For any* asynchronous operation (API call, file upload, processing), the system SHALL display a loading indicator within 100ms of operation start and hide it within 100ms of completion.

**Validates: Requirements 5.2.1**

**Test Strategy:** Measure time between operation start and loading indicator display, verify <100ms.

### Property 5: Keyboard Navigation
*For any* interactive element (button, input, link), the system SHALL be accessible via keyboard (Tab, Enter, Space, Escape) with visible focus indicators.

**Validates: Requirements 5.4.3**

**Test Strategy:** Navigate entire application using only keyboard, verify all features accessible.

### Property 6: Offline Mode Functionality
*For any* cached FIR or session data, the system SHALL allow viewing and basic operations when offline, queuing write operations for sync when online.

**Validates: Requirements 5.5.6**

**Test Strategy:** Load application, go offline, verify cached data accessible and operations queued.

### Property 7: Dark Mode Consistency
*For any* UI element, when dark mode is enabled, the system SHALL apply dark theme colors with contrast ratio >4.5:1 for text and >3:1 for UI components.

**Validates: Requirements 5.4.7**

**Test Strategy:** Enable dark mode, measure contrast ratios for all text and UI elements.

### Property 8: Toast Notification Display
*For any* user action that completes (success or error), the system SHALL display a toast notification with appropriate message and type within 200ms.

**Validates: Requirements 5.2.3**

**Test Strategy:** Trigger various actions, verify toast appears within 200ms with correct message.

### Property 9: Form Validation Feedback
*For any* form field with validation rules, the system SHALL provide real-time validation feedback (inline error message) within 300ms of user input.

**Validates: Requirements 5.2.5**

**Test Strategy:** Enter invalid data in form fields, measure time to error message display.

### Property 10: PDF Export Completeness
*For any* FIR data exported to PDF, the generated PDF SHALL contain all FIR fields, be properly formatted, and be downloadable without errors.

**Validates: Requirements 5.5.2**

**Test Strategy:** Generate PDFs from various FIR data, verify all fields present and formatting correct.

## 5. Error Handling

### 5.1 Error Categories

#### 5.1.1 Network Errors
- Connection timeout
- Network unavailable
- DNS resolution failure

**Handling:**
- Retry with exponential backoff (3 attempts)
- Show toast: "Network error. Retrying..."
- If all retries fail: "Unable to connect. Please check your internet connection."
- Queue operation for offline sync if applicable

#### 5.1.2 API Errors
- 400 Bad Request: Invalid input
- 401 Unauthorized: Invalid API key
- 403 Forbidden: Access denied
- 404 Not Found: Resource not found
- 429 Too Many Requests: Rate limit exceeded
- 500 Internal Server Error: Backend error

**Handling:**
- 400: Show specific validation errors from response
- 401: Redirect to login or show "Authentication failed"
- 403: Show "Access denied. Please contact support."
- 404: Show "Resource not found"
- 429: Show "Too many requests. Please wait and try again."
- 500: Retry once, then show "Server error. Please try again later."

#### 5.1.3 Validation Errors
- Invalid file type
- File too large
- Invalid input format
- Required field missing

**Handling:**
- Show inline error message below field
- Highlight field in red
- Disable submit button until fixed
- Provide helpful error message with correction guidance

#### 5.1.4 Client Errors
- JavaScript error
- Out of memory
- Storage quota exceeded

**Handling:**
- Log error to console
- Show generic error message to user
- Attempt to recover gracefully
- Provide "Reload page" button

### 5.2 Error Recovery

**Automatic Recovery:**
- Network errors: Retry with backoff
- Transient API errors (5xx): Retry once
- Storage quota: Clear old cache data

**Manual Recovery:**
- Persistent errors: Show "Reload page" button
- Data loss: Restore from LocalStorage backup
- Corrupted state: Clear state and restart

## 6. Performance Optimizations

### 6.1 Bundle Optimization

**Minification:**
- HTML: Remove whitespace, comments
- CSS: Minify with cssnano
- JavaScript: Minify with terser

**Code Splitting:**
- Lazy load PDF export module (only when needed)
- Lazy load dark mode CSS (only when enabled)
- Separate vendor bundles (DOMPurify, jsPDF)

**Target Bundle Sizes:**
- main.css: <50KB (gzipped)
- app.js: <100KB (gzipped)
- vendor.js: <150KB (gzipped)
- Total: <300KB (gzipped)

### 6.2 Asset Optimization

**Images:**
- Convert to WebP format
- Lazy load images below fold
- Use responsive images (srcset)
- Compress with quality 85

**Fonts:**
- Use system fonts where possible
- Subset custom fonts (only needed characters)
- Preload critical fonts
- Use font-display: swap

### 6.3 Caching Strategy

**Service Worker Cache:**
- Static assets: Cache-first (1 year)
- API responses: Network-first with cache fallback (5 minutes)
- HTML: Network-first with cache fallback

**HTTP Caching:**
- Static assets: Cache-Control: public, max-age=31536000, immutable
- API responses: Cache-Control: private, max-age=300
- HTML: Cache-Control: no-cache

### 6.4 Network Optimization

**Resource Hints:**
- Preconnect to API domain
- DNS-prefetch for CDN
- Prefetch critical resources

**Request Optimization:**
- Batch multiple API calls where possible
- Use HTTP/2 multiplexing
- Compress requests with gzip

## 7. Accessibility Features

### 7.1 ARIA Implementation

**Landmarks:**
- `<nav role="navigation">`
- `<main role="main">`
- `<aside role="complementary">` (sidebar)

**Labels:**
- All buttons: `aria-label`
- All inputs: `aria-labelledby` or `aria-label`
- All icons: `aria-hidden="true"` (decorative)

**Live Regions:**
- Toast notifications: `aria-live="polite"`
- Status messages: `aria-live="assertive"`
- Loading states: `aria-busy="true"`

**States:**
- Modals: `aria-modal="true"`, `aria-hidden`
- Expandable: `aria-expanded`
- Selected: `aria-selected`
- Disabled: `aria-disabled`

### 7.2 Keyboard Navigation

**Tab Order:**
- Logical flow: Top to bottom, left to right
- Skip links: "Skip to main content"
- Focus trap in modals

**Keyboard Shortcuts:**
- Tab: Next element
- Shift+Tab: Previous element
- Enter/Space: Activate button
- Escape: Close modal/dropdown
- Arrow keys: Navigate lists

**Focus Management:**
- Visible focus indicators (2px outline)
- Focus returns to trigger after modal close
- Focus moves to first element in modal on open

### 7.3 Screen Reader Support

**Semantic HTML:**
- Use `<button>` for buttons (not `<div>`)
- Use `<input>` for inputs (not custom elements)
- Use `<nav>`, `<main>`, `<aside>` for structure

**Alt Text:**
- All images: Descriptive alt text
- Decorative images: `alt=""`
- Icons: `aria-label` on parent

**Announcements:**
- Status changes: Announced via `aria-live`
- Errors: Announced immediately
- Success: Announced after completion

## 8. Security Measures

### 8.1 Content Security Policy

```
Content-Security-Policy:
  default-src 'self';
  script-src 'self' 'unsafe-inline';
  style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
  font-src 'self' https://fonts.gstatic.com;
  connect-src 'self' https://api.afirgen.example.com;
  img-src 'self' data: blob:;
  frame-ancestors 'none';
  base-uri 'self';
  form-action 'self';
```

### 8.2 API Key Protection

**Current Issue:** API key visible in config.js

**Solution:**
1. Move API key to secure HttpOnly cookie set by backend
2. Backend sets cookie on initial page load
3. Frontend reads cookie automatically (not accessible to JS)
4. Cookie attributes: HttpOnly, Secure, SameSite=Strict

**Alternative:** Use backend proxy for API calls (no client-side key)

### 8.3 Input Sanitization

**DOMPurify Configuration:**
```javascript
DOMPurify.sanitize(html, {
  ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'p', 'br'],
  ALLOWED_ATTR: [],
  KEEP_CONTENT: true
});
```

**Text Sanitization:**
- Escape HTML entities: `<`, `>`, `&`, `"`, `'`
- Remove control characters
- Limit length (prevent DoS)

## 9. New Features

### 9.1 FIR History

**UI:**
- List view in sidebar (replace static list)
- Search by FIR number, complainant, date
- Filter by status (pending, investigating, closed)
- Sort by date (newest first)
- Pagination (20 per page)

**Data:**
- Fetch from backend: `GET /fir/list`
- Cache in IndexedDB for offline access
- Refresh on page load and after new FIR

**Interaction:**
- Click FIR item: Show details in modal
- Search: Filter list in real-time
- Infinite scroll or "Load more" button

### 9.2 PDF Export

**Trigger:** "Export PDF" button in FIR modal

**Implementation:**
- Use jsPDF library
- Format: A4 portrait
- Include: All FIR fields, header, footer, page numbers
- Download: `fir_${firNumber}_${date}.pdf`

**Styling:**
- Professional layout
- Monospace font for FIR content
- Header: FIR number, date
- Footer: Page number, generated timestamp

### 9.3 Dark Mode

**Toggle:** Button in navbar

**Implementation:**
- CSS custom properties for colors
- Toggle class on `<body>`: `dark-mode`
- Persist preference in LocalStorage
- Smooth transition (0.3s)

**Colors:**
- Background: #000000 → #0a0a0a
- Text: #ffffff → #e5e5e5
- Borders: #4b4b4b → #2a2a2a
- Accents: Adjust for contrast

### 9.4 PWA Features

**Manifest:**
- Name: "AFIRGen"
- Short name: "AFIRGen"
- Icons: 192x192, 512x512
- Start URL: "/"
- Display: standalone
- Theme color: #000000

**Service Worker:**
- Cache static assets
- Cache API responses
- Offline fallback page
- Background sync for queued operations

**Installation:**
- Show install prompt on second visit
- "Add to Home Screen" button in navbar

## 10. Testing Strategy

### 10.1 Unit Tests

**Framework:** Jest

**Coverage Target:** >80%

**Test Files:**
- `api.test.js`: API client, retry logic, caching
- `validation.test.js`: File validation, input validation
- `security.test.js`: Sanitization, XSS prevention
- `storage.test.js`: LocalStorage, IndexedDB operations
- `ui.test.js`: Toast, loading states, modals

### 10.2 Property-Based Tests

**Framework:** fast-check (JavaScript PBT library)

**Properties:** See section 4 (10 properties)

### 10.3 E2E Tests

**Framework:** Playwright

**Critical Flows:**
1. Upload file → Generate FIR → Validate → Complete
2. Search FIR history → View details
3. Export FIR to PDF
4. Toggle dark mode
5. Offline mode → Queue operation → Sync when online

### 10.4 Accessibility Tests

**Tools:**
- Lighthouse accessibility audit (score >90)
- axe DevTools
- NVDA screen reader testing
- Keyboard-only navigation testing

### 10.5 Performance Tests

**Tools:**
- Lighthouse performance audit (score >90)
- WebPageTest
- Chrome DevTools Performance panel

**Metrics:**
- First Contentful Paint (FCP): <1s
- Time to Interactive (TTI): <3s
- Total Blocking Time (TBT): <300ms
- Cumulative Layout Shift (CLS): <0.1

## 11. Build Process

### 11.1 Development Build

**Tools:**
- No build step (vanilla JS)
- Live server for development
- Source maps enabled

**Commands:**
```bash
npm run dev    # Start live server
npm run test   # Run unit tests
npm run lint   # Run ESLint
```

### 11.2 Production Build

**Tools:**
- Terser for JS minification
- cssnano for CSS minification
- html-minifier for HTML minification

**Commands:**
```bash
npm run build       # Build production bundle
npm run build:css   # Minify CSS
npm run build:js    # Minify JS
npm run build:html  # Minify HTML
```

**Output:**
```
dist/
├── index.html (minified)
├── manifest.json
├── sw.js (minified)
├── css/
│   └── main.min.css
├── js/
│   ├── app.min.js
│   └── vendor.min.js
└── assets/
```

### 11.3 Quality Checks

**Pre-commit:**
- ESLint (no errors)
- Prettier (format code)
- Unit tests (all passing)

**Pre-deploy:**
- All tests passing
- Lighthouse score >90 (all categories)
- Bundle size <500KB (gzipped)
- No console errors

## 12. Deployment

### 12.1 Docker Build

**Dockerfile:**
```dockerfile
FROM nginx:alpine
COPY dist/ /usr/share/nginx/html/
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### 12.2 Environment Configuration

**config.js:**
```javascript
window.ENV = {
  API_BASE_URL: process.env.API_BASE_URL || 'http://localhost:8000',
  ENVIRONMENT: process.env.ENVIRONMENT || 'development'
};
```

**Inject at build time:**
```bash
envsubst < config.js.template > config.js
```

## 13. Migration Plan

### 13.1 Phase 1: Core Improvements (P0)
- Loading states
- Error handling with toasts
- Input sanitization
- File validation
- Basic accessibility (ARIA, keyboard nav)

### 13.2 Phase 2: Performance (P1)
- Minification and bundling
- Caching strategy
- Service worker
- Asset optimization

### 13.3 Phase 3: Features (P1)
- FIR history
- Dark mode
- Drag-and-drop upload

### 13.4 Phase 4: Advanced Features (P2)
- PDF export
- Offline mode
- PWA features
- Advanced accessibility

### 13.5 Phase 5: Polish (P2)
- Animations and transitions
- Advanced error recovery
- Performance monitoring

### 13.6 Phase 6: Visual Effects & Animations (P2)
- Particle effects on page load
- Animated gradient backgrounds with flow effects
- Glassmorphism effects on cards and modals
- Parallax scrolling effects
- Hover animations with scale and glow effects
- Text reveal animations on scroll
- Floating elements with subtle motion
- Ripple effects on button clicks
- Animated icons and SVG illustrations
- Cursor trail effects
- Page transition animations with fade/slide
- Loading animations with custom spinners
- Success/error animations with confetti or shake effects
- Smooth morphing transitions between states
- 3D card flip effects for FIR items

## 14. Success Metrics

**Performance:**
- Lighthouse score >90 (all categories)
- Page load time <2s on 3G
- Bundle size <500KB (gzipped)

**Accessibility:**
- WCAG 2.1 AA compliance
- Lighthouse accessibility score >90
- Keyboard navigation 100% functional

**User Experience:**
- Error rate <1%
- Toast notifications for all actions
- Loading states for all async operations

**Code Quality:**
- Unit test coverage >80%
- All property tests passing
- ESLint passing with no errors
- Documentation complete

## 15. Future Enhancements

**P3 (Future):**
- Multi-language support (i18n)
- Advanced analytics
- Push notifications
- Real-time updates (WebSocket)
- Voice input for complaints
- Mobile native apps (React Native)
- Collaborative editing
- Advanced search with filters
- Data visualization (charts, graphs)
