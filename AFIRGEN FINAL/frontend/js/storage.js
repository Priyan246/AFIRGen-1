/**
 * Storage Module
 * Provides unified interface for LocalStorage and IndexedDB operations
 * Supports TTL for LocalStorage and structured data storage in IndexedDB
 */

// IndexedDB configuration
const DB_NAME = 'AFIRGenDB';
const DB_VERSION = 1;
const STORES = {
  FIR_HISTORY: 'fir_history',
  CACHE: 'cache'
};

let dbInstance = null;

/**
 * Initialize IndexedDB
 * @returns {Promise<IDBDatabase>}
 */
async function initDB() {
  if (dbInstance) return dbInstance;

  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onerror = () => reject(request.error);
    request.onsuccess = () => {
      dbInstance = request.result;
      resolve(dbInstance);
    };

    request.onupgradeneeded = (event) => {
      const db = event.target.result;

      // Create FIR history store
      if (!db.objectStoreNames.contains(STORES.FIR_HISTORY)) {
        const firStore = db.createObjectStore(STORES.FIR_HISTORY, { keyPath: 'id' });
        firStore.createIndex('status', 'status', { unique: false });
        firStore.createIndex('date', 'date', { unique: false });
        firStore.createIndex('complainant', 'complainant', { unique: false });
      }

      // Create cache store
      if (!db.objectStoreNames.contains(STORES.CACHE)) {
        db.createObjectStore(STORES.CACHE, { keyPath: 'key' });
      }
    };
  });
}

/**
 * Set item in LocalStorage with optional TTL
 * @param {string} key - Storage key
 * @param {*} value - Value to store (will be JSON stringified)
 * @param {number} [ttl] - Time to live in milliseconds
 */
function setLocal(key, value, ttl = null) {
  try {
    const item = {
      value,
      timestamp: Date.now(),
      ttl
    };
    localStorage.setItem(key, JSON.stringify(item));
  } catch (error) {
    console.error('Error setting LocalStorage item:', error);
    throw error;
  }
}

/**
 * Get item from LocalStorage
 * @param {string} key - Storage key
 * @returns {*} Stored value or null if not found/expired
 */
function getLocal(key) {
  try {
    const itemStr = localStorage.getItem(key);
    if (!itemStr) return null;

    const item = JSON.parse(itemStr);
    
    // Check if item has expired
    if (item.ttl && Date.now() - item.timestamp > item.ttl) {
      localStorage.removeItem(key);
      return null;
    }

    return item.value;
  } catch (error) {
    console.error('Error getting LocalStorage item:', error);
    return null;
  }
}

/**
 * Remove item from LocalStorage
 * @param {string} key - Storage key
 */
function removeLocal(key) {
  try {
    localStorage.removeItem(key);
  } catch (error) {
    console.error('Error removing LocalStorage item:', error);
  }
}

/**
 * Clear all items from LocalStorage
 */
function clearLocal() {
  try {
    localStorage.clear();
  } catch (error) {
    console.error('Error clearing LocalStorage:', error);
  }
}

/**
 * Set item in IndexedDB
 * @param {string} storeName - Object store name
 * @param {string} key - Item key (or full object with keyPath)
 * @param {*} value - Value to store
 * @returns {Promise<void>}
 */
async function setDB(storeName, key, value) {
  try {
    const db = await initDB();
    
    return new Promise((resolve, reject) => {
      const transaction = db.transaction([storeName], 'readwrite');
      const store = transaction.objectStore(storeName);
      
      // If value is an object with the keyPath, use it directly
      // Otherwise, create an object with the key
      const item = typeof value === 'object' && value !== null && 'id' in value
        ? value
        : { id: key, data: value };
      
      const request = store.put(item);
      
      request.onsuccess = () => resolve();
      request.onerror = () => {
        // Check for quota exceeded error
        if (request.error && request.error.name === 'QuotaExceededError') {
          console.error('IndexedDB quota exceeded');
          if (typeof window !== 'undefined' && window.showToast) {
            window.showToast('Storage quota exceeded. Please clear old data.', 'error', 10000);
          }
        }
        reject(request.error);
      };
    });
  } catch (error) {
    console.error('Error setting IndexedDB item:', error);
    // Check for quota exceeded error
    if (error.name === 'QuotaExceededError') {
      if (typeof window !== 'undefined' && window.showToast) {
        window.showToast('Storage quota exceeded. Please clear old data.', 'error', 10000);
      }
    }
    throw error;
  }
}

