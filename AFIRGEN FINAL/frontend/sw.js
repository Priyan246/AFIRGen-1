// Service Worker for AFIRGen Frontend
// Provides offline capability and caching

const CACHE_VERSION = 'v1.0.0';
const CACHE_NAME = `afirgen-${CACHE_VERSION}`;
const CACHE_NAME_DYNAMIC = `afirgen-dynamic-${CACHE_VERSION}`;

// Assets to cache on install
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/offline.html',
  '/css/main.css',
  '/css/themes.css',
  '/js/app.js',
  '/js/api.js',
  '/js/validation.js',
  '/js/security.js',
  '/js/ui.js',
  '/js/keyboard-navigation.js',
  '/js/config.js',
  '/lib/dompurify.min.js',
];

// API endpoints that should use network-first strategy
const API_ENDPOINTS = [
  '/process',
  '/validate',
  '/regenerate',
  '/session',
  '/fir',
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('[Service Worker] Installing...');
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[Service Worker] Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        console.log('[Service Worker] Installation complete');
        return self.skipWaiting(); // Activate immediately
      })
      .catch((error) => {
        console.error('[Service Worker] Installation failed:', error);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[Service Worker] Activating...');
  
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter((cacheName) => {
              // Delete old versions of caches
              return cacheName.startsWith('afirgen-') && 
                     cacheName !== CACHE_NAME && 
                     cacheName !== CACHE_NAME_DYNAMIC;
            })
            .map((cacheName) => {
              console.log('[Service Worker] Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            })
        );
      })
      .then(() => {
        console.log('[Service Worker] Activation complete');
        return self.clients.claim(); // Take control immediately
      })
  );
});

// Fetch event - implement caching strategies
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }
  
  // Determine caching strategy based on request type
  if (isAPIRequest(url)) {
    // Network-first for API requests
    event.respondWith(networkFirstStrategy(request));
  } else if (isStaticAsset(url)) {
    // Cache-first for static assets
    event.respondWith(cacheFirstStrategy(request));
  } else {
    // Network-first with cache fallback for HTML
    event.respondWith(networkFirstStrategy(request));
  }
});

// Check if request is to API endpoint
function isAPIRequest(url) {
  return API_ENDPOINTS.some(endpoint => url.pathname.includes(endpoint));
}

// Check if request is for static asset
function isStaticAsset(url) {
  const staticExtensions = ['.css', '.js', '.png', '.jpg', '.jpeg', '.svg', '.woff', '.woff2'];
  return staticExtensions.some(ext => url.pathname.endsWith(ext));
}

// Cache-first strategy: Try cache first, then network
async function cacheFirstStrategy(request) {
  try {
    const cachedResponse = await caches.match(request);
    
    if (cachedResponse) {
      console.log('[Service Worker] Serving from cache:', request.url);
      return cachedResponse;
    }
    
    console.log('[Service Worker] Fetching from network:', request.url);
    const networkResponse = await fetch(request);
    
    // Cache successful responses
    if (networkResponse && networkResponse.status === 200) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.error('[Service Worker] Cache-first strategy failed:', error);
    
    // Return offline page if available
    const offlineResponse = await caches.match('/offline.html');
    if (offlineResponse) {
      return offlineResponse;
    }
    
    // Return basic offline response
    return new Response('Offline - Content not available', {
      status: 503,
      statusText: 'Service Unavailable',
      headers: new Headers({
        'Content-Type': 'text/plain',
      }),
    });
  }
}

// Network-first strategy: Try network first, then cache
async function networkFirstStrategy(request) {
  try {
    console.log('[Service Worker] Fetching from network:', request.url);
    const networkResponse = await fetch(request);
    
    // Cache successful responses (with TTL for API responses)
    if (networkResponse && networkResponse.status === 200) {
      const cache = await caches.open(CACHE_NAME_DYNAMIC);
      
      // Clone response and add timestamp for TTL
      const responseToCache = networkResponse.clone();
      cache.put(request, responseToCache);
      
      // Clean up old dynamic cache entries (keep last 50)
      cleanupDynamicCache();
    }
    
    return networkResponse;
  } catch (error) {
    console.log('[Service Worker] Network failed, trying cache:', request.url);
    
    // Try cache as fallback
    const cachedResponse = await caches.match(request);
    
    if (cachedResponse) {
      console.log('[Service Worker] Serving from cache (fallback):', request.url);
      return cachedResponse;
    }
    
    // Return offline page for HTML requests
    if (request.headers.get('accept').includes('text/html')) {
      const offlineResponse = await caches.match('/offline.html');
      if (offlineResponse) {
        return offlineResponse;
      }
    }
    
    // Return error response
    return new Response('Offline - Content not available', {
      status: 503,
      statusText: 'Service Unavailable',
      headers: new Headers({
        'Content-Type': 'text/plain',
      }),
    });
  }
}

// Clean up old dynamic cache entries
async function cleanupDynamicCache() {
  const cache = await caches.open(CACHE_NAME_DYNAMIC);
  const keys = await cache.keys();
  
  // Keep only the last 50 entries
  if (keys.length > 50) {
    const keysToDelete = keys.slice(0, keys.length - 50);
    await Promise.all(keysToDelete.map(key => cache.delete(key)));
    console.log('[Service Worker] Cleaned up', keysToDelete.length, 'old cache entries');
  }
}

// Message event - handle messages from clients
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'CLEAR_CACHE') {
    event.waitUntil(
      caches.keys().then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => caches.delete(cacheName))
        );
      })
    );
  }
});

// Background sync event (for future implementation)
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-fir-data') {
    event.waitUntil(syncFIRData());
  }
});

// Sync FIR data when back online (placeholder for future implementation)
async function syncFIRData() {
  console.log('[Service Worker] Syncing FIR data...');
  // TODO: Implement sync logic when storage module is ready
}
