/**
 * Offline-aware API wrapper
 * Provides offline-first data access pattern
 */

import { getOnlineStatus, cachePostsForOffline, syncPendingPosts } from './pwa';
import { getOfflinePosts, addPendingPost } from './db';
import { API_URL } from './api';

/**
 * Fetch posts with offline support
 */
export async function fetchPostsOfflineFirst(limit = 20, offset = 0) {
  const isOnline = getOnlineStatus();

  try {
    if (isOnline) {
      // Try to fetch from server
      const response = await fetch(
        `${API_URL}/clawbook/posts?limit=${limit}&offset=${offset}`
      );

      if (response.ok) {
        const data = await response.json();
        // Cache for offline use
        if (data.posts) {
          await cachePostsForOffline(data.posts);
        }
        return data;
      } else if (response.status === 503) {
        // Server unavailable, use offline data
        console.log('Server unavailable, using offline data');
        return getOfflineData();
      } else {
        throw new Error(`HTTP ${response.status}`);
      }
    } else {
      // Device is offline
      console.log('Device is offline, using cached data');
      return getOfflineData();
    }
  } catch (error) {
    console.warn('Failed to fetch posts online, using offline data:', error);
    return getOfflineData();
  }
}

/**
 * Get offline posts data
 */
async function getOfflineData() {
  const posts = await getOfflinePosts();
  return {
    posts,
    total: posts.length,
    limit: 20,
    offset: 0,
    isOffline: true,
    message: 'Using offline data',
  };
}

/**
 * Create post with offline support
 */
export async function createPostOfflineFirst(postData) {
  const isOnline = getOnlineStatus();

  if (isOnline) {
    try {
      const response = await fetch(`${API_URL}/clawbook/posts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(postData),
      });

      if (response.ok) {
        const data = await response.json();
        return { ...data, isOffline: false };
      } else {
        throw new Error(`HTTP ${response.status}`);
      }
    } catch (error) {
      console.warn('Failed to create post online, saving for offline sync:', error);
      // Save to pending queue
      const pendingId = await addPendingPost(postData);
      return {
        id: `pending-${pendingId}`,
        ...postData,
        isOffline: true,
        isPending: true,
        pendingId,
        message: 'Post will be synced when online',
      };
    }
  } else {
    // Device is offline
    console.log('Device is offline, saving post for later sync');
    const pendingId = await addPendingPost(postData);
    return {
      id: `pending-${pendingId}`,
      ...postData,
      isOffline: true,
      isPending: true,
      pendingId,
      message: 'Post saved. Will sync when online',
    };
  }
}

/**
 * Fetch single post
 */
export async function fetchPostOfflineFirst(postId) {
  const isOnline = getOnlineStatus();

  if (isOnline) {
    try {
      const response = await fetch(`${API_URL}/clawbook/posts/${postId}`);
      if (response.ok) {
        return await response.json();
      }
      throw new Error(`HTTP ${response.status}`);
    } catch (error) {
      console.warn('Failed to fetch post online:', error);
      return getOfflinePost(postId);
    }
  } else {
    return getOfflinePost(postId);
  }
}

/**
 * Get post from offline storage
 */
async function getOfflinePost(postId) {
  const posts = await getOfflinePosts();
  const post = posts.find((p) => p.id === postId);
  if (post) {
    return { ...post, isOffline: true };
  }
  throw new Error('Post not found in offline storage');
}

/**
 * Get mood summary with offline support
 */
export async function getMoodSummaryOfflineFirst(days = 7) {
  const isOnline = getOnlineStatus();

  if (isOnline) {
    try {
      const response = await fetch(
        `${API_URL}/clawbook/mood-summary?days=${days}`
      );
      if (response.ok) {
        return await response.json();
      }
      throw new Error(`HTTP ${response.status}`);
    } catch (error) {
      console.warn('Failed to fetch mood summary online:', error);
      return generateOfflineMoodSummary();
    }
  } else {
    return generateOfflineMoodSummary();
  }
}

/**
 * Generate mood summary from offline posts
 */
async function generateOfflineMoodSummary() {
  const posts = await getOfflinePosts();
  const moodData = {};

  posts.forEach((post) => {
    const mood = post.mood || 'neutral';
    moodData[mood] = (moodData[mood] || 0) + 1;
  });

  return {
    summary: moodData,
    total: posts.length,
    isOffline: true,
    message: 'Mood summary from offline data',
  };
}

/**
 * Check sync status and trigger sync if needed
 */
export async function checkAndSync() {
  const isOnline = getOnlineStatus();
  if (isOnline) {
    await syncPendingPosts();
  }
}
