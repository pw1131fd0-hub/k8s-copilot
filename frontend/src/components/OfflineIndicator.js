/**
 * OfflineIndicator Component
 * Displays offline status and pending sync count
 */

import React, { useState, useEffect } from 'react';
import { getPendingPosts } from '../utils/db';

export default function OfflineIndicator() {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [pendingCount, setPendingCount] = useState(0);
  const [showSync, setShowSync] = useState(false);

  useEffect(() => {
    // Update online status
    const handleOnline = () => {
      setIsOnline(true);
      setShowSync(false);
    };

    const handleOffline = () => {
      setIsOnline(false);
    };

    // Check pending posts
    const checkPending = async () => {
      try {
        const pending = await getPendingPosts();
        setPendingCount(pending.length);
      } catch (error) {
        // Silently fail if IndexedDB is unavailable
        console.warn('Could not check pending posts:', error);
      }
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    window.addEventListener('pwa:offline', handleOffline);
    window.addEventListener('pwa:online', handleOnline);
    window.addEventListener('pwa:sync-complete', () => {
      checkPending();
      setShowSync(true);
      setTimeout(() => setShowSync(false), 3000);
    });

    // Check pending count periodically
    const interval = setInterval(checkPending, 5000);
    checkPending();

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      window.removeEventListener('pwa:offline', handleOffline);
      window.removeEventListener('pwa:online', handleOnline);
      clearInterval(interval);
    };
  }, []);

  if (isOnline && pendingCount === 0) {
    return null; // Don't show when fully online
  }

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-2">
      {!isOnline && (
        <div className="bg-amber-600 text-white px-4 py-2 rounded-lg shadow-lg flex items-center gap-2 animate-pulse">
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8.111 16.5a6.5 6.5 0 0112.222-3.333a4 4 0 11-5.333 6.333M8 12h.01M12 12h.01M16 12h.01"
            />
          </svg>
          <span className="text-sm font-medium">Offline Mode</span>
        </div>
      )}

      {pendingCount > 0 && (
        <div className="bg-blue-600 text-white px-4 py-2 rounded-lg shadow-lg flex items-center gap-2">
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8v4m0 4v.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <span className="text-sm font-medium">
            {pendingCount} post{pendingCount > 1 ? 's' : ''} pending sync
          </span>
        </div>
      )}

      {showSync && (
        <div className="bg-green-600 text-white px-4 py-2 rounded-lg shadow-lg flex items-center gap-2 animate-pulse">
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M5 13l4 4L19 7"
            />
          </svg>
          <span className="text-sm font-medium">Sync Complete!</span>
        </div>
      )}
    </div>
  );
}
