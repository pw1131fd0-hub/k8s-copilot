/**
 * Offline-aware API Tests
 */

import {
  fetchPostsOfflineFirst,
  createPostOfflineFirst,
  fetchPostOfflineFirst,
  getMoodSummaryOfflineFirst,
} from '../utils/offlineApi';
import * as pwaModule from '../utils/pwa';
import * as dbModule from '../utils/db';

jest.mock('../utils/pwa', () => ({
  getOnlineStatus: jest.fn(),
  cachePostsForOffline: jest.fn(),
  syncPendingPosts: jest.fn(),
}));

jest.mock('../utils/db', () => ({
  getOfflinePosts: jest.fn(),
  addPendingPost: jest.fn(),
}));

global.fetch = jest.fn();

describe('Offline-aware API', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    fetch.mockClear();
  });

  describe('fetchPostsOfflineFirst', () => {
    it('should fetch from server when online', async () => {
      pwaModule.getOnlineStatus.mockReturnValue(true);

      const mockPosts = [
        { id: 1, mood: '😊', content: 'Hello' },
        { id: 2, mood: '😔', content: 'Sad' },
      ];

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ posts: mockPosts, total: 2 }),
      });

      const result = await fetchPostsOfflineFirst(20, 0);

      expect(result.posts).toEqual(mockPosts);
      expect(result.total).toBe(2);
      expect(result.isOffline).toBeUndefined();
      expect(pwaModule.cachePostsForOffline).toHaveBeenCalledWith(mockPosts);
    });

    it('should use offline data when device is offline', async () => {
      pwaModule.getOnlineStatus.mockReturnValue(false);

      const offlinePosts = [
        { id: 1, mood: '😊', content: 'Cached' },
      ];

      dbModule.getOfflinePosts.mockResolvedValueOnce(offlinePosts);

      const result = await fetchPostsOfflineFirst(20, 0);

      expect(result.posts).toEqual(offlinePosts);
      expect(result.isOffline).toBe(true);
      expect(result.message).toBe('Using offline data');
    });

    it('should fallback to offline data on fetch error', async () => {
      pwaModule.getOnlineStatus.mockReturnValue(true);

      const offlinePosts = [
        { id: 1, mood: '😊', content: 'Cached' },
      ];

      dbModule.getOfflinePosts.mockResolvedValueOnce(offlinePosts);

      fetch.mockRejectedValueOnce(new Error('Network error'));

      const result = await fetchPostsOfflineFirst(20, 0);

      expect(result.posts).toEqual(offlinePosts);
      expect(result.isOffline).toBe(true);
    });
  });

  describe('createPostOfflineFirst', () => {
    const mockPostData = {
      mood: '😊',
      content: 'New post',
      author: 'AI Assistant',
    };

    it('should create post on server when online', async () => {
      pwaModule.getOnlineStatus.mockReturnValue(true);

      const mockResponse = { id: 123, ...mockPostData };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await createPostOfflineFirst(mockPostData);

      expect(result).toEqual(mockResponse);
      expect(result.isOffline).toBeFalsy();
      expect(fetch).toHaveBeenCalledWith(
        '/api/v1/clawbook/posts',
        expect.objectContaining({ method: 'POST' })
      );
    });

    it('should save to pending queue when offline', async () => {
      pwaModule.getOnlineStatus.mockReturnValue(false);
      dbModule.addPendingPost.mockResolvedValueOnce(1);

      const result = await createPostOfflineFirst(mockPostData);

      expect(result.isPending).toBe(true);
      expect(result.isOffline).toBe(true);
      expect(result.message).toContain('saved');
      expect(dbModule.addPendingPost).toHaveBeenCalledWith(mockPostData);
    });

    it('should fallback to pending queue on server error', async () => {
      pwaModule.getOnlineStatus.mockReturnValue(true);
      dbModule.addPendingPost.mockResolvedValueOnce(2);

      fetch.mockRejectedValueOnce(new Error('Server error'));

      const result = await createPostOfflineFirst(mockPostData);

      expect(result.isPending).toBe(true);
      expect(result.isOffline).toBe(true);
      expect(dbModule.addPendingPost).toHaveBeenCalledWith(mockPostData);
    });
  });

  describe('fetchPostOfflineFirst', () => {
    it('should fetch single post from server when online', async () => {
      pwaModule.getOnlineStatus.mockReturnValue(true);

      const mockPost = { id: 1, mood: '😊', content: 'Post' };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockPost,
      });

      const result = await fetchPostOfflineFirst(1);

      expect(result).toEqual(mockPost);
      expect(fetch).toHaveBeenCalledWith('/api/v1/clawbook/posts/1');
    });

    it('should throw error if post not found in offline storage', async () => {
      pwaModule.getOnlineStatus.mockReturnValue(false);
      dbModule.getOfflinePosts.mockResolvedValueOnce([]);

      await expect(fetchPostOfflineFirst(999)).rejects.toThrow(
        'Post not found'
      );
    });
  });

  describe('getMoodSummaryOfflineFirst', () => {
    it('should fetch mood summary when online', async () => {
      pwaModule.getOnlineStatus.mockReturnValue(true);

      const mockSummary = { happy: 5, sad: 2 };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSummary,
      });

      const result = await getMoodSummaryOfflineFirst(7);

      expect(result).toEqual(mockSummary);
      expect(fetch).toHaveBeenCalledWith(
        '/api/v1/clawbook/mood-summary?days=7'
      );
    });

    it('should generate mood summary from offline posts', async () => {
      pwaModule.getOnlineStatus.mockReturnValue(false);

      dbModule.getOfflinePosts.mockResolvedValueOnce([
        { id: 1, mood: '😊' },
        { id: 2, mood: '😊' },
        { id: 3, mood: '😔' },
      ]);

      const result = await getMoodSummaryOfflineFirst(7);

      expect(result.summary['😊']).toBe(2);
      expect(result.summary['😔']).toBe(1);
      expect(result.isOffline).toBe(true);
    });
  });
});
