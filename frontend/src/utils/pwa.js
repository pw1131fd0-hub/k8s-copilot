/**
 * PWA Service Worker registration and management
 */

import {
  initDB,
  savePosts,
  getPendingPosts,
  removePendingPost,
} from './db';

let serviceWorkerRegistration = null;
let isOnline = navigator.onLine;

/**
 * Register Service Worker
 */
export async function registerServiceWorker() {
  if (!('serviceWorker' in navigator)) {
    console.warn('Service Workers not supported');
    return null;
  }

  try {
    const registration = await navigator.serviceWorker.register('/service-worker.js', {
      scope: '/',
    });

    serviceWorkerRegistration = registration;
    console.log('Service Worker registered:', registration);

    // Handle messages from Service Worker
    if (navigator.serviceWorker.controller) {
      navigator.serviceWorker.controller.postMessage({
        type: 'SYNC_CHECK',
      });
    }

    navigator.serviceWorker.addEventListener('message', handleServiceWorkerMessage);

    return registration;
  } catch (error) {
    console.error('Failed to register Service Worker:', error);
    return null;
  }
}

/**
 * Handle messages from Service Worker
 */
function handleServiceWorkerMessage(event) {
  const { data } = event;

  if (data.type === 'sync-complete') {
    console.log(`Synced ${data.synced} posts`);
    // Dispatch custom event for UI to listen
    window.dispatchEvent(
      new CustomEvent('pwa:sync-complete', {
        detail: { synced: data.synced },
      })
    );
  }
}

/**
 * Initialize offline support
 */
export async function initOfflineSupport() {
  // Initialize IndexedDB
  await initDB();

  // Register Service Worker
  await registerServiceWorker();

  // Listen for online/offline events
  window.addEventListener('online', handleOnline);
  window.addEventListener('offline', handleOffline);

  console.log('Offline support initialized');
}

/**
 * Detect online status change
 */
function handleOnline() {
  isOnline = true;
  console.log('Device is online');
  window.dispatchEvent(new CustomEvent('pwa:online'));

  // Trigger sync
  syncPendingPosts();
}

/**
 * Detect offline status change
 */
function handleOffline() {
  isOnline = false;
  console.log('Device is offline');
  window.dispatchEvent(new CustomEvent('pwa:offline'));
}

/**
 * Get current online status
 */
export function getOnlineStatus() {
  return isOnline;
}

/**
 * Sync pending posts with server
 */
export async function syncPendingPosts() {
  if (!isOnline) {
    console.warn('Cannot sync: device is offline');
    return;
  }

  try {
    const pendingPosts = await getPendingPosts();

    if (pendingPosts.length === 0) {
      console.log('No pending posts to sync');
      return;
    }

    console.log(`Syncing ${pendingPosts.length} pending posts...`);

    const syncResults = [];
    for (const pendingPost of pendingPosts) {
      try {
        const response = await fetch('/api/v1/clawbook/posts', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(pendingPost.data),
        });

        if (response.ok) {
          await removePendingPost(pendingPost.id);
          syncResults.push({ id: pendingPost.id, success: true });
          console.log(`Synced post: ${pendingPost.id}`);
        } else {
          syncResults.push({ id: pendingPost.id, success: false, error: 'Server error' });
        }
      } catch (error) {
        syncResults.push({
          id: pendingPost.id,
          success: false,
          error: error.message
        });
        console.error(`Failed to sync post ${pendingPost.id}:`, error);
      }
    }

    // Dispatch sync complete event
    window.dispatchEvent(
      new CustomEvent('pwa:sync-complete', {
        detail: {
          total: pendingPosts.length,
          results: syncResults,
        },
      })
    );

    console.log('Pending posts sync complete');
  } catch (error) {
    console.error('Sync failed:', error);
  }
}

/**
 * Cache posts for offline use
 */
export async function cachePostsForOffline(posts) {
  try {
    await savePosts(posts);
    console.log(`Cached ${posts.length} posts for offline use`);
  } catch (error) {
    console.error('Failed to cache posts:', error);
  }
}

/**
 * Request background sync
 */
export async function requestBackgroundSync() {
  if (!serviceWorkerRegistration || !('sync' in serviceWorkerRegistration)) {
    console.warn('Background Sync not supported');
    return;
  }

  try {
    await serviceWorkerRegistration.sync.register('sync-posts');
    console.log('Background sync registered');
  } catch (error) {
    console.error('Failed to register background sync:', error);
  }
}

/**
 * Unregister Service Worker
 */
export async function unregisterServiceWorker() {
  if (serviceWorkerRegistration) {
    try {
      await serviceWorkerRegistration.unregister();
      console.log('Service Worker unregistered');
    } catch (error) {
      console.error('Failed to unregister Service Worker:', error);
    }
  }
}
