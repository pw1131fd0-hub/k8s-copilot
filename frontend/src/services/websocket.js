/**
 * WebSocket service for real-time collaboration in ClawBook
 * Uses Socket.IO for real-time event handling
 */

import io from 'socket.io-client';

// Global Socket.IO instance
let socket = null;

const API_URL = process.env.REACT_APP_API_URL || '/api/v1';
const SOCKET_URL = new URL(API_URL).origin; // Get base URL for WebSocket

/**
 * Connect to WebSocket server
 */
export const connectWebSocket = (userId = 'default_user') => {
  if (socket && socket.connected) {
    console.log('WebSocket already connected');
    return socket;
  }

  console.log(`Connecting to WebSocket at ${SOCKET_URL}`);

  socket = io(SOCKET_URL, {
    path: '/socket.io/',
    transports: ['websocket', 'polling'],
    reconnection: true,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 5000,
    reconnectionAttempts: 5,
    query: {
      user_id: userId
    }
  });

  // Connection established
  socket.on('connect', () => {
    console.log('WebSocket connected:', socket.id);
  });

  // Connection error
  socket.on('connect_error', (error) => {
    console.error('WebSocket connection error:', error);
  });

  // Reconnection attempt
  socket.on('reconnect_attempt', () => {
    console.log('Attempting to reconnect WebSocket...');
  });

  // Connection acknowledged
  socket.on('connection:ack', (data) => {
    console.log('WebSocket connection acknowledged:', data);
  });

  return socket;
};

/**
 * Disconnect WebSocket
 */
export const disconnectWebSocket = () => {
  if (socket && socket.connected) {
    socket.disconnect();
    socket = null;
    console.log('WebSocket disconnected');
  }
};

/**
 * Get Socket.IO instance
 */
export const getSocket = () => socket;

/**
 * Join a group room for real-time collaboration
 */
export const joinGroupRoom = (groupId) => {
  if (!socket || !socket.connected) {
    console.warn('WebSocket not connected, cannot join group room');
    return;
  }

  socket.emit('join_group', { group_id: groupId });
  console.log(`Joined group room: ${groupId}`);
};

/**
 * Leave a group room
 */
export const leaveGroupRoom = (groupId) => {
  if (!socket || !socket.connected) {
    return;
  }

  socket.emit('leave_group', { group_id: groupId });
  console.log(`Left group room: ${groupId}`);
};

/**
 * Join a post room for comment updates
 */
export const joinPostRoom = (postId) => {
  if (!socket || !socket.connected) {
    console.warn('WebSocket not connected, cannot join post room');
    return;
  }

  socket.emit('join_post', { post_id: postId });
  console.log(`Joined post room: ${postId}`);
};

/**
 * Leave a post room
 */
export const leavePostRoom = (postId) => {
  if (!socket || !socket.connected) {
    return;
  }

  socket.emit('leave_post', { post_id: postId });
  console.log(`Left post room: ${postId}`);
};

/**
 * Subscribe to comment:new events
 */
export const onCommentNew = (callback) => {
  if (!socket) {
    console.warn('WebSocket not initialized');
    return () => {};
  }

  socket.on('comment:new', callback);

  // Return unsubscribe function
  return () => socket.off('comment:new', callback);
};

/**
 * Subscribe to comment:updated events
 */
export const onCommentUpdated = (callback) => {
  if (!socket) return () => {};
  socket.on('comment:updated', callback);
  return () => socket.off('comment:updated', callback);
};

/**
 * Subscribe to comment:deleted events
 */
export const onCommentDeleted = (callback) => {
  if (!socket) return () => {};
  socket.on('comment:deleted', callback);
  return () => socket.off('comment:deleted', callback);
};

/**
 * Subscribe to user:online events
 */
export const onUserOnline = (callback) => {
  if (!socket) return () => {};
  socket.on('user:online', callback);
  return () => socket.off('user:online', callback);
};

/**
 * Subscribe to user:offline events
 */
export const onUserOffline = (callback) => {
  if (!socket) return () => {};
  socket.on('user:offline', callback);
  return () => socket.off('user:offline', callback);
};

/**
 * Subscribe to share:notification events
 */
export const onShareNotification = (callback) => {
  if (!socket) return () => {};
  socket.on('share:notification', callback);
  return () => socket.off('share:notification', callback);
};

/**
 * Subscribe to activity:log events
 */
export const onActivityLog = (callback) => {
  if (!socket) return () => {};
  socket.on('activity:log', callback);
  return () => socket.off('activity:log', callback);
};

/**
 * Send ping to server
 */
export const ping = () => {
  if (!socket || !socket.connected) {
    return;
  }
  socket.emit('ping');
};

/**
 * Subscribe to pong response
 */
export const onPong = (callback) => {
  if (!socket) return () => {};
  socket.on('pong', callback);
  return () => socket.off('pong', callback);
};

/**
 * Get Socket.IO connection status
 */
export const isConnected = () => {
  return socket && socket.connected;
};

/**
 * Get Socket.IO connection ID
 */
export const getSocketId = () => {
  return socket ? socket.id : null;
};

export default {
  connectWebSocket,
  disconnectWebSocket,
  getSocket,
  joinGroupRoom,
  leaveGroupRoom,
  joinPostRoom,
  leavePostRoom,
  onCommentNew,
  onCommentUpdated,
  onCommentDeleted,
  onUserOnline,
  onUserOffline,
  onShareNotification,
  onActivityLog,
  ping,
  onPong,
  isConnected,
  getSocketId,
};
