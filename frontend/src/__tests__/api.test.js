import {
  fetchPosts,
  fetchPost,
  createPost,
  deletePost,
  toggleLike,
  addComment,
  deleteComment,
  getMoodSummary,
  API_URL,
} from '../utils/api';

// Mock fetch globally
global.fetch = jest.fn();

describe('API Utility Functions', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  afterEach(() => {
    fetch.mockClear();
  });

  describe('fetchPosts', () => {
    test('calls GET /clawbook/posts with default params', async () => {
      const mockData = { posts: [{ id: '1', content: 'Test post' }], total: 1 };
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      });

      const result = await fetchPosts();

      expect(fetch).toHaveBeenCalledWith(
        `${API_URL}/clawbook/posts?limit=20&offset=0`
      );
      expect(result).toEqual(mockData);
    });

    test('calls GET /clawbook/posts with custom params', async () => {
      const mockData = { posts: [], total: 0 };
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      });

      const result = await fetchPosts(50, 10);

      expect(fetch).toHaveBeenCalledWith(
        `${API_URL}/clawbook/posts?limit=50&offset=10`
      );
      expect(result).toEqual(mockData);
    });
  });

  describe('fetchPost', () => {
    test('calls GET /clawbook/posts/{postId}', async () => {
      const mockData = { id: '123', content: 'Test post' };
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      });

      const result = await fetchPost('123');

      expect(fetch).toHaveBeenCalledWith(`${API_URL}/clawbook/posts/123`);
      expect(result).toEqual(mockData);
    });
  });

  describe('createPost', () => {
    test('calls POST /clawbook/posts with post data', async () => {
      const postData = { content: 'New post', mood: '😊' };
      const mockData = { id: '1', ...postData };
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      });

      const result = await createPost(postData);

      expect(fetch).toHaveBeenCalledWith(`${API_URL}/clawbook/posts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(postData),
      });
      expect(result).toEqual(mockData);
    });
  });

  describe('deletePost', () => {
    test('calls DELETE /clawbook/posts/{postId}', async () => {
      const mockData = { success: true };
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      });

      const result = await deletePost('123');

      expect(fetch).toHaveBeenCalledWith(`${API_URL}/clawbook/posts/123`, {
        method: 'DELETE',
      });
      expect(result).toEqual(mockData);
    });
  });

  describe('toggleLike', () => {
    test('calls POST /clawbook/posts/{postId}/like', async () => {
      const mockData = { liked: true, likeCount: 5 };
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      });

      const result = await toggleLike('123');

      expect(fetch).toHaveBeenCalledWith(
        `${API_URL}/clawbook/posts/123/like`,
        { method: 'POST' }
      );
      expect(result).toEqual(mockData);
    });
  });

  describe('addComment', () => {
    test('calls POST /clawbook/posts/{postId}/comments', async () => {
      const commentData = { content: 'Great post!' };
      const mockData = { id: '1', ...commentData };
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      });

      const result = await addComment('123', commentData);

      expect(fetch).toHaveBeenCalledWith(
        `${API_URL}/clawbook/posts/123/comments`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(commentData),
        }
      );
      expect(result).toEqual(mockData);
    });
  });

  describe('deleteComment', () => {
    test('calls DELETE /clawbook/comments/{commentId}', async () => {
      const mockData = { success: true };
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      });

      const result = await deleteComment('123');

      expect(fetch).toHaveBeenCalledWith(`${API_URL}/clawbook/comments/123`, {
        method: 'DELETE',
      });
      expect(result).toEqual(mockData);
    });
  });

  describe('getMoodSummary', () => {
    test('calls GET /clawbook/mood-summary with default days', async () => {
      const mockData = { moods: { '😊': 5, '😔': 2 } };
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      });

      const result = await getMoodSummary();

      expect(fetch).toHaveBeenCalledWith(
        `${API_URL}/clawbook/mood-summary?days=7`
      );
      expect(result).toEqual(mockData);
    });

    test('calls GET /clawbook/mood-summary with custom days', async () => {
      const mockData = { moods: { '😊': 15 } };
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      });

      const result = await getMoodSummary(30);

      expect(fetch).toHaveBeenCalledWith(
        `${API_URL}/clawbook/mood-summary?days=30`
      );
      expect(result).toEqual(mockData);
    });
  });

  test('throws error when response is not ok', async () => {
    fetch.mockResolvedValueOnce({
      ok: false,
    });

    await expect(fetchPosts()).rejects.toThrow('Failed to fetch posts');
  });
});
