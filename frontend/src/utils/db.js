/**
 * IndexedDB helper for offline data persistence
 */

const DB_NAME = 'clawbook';
const DB_VERSION = 1;

let db = null;

/**
 * Initialize IndexedDB
 */
export async function initDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onerror = () => {
      console.error('Failed to open IndexedDB:', request.error);
      reject(request.error);
    };

    request.onsuccess = () => {
      db = request.result;
      console.log('IndexedDB initialized');
      resolve(db);
    };

    request.onupgradeneeded = (event) => {
      const upgradeDB = event.target.result;

      // Create object stores
      if (!upgradeDB.objectStoreNames.contains('posts')) {
        upgradeDB.createObjectStore('posts', { keyPath: 'id' });
      }

      if (!upgradeDB.objectStoreNames.contains('pending-posts')) {
        upgradeDB.createObjectStore('pending-posts', { keyPath: 'id', autoIncrement: true });
      }

      if (!upgradeDB.objectStoreNames.contains('sync-queue')) {
        upgradeDB.createObjectStore('sync-queue', { keyPath: 'id', autoIncrement: true });
      }

      console.log('IndexedDB upgraded with new stores');
    };
  });
}

/**
 * Save posts to offline storage
 */
export async function savePosts(posts) {
  if (!db) await initDB();

  return new Promise((resolve, reject) => {
    const tx = db.transaction('posts', 'readwrite');
    const store = tx.objectStore('posts');

    // Clear existing posts
    store.clear();

    // Add new posts
    posts.forEach((post) => {
      store.put({
        ...post,
        savedAt: new Date().toISOString(),
      });
    });

    tx.oncomplete = () => {
      console.log(`Saved ${posts.length} posts to IndexedDB`);
      resolve();
    };

    tx.onerror = () => {
      console.error('Failed to save posts:', tx.error);
      reject(tx.error);
    };
  });
}

/**
 * Get offline posts
 */
export async function getOfflinePosts() {
  if (!db) await initDB();

  return new Promise((resolve, reject) => {
    const tx = db.transaction('posts', 'readonly');
    const store = tx.objectStore('posts');
    const request = store.getAll();

    request.onsuccess = () => {
      resolve(request.result || []);
    };

    request.onerror = () => {
      console.error('Failed to get offline posts:', request.error);
      reject(request.error);
    };
  });
}

/**
 * Add post to pending sync queue
 */
export async function addPendingPost(postData) {
  if (!db) await initDB();

  return new Promise((resolve, reject) => {
    const tx = db.transaction('pending-posts', 'readwrite');
    const store = tx.objectStore('pending-posts');

    const request = store.add({
      data: postData,
      createdAt: new Date().toISOString(),
      status: 'pending',
    });

    request.onsuccess = () => {
      console.log('Post added to pending queue:', request.result);
      resolve(request.result);
    };

    request.onerror = () => {
      console.error('Failed to add pending post:', request.error);
      reject(request.error);
    };
  });
}

/**
 * Get pending posts
 */
export async function getPendingPosts() {
  if (!db) await initDB();

  return new Promise((resolve, reject) => {
    const tx = db.transaction('pending-posts', 'readonly');
    const store = tx.objectStore('pending-posts');
    const request = store.getAll();

    request.onsuccess = () => {
      resolve(request.result || []);
    };

    request.onerror = () => {
      console.error('Failed to get pending posts:', request.error);
      reject(request.error);
    };
  });
}

/**
 * Remove pending post after sync
 */
export async function removePendingPost(id) {
  if (!db) await initDB();

  return new Promise((resolve, reject) => {
    const tx = db.transaction('pending-posts', 'readwrite');
    const store = tx.objectStore('pending-posts');
    const request = store.delete(id);

    request.onsuccess = () => {
      console.log('Pending post removed:', id);
      resolve();
    };

    request.onerror = () => {
      console.error('Failed to remove pending post:', request.error);
      reject(request.error);
    };
  });
}

/**
 * Add to sync queue
 */
export async function addToSyncQueue(action, data) {
  if (!db) await initDB();

  return new Promise((resolve, reject) => {
    const tx = db.transaction('sync-queue', 'readwrite');
    const store = tx.objectStore('sync-queue');

    const request = store.add({
      action,
      data,
      createdAt: new Date().toISOString(),
      status: 'pending',
    });

    request.onsuccess = () => {
      resolve(request.result);
    };

    request.onerror = () => {
      reject(request.error);
    };
  });
}

/**
 * Get sync queue
 */
export async function getSyncQueue() {
  if (!db) await initDB();

  return new Promise((resolve, reject) => {
    const tx = db.transaction('sync-queue', 'readonly');
    const store = tx.objectStore('sync-queue');
    const request = store.getAll();

    request.onsuccess = () => {
      resolve(request.result || []);
    };

    request.onerror = () => {
      reject(request.error);
    };
  });
}

/**
 * Clear sync queue
 */
export async function clearSyncQueue() {
  if (!db) await initDB();

  return new Promise((resolve, reject) => {
    const tx = db.transaction('sync-queue', 'readwrite');
    const store = tx.objectStore('sync-queue');
    const request = store.clear();

    request.onsuccess = () => {
      resolve();
    };

    request.onerror = () => {
      reject(request.error);
    };
  });
}
