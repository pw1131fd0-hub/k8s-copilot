// API Configuration
export const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

// Fetch utilities
export async function fetchPosts(limit = 20, offset = 0) {
  const response = await fetch(
    `${API_URL}/clawbook/posts?limit=${limit}&offset=${offset}`
  );
  if (!response.ok) throw new Error('Failed to fetch posts');
  return response.json();
}

export async function fetchPost(postId) {
  const response = await fetch(`${API_URL}/clawbook/posts/${postId}`);
  if (!response.ok) throw new Error('Failed to fetch post');
  return response.json();
}

export async function createPost(postData) {
  const response = await fetch(`${API_URL}/clawbook/posts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(postData),
  });
  if (!response.ok) throw new Error('Failed to create post');
  return response.json();
}

export async function deletePost(postId) {
  const response = await fetch(`${API_URL}/clawbook/posts/${postId}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error('Failed to delete post');
  return response.json();
}

export async function toggleLike(postId) {
  const response = await fetch(`${API_URL}/clawbook/posts/${postId}/like`, {
    method: 'POST',
  });
  if (!response.ok) throw new Error('Failed to toggle like');
  return response.json();
}

export async function addComment(postId, commentData) {
  const response = await fetch(`${API_URL}/clawbook/posts/${postId}/comments`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(commentData),
  });
  if (!response.ok) throw new Error('Failed to add comment');
  return response.json();
}

export async function deleteComment(commentId) {
  const response = await fetch(`${API_URL}/clawbook/comments/${commentId}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error('Failed to delete comment');
  return response.json();
}

export async function getMoodSummary(days = 7) {
  const response = await fetch(`${API_URL}/clawbook/mood-summary?days=${days}`);
  if (!response.ok) throw new Error('Failed to fetch mood summary');
  return response.json();
}

// AI Decision Path APIs (v1.4)
export async function fetchDecisionPath(postId) {
  const response = await fetch(`${API_URL}/clawbook/posts/${postId}/decision-path`);
  if (!response.ok) throw new Error('Failed to fetch decision path');
  return response.json();
}

export async function createDecisionPath(postId, decisionPathData) {
  const response = await fetch(`${API_URL}/clawbook/posts/${postId}/decision-path`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(decisionPathData),
  });
  if (!response.ok) throw new Error('Failed to create decision path');
  return response.json();
}

export async function fetchDecisionPathsHistory(limit = 20, offset = 0) {
  const response = await fetch(
    `${API_URL}/clawbook/decision-paths/history?limit=${limit}&offset=${offset}`
  );
  if (!response.ok) throw new Error('Failed to fetch decision paths history');
  return response.json();
}

// Collaboration APIs (v1.6)
export async function sharePost(postId, sharedWithIds, groupIds = [], permission = 'read') {
  const response = await fetch(`${API_URL}/collaboration/posts/${postId}/share`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ shared_with_ids: sharedWithIds, group_ids: groupIds, permission }),
  });
  if (!response.ok) throw new Error('Failed to share post');
  return response.json();
}

export async function getSharedWithMe(limit = 50) {
  const response = await fetch(`${API_URL}/collaboration/posts/shared-with-me?limit=${limit}`);
  if (!response.ok) throw new Error('Failed to fetch shared posts');
  return response.json();
}

export async function acceptShare(shareId) {
  const response = await fetch(`${API_URL}/collaboration/shares/${shareId}/accept`, {
    method: 'POST',
  });
  if (!response.ok) throw new Error('Failed to accept share');
  return response.json();
}

export async function rejectShare(shareId) {
  const response = await fetch(`${API_URL}/collaboration/shares/${shareId}/reject`, {
    method: 'POST',
  });
  if (!response.ok) throw new Error('Failed to reject share');
  return response.json();
}

export async function revokeShare(shareId) {
  const response = await fetch(`${API_URL}/collaboration/shares/${shareId}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error('Failed to revoke share');
  return response.json();
}

// Group APIs
export async function createGroup(groupData) {
  const response = await fetch(`${API_URL}/collaboration/groups`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(groupData),
  });
  if (!response.ok) throw new Error('Failed to create group');
  return response.json();
}

export async function getGroups() {
  const response = await fetch(`${API_URL}/collaboration/groups`);
  if (!response.ok) throw new Error('Failed to fetch groups');
  return response.json();
}

export async function updateGroup(groupId, groupData) {
  const response = await fetch(`${API_URL}/collaboration/groups/${groupId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(groupData),
  });
  if (!response.ok) throw new Error('Failed to update group');
  return response.json();
}

export async function deleteGroup(groupId) {
  const response = await fetch(`${API_URL}/collaboration/groups/${groupId}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error('Failed to delete group');
  return response.json();
}

export async function addGroupMember(groupId, userId) {
  const response = await fetch(`${API_URL}/collaboration/groups/${groupId}/members`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId }),
  });
  if (!response.ok) throw new Error('Failed to add group member');
  return response.json();
}

export async function removeGroupMember(groupId, userId) {
  const response = await fetch(`${API_URL}/collaboration/groups/${groupId}/members/${userId}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error('Failed to remove group member');
  return response.json();
}

// Comment APIs
export async function addCollaborationComment(postId, commentData) {
  const response = await fetch(`${API_URL}/collaboration/posts/${postId}/comments`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(commentData),
  });
  if (!response.ok) throw new Error('Failed to add comment');
  return response.json();
}

export async function getCollaborationComments(postId) {
  const response = await fetch(`${API_URL}/collaboration/posts/${postId}/comments`);
  if (!response.ok) throw new Error('Failed to fetch comments');
  return response.json();
}

export async function updateComment(commentId, status) {
  const response = await fetch(`${API_URL}/collaboration/comments/${commentId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status }),
  });
  if (!response.ok) throw new Error('Failed to update comment');
  return response.json();
}

export async function deleteCollaborationComment(commentId) {
  const response = await fetch(`${API_URL}/collaboration/comments/${commentId}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error('Failed to delete comment');
  return response.json();
}

export async function getActivityLog(groupId) {
  const response = await fetch(`${API_URL}/collaboration/groups/${groupId}/activity`);
  if (!response.ok) throw new Error('Failed to fetch activity log');
  return response.json();
}

// API client object for backward compatibility
export const api = {
  baseURL: API_URL,
};
