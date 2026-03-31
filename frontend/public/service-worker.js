/**
 * Service Worker for ClawBook PWA
 * Enables offline functionality with cache-first strategy
 */

const CACHE_NAME = 'clawbook-v1';
const API_CACHE = 'clawbook-api-v1';
const ASSET_URLS = [
  '/',
  '/index.html',
];

// Install event - cache assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('Service Worker installing...');
      return cache.addAll(ASSET_URLS).catch((err) => {
        console.warn('Failed to cache assets during install:', err);
      });
    })
  );
  self.skipWaiting();
});

// Activate event - cleanup old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME && name !== API_CACHE)
          .map((name) => {
            console.log('Deleting old cache:', name);
            return caches.delete(name);
          })
      );
    })
  );
  self.clients.claim();
});

// Fetch event - implement cache-first strategy
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    event.respondWith(fetch(request));
    return;
  }

  // API requests - network first with fallback to cache
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          // Cache successful API responses
          if (response.ok) {
            const clone = response.clone();
            caches.open(API_CACHE).then((cache) => {
              cache.put(request, clone);
            });
          }
          return response;
        })
        .catch(() => {
          // Fallback to cached API response
          return caches.match(request).then((response) => {
            return response || new Response(
              JSON.stringify({
                error: 'Offline - using cached data',
                timestamp: new Date().toISOString(),
              }),
              {
                status: 503,
                statusText: 'Service Unavailable',
                headers: { 'Content-Type': 'application/json' },
              }
            );
          });
        })
    );
    return;
  }

  // Asset requests - cache first with fallback to network
  event.respondWith(
    caches.match(request).then((response) => {
      return (
        response ||
        fetch(request).then((response) => {
          if (response.ok && (response.type === 'basic' || response.type === 'cors')) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(request, clone);
            });
          }
          return response;
        })
      );
    })
  );
});

// Handle sync events (background sync)
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-posts') {
    event.waitUntil(syncOfflinePosts());
  }
});

// Sync offline posts when online
async function syncOfflinePosts() {
  try {
    const db = await openDB('clawbook');
    const tx = db.transaction('pending-posts', 'readonly');
    const store = tx.objectStore('pending-posts');
    const allPending = await store.getAll();

    for (const post of allPending) {
      try {
        const response = await fetch('/api/v1/clawbook/posts', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(post.data),
        });

        if (response.ok) {
          const txDelete = db.transaction('pending-posts', 'readwrite');
          await txDelete.objectStore('pending-posts').delete(post.id);
        }
      } catch (error) {
        console.error('Failed to sync post:', error);
      }
    }

    // Notify all clients of sync completion
    const clients = await self.clients.matchAll();
    clients.forEach((client) => {
      client.postMessage({
        type: 'sync-complete',
        synced: allPending.length,
      });
    });
  } catch (error) {
    console.error('Sync error:', error);
  }
}

// Helper to open IndexedDB
function openDB(name) {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(name, 1);
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}
