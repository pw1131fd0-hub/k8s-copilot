/**
 * Custom React hook for WebSocket functionality
 * Handles connection lifecycle and event subscriptions
 */

import { useEffect, useState, useCallback, useRef } from 'react';
import * as websocketService from '../services/websocket';

/**
 * Custom hook for WebSocket connection management
 * @param {string} userId - Current user ID
 * @returns {Object} WebSocket state and methods
 */
export const useWebSocket = (userId = 'default_user') => {
  const [connected, setConnected] = useState(false);
  const [socketId, setSocketId] = useState(null);
  const subscriptionsRef = useRef([]);

  // Connect WebSocket on mount
  useEffect(() => {
    const socket = websocketService.connectWebSocket(userId);

    const handleConnect = () => {
      setConnected(true);
      setSocketId(socket.id);
      console.log('WebSocket hook: Connected');
    };

    const handleDisconnect = () => {
      setConnected(false);
      setSocketId(null);
      console.log('WebSocket hook: Disconnected');
    };

    socket.on('connect', handleConnect);
    socket.on('disconnect', handleDisconnect);

    // Set initial state if already connected
    if (socket.connected) {
      handleConnect();
    }

    // Cleanup on unmount
    return () => {
      socket.off('connect', handleConnect);
      socket.off('disconnect', handleDisconnect);
      // Don't disconnect the socket here - keep it alive for other components
    };
  }, [userId]);

  // Subscribe to events (with automatic cleanup)
  const subscribe = useCallback((eventName, callback) => {
    const unsubscribe = websocketService[`on${eventName.charAt(0).toUpperCase() + eventName.slice(1)}`](callback);
    if (unsubscribe) {
      subscriptionsRef.current.push(unsubscribe);
    }
    return unsubscribe;
  }, []);

  // Cleanup all subscriptions on unmount
  useEffect(() => {
    return () => {
      subscriptionsRef.current.forEach(unsubscribe => {
        if (typeof unsubscribe === 'function') {
          unsubscribe();
        }
      });
      subscriptionsRef.current = [];
    };
  }, []);

  return {
    connected,
    socketId,
    subscribe,
    joinGroupRoom: websocketService.joinGroupRoom,
    leaveGroupRoom: websocketService.leaveGroupRoom,
    joinPostRoom: websocketService.joinPostRoom,
    leavePostRoom: websocketService.leavePostRoom,
  };
};

/**
 * Hook for listening to real-time comment updates
 */
export const useCommentUpdates = (postId, onNewComment, onUpdatedComment, onDeletedComment) => {
  useEffect(() => {
    if (!postId) return;

    websocketService.joinPostRoom(postId);

    const unsubscribeNew = websocketService.onCommentNew(onNewComment);
    const unsubscribeUpdated = websocketService.onCommentUpdated(onUpdatedComment);
    const unsubscribeDeleted = websocketService.onCommentDeleted(onDeletedComment);

    return () => {
      unsubscribeNew && unsubscribeNew();
      unsubscribeUpdated && unsubscribeUpdated();
      unsubscribeDeleted && unsubscribeDeleted();
      websocketService.leavePostRoom(postId);
    };
  }, [postId, onNewComment, onUpdatedComment, onDeletedComment]);
};

/**
 * Hook for listening to user presence in a group
 */
export const useGroupPresence = (groupId, onUserOnline, onUserOffline) => {
  useEffect(() => {
    if (!groupId) return;

    websocketService.joinGroupRoom(groupId);

    const unsubscribeOnline = websocketService.onUserOnline(onUserOnline);
    const unsubscribeOffline = websocketService.onUserOffline(onUserOffline);

    return () => {
      unsubscribeOnline && unsubscribeOnline();
      unsubscribeOffline && unsubscribeOffline();
      websocketService.leaveGroupRoom(groupId);
    };
  }, [groupId, onUserOnline, onUserOffline]);
};

/**
 * Hook for listening to share notifications
 */
export const useShareNotifications = (onNotification) => {
  useEffect(() => {
    const unsubscribe = websocketService.onShareNotification(onNotification);
    return () => unsubscribe && unsubscribe();
  }, [onNotification]);
};

/**
 * Hook for listening to activity log updates
 */
export const useActivityLog = (groupId, onActivity) => {
  useEffect(() => {
    if (!groupId) return;

    websocketService.joinGroupRoom(groupId);
    const unsubscribe = websocketService.onActivityLog(onActivity);

    return () => {
      unsubscribe && unsubscribe();
      websocketService.leaveGroupRoom(groupId);
    };
  }, [groupId, onActivity]);
};

export default useWebSocket;