/**
 * Get item from IndexedDB
 * @param {string} storeName - Object store name
 * @param {string} key - Item key
 * @returns {Promise<*>} Stored value or null if not found
 */
async function getDB(storeName, key) {
  try {
    const db = await initDB();
    
    return new Promise((resolve, reject) => {
      const transaction = db.transaction([storeName], 'readonly');
      const store = transaction.objectStore(storeName);
      const request = store.get(key);
      
      request.onsuccess = () => resolve(request.result || null);
      request.onerror = () => reject(request.error);
    });
  } catch (error) {
    console.error('Error getting IndexedDB item:', error);
    return null;
  }
}

/**
 * Get all items from IndexedDB store
 * @param {string} storeName - Object store name
 * @returns {Promise<Array>} Array of all items in the store
 */
async function getAllDB(storeName) {
  try {
    const db = await initDB();
    
    return new Promise((resolve, reject) => {
      const transaction = db.transaction([storeName], 'readonly');
      const store = transaction.objectStore(storeName);
      const request = store.getAll();
      
      request.onsuccess = () => resolve(request.result || []);
      request.onerror = () => reject(request.error);
    });
  } catch (error) {
    console.error('Error getting all IndexedDB items:', error);
    return [];
  }
}

/**
 * Delete item from IndexedDB
 * @param {string} storeName - Object store name
 * @param {string} key - Item key
 * @returns {Promise<void>}
 */
async function deleteDB(storeName, key) {
  try {
    const db = await initDB();
    
    return new Promise((resolve, reject) => {
      const transaction = db.transaction([storeName], 'readwrite');
      const store = transaction.objectStore(storeName);
      const request = store.delete(key);
      
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  } catch (error) {
    console.error('Error deleting IndexedDB item:', error);
    throw error;
  }
}

/**
 * Clear all items from IndexedDB store
 * @param {string} storeName - Object store name
 * @returns {Promise<void>}
 */
async function clearDB(storeName) {
  try {
    const db = await initDB();
    
    return new Promise((resolve, reject) => {
      const transaction = db.transaction([storeName], 'readwrite');
      const store = transaction.objectStore(storeName);
      const request = store.clear();
      
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  } catch (error) {
    console.error('Error clearing IndexedDB store:', error);
    throw error;
  }
}

/**
 * Query IndexedDB by index
 * @param {string} storeName - Object store name
 * @param {string} indexName - Index name
 * @param {*} value - Value to query
 * @returns {Promise<Array>} Array of matching items
 */
async function queryDB(storeName, indexName, value) {
  try {
    const db = await initDB();
    
    return new Promise((resolve, reject) => {
      const transaction = db.transaction([storeName], 'readonly');
      const store = transaction.objectStore(storeName);
      const index = store.index(indexName);
      const request = index.getAll(value);
      
      request.onsuccess = () => resolve(request.result || []);
      request.onerror = () => reject(request.error);
    });
  } catch (error) {
    console.error('Error querying IndexedDB:', error);
    return [];
  }
}

// Export functions
export {
  // LocalStorage
  setLocal,
  getLocal,
  removeLocal,
  clearLocal,
  
  // IndexedDB
  initDB,
  setDB,
  getDB,
  getAllDB,
  deleteDB,
  clearDB,
  queryDB,
  
  // Constants
  STORES
};


// Make functions available globally for non-module scripts
if (typeof window !== 'undefined') {
    window.Storage = {
        setLocal,
        getLocal,
        removeLocal,
        clearLocal,
        initDB,
        setDB,
        getDB,
        getAllDB,
        deleteDB,
        clearDB,
        queryDB,
        STORES
    };
}
