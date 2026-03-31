/**
 * Tests for IndexedDB utility functions
 */

import {
  initDB,
  savePosts,
  getOfflinePosts,
  addPendingPost,
  getPendingPosts,
  removePendingPost,
  addToSyncQueue,
  getSyncQueue,
  clearSyncQueue,
} from '../utils/db';

// Mock IndexedDB
const mockObjectStore = {
  clear: jest.fn(),
  put: jest.fn(),
  add: jest.fn(),
  delete: jest.fn(),
  getAll: jest.fn(),
};

const mockTransaction = {
  objectStore: jest.fn(() => mockObjectStore),
  oncomplete: null,
  onerror: null,
};

const mockDBResult = {
  transaction: jest.fn(() => mockTransaction),
  objectStoreNames: {
    contains: jest.fn(() => false),
  },
  createObjectStore: jest.fn(),
};

const mockOpenRequest = {
  result: mockDBResult,
  error: null,
  onerror: null,
  onsuccess: null,
  onupgradeneeded: null,
};

describe('IndexedDB Utils', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockObjectStore.clear.mockClear();
    mockObjectStore.put.mockClear();
    mockObjectStore.add.mockClear();
    mockObjectStore.delete.mockClear();
    mockObjectStore.getAll.mockClear();

    global.indexedDB = {
      open: jest.fn(() => mockOpenRequest),
    };

    global.console.log = jest.fn();
    global.console.error = jest.fn();
  });

  describe('initDB', () => {
    it('should initialize IndexedDB successfully', async () => {
      const openMock = jest.fn((name, version) => {
        setTimeout(() => {
          mockOpenRequest.onsuccess();
        }, 0);
        return mockOpenRequest;
      });

      global.indexedDB.open = openMock;

      const result = await initDB();
      expect(result).toBe(mockDBResult);
      expect(openMock).toHaveBeenCalledWith('clawbook', 1);
    });

    it('should handle upgrade needed event', async () => {
      const openMock = jest.fn((name, version) => {
        setTimeout(() => {
          mockOpenRequest.onupgradeneeded({ target: { result: mockDBResult } });
          mockOpenRequest.onsuccess();
        }, 0);
        return mockOpenRequest;
      });

      global.indexedDB.open = openMock;

      await initDB();
      expect(mockDBResult.createObjectStore).toHaveBeenCalledWith('posts', { keyPath: 'id' });
    });

    it('should handle database open error', async () => {
      const openMock = jest.fn(() => {
        setTimeout(() => {
          mockOpenRequest.error = new Error('DB Error');
          mockOpenRequest.onerror();
        }, 0);
        return mockOpenRequest;
      });

      global.indexedDB.open = openMock;

      await expect(initDB()).rejects.toThrow();
    });
  });

  describe('savePosts', () => {
    it('should save posts to offline storage', async () => {
      const posts = [
        { id: '1', content: 'Test post 1' },
        { id: '2', content: 'Test post 2' },
      ];

      mockObjectStore.clear.mockImplementation(() => {});
      mockObjectStore.put.mockImplementation(() => {});

      mockTransaction.oncomplete = null;
      const saveMock = jest.fn((posts) => {
        setTimeout(() => {
          if (mockTransaction.oncomplete) {
            mockTransaction.oncomplete();
          }
        }, 0);
        return mockOpenRequest;
      });

      global.indexedDB.open = jest.fn(() => {
        setTimeout(() => {
          mockOpenRequest.onsuccess();
        }, 0);
        return mockOpenRequest;
      });

      await initDB();

      // Manually trigger transaction completion
      mockTransaction.oncomplete = jest.fn();

      const saveResult = savePosts(posts);
      mockTransaction.oncomplete();

      await expect(saveResult).resolves.toBeUndefined();
    });
  });

  describe('getOfflinePosts', () => {
    it('should retrieve offline posts', async () => {
      const mockPosts = [
        { id: '1', content: 'Cached post', savedAt: new Date().toISOString() },
      ];

      global.indexedDB.open = jest.fn(() => {
        setTimeout(() => {
          mockOpenRequest.onsuccess();
        }, 0);
        return mockOpenRequest;
      });

      await initDB();

      // Mock the getAll request
      const getRequest = {
        result: mockPosts,
        onsuccess: null,
        onerror: null,
      };

      mockObjectStore.getAll.mockReturnValue(getRequest);

      const getResult = getOfflinePosts();
      getRequest.onsuccess();

      const result = await getResult;
      expect(result).toEqual(mockPosts);
    });

    it('should return empty array when no posts exist', async () => {
      global.indexedDB.open = jest.fn(() => {
        setTimeout(() => {
          mockOpenRequest.onsuccess();
        }, 0);
        return mockOpenRequest;
      });

      await initDB();

      const getRequest = {
        result: null,
        onsuccess: null,
        onerror: null,
      };

      mockObjectStore.getAll.mockReturnValue(getRequest);

      const getResult = getOfflinePosts();
      getRequest.onsuccess();

      const result = await getResult;
      expect(result).toEqual([]);
    });
  });

  describe('addPendingPost', () => {
    it('should add post to pending queue', async () => {
      global.indexedDB.open = jest.fn(() => {
        setTimeout(() => {
          mockOpenRequest.onsuccess();
        }, 0);
        return mockOpenRequest;
      });

      await initDB();

      const addRequest = {
        result: 1,
        onsuccess: null,
        onerror: null,
      };

      mockObjectStore.add.mockReturnValue(addRequest);

      const postData = { mood: '😊', content: 'New post' };
      const addResult = addPendingPost(postData);
      addRequest.onsuccess();

      const result = await addResult;
      expect(result).toBe(1);
    });
  });

  describe('getPendingPosts', () => {
    it('should retrieve pending posts', async () => {
      global.indexedDB.open = jest.fn(() => {
        setTimeout(() => {
          mockOpenRequest.onsuccess();
        }, 0);
        return mockOpenRequest;
      });

      await initDB();

      const mockPending = [
        {
          id: 1,
          data: { mood: '😊', content: 'Pending post' },
          status: 'pending',
        },
      ];

      const getRequest = {
        result: mockPending,
        onsuccess: null,
        onerror: null,
      };

      mockObjectStore.getAll.mockReturnValue(getRequest);

      const getResult = getPendingPosts();
      getRequest.onsuccess();

      const result = await getResult;
      expect(result).toEqual(mockPending);
    });
  });

  describe('removePendingPost', () => {
    it('should remove post from pending queue', async () => {
      global.indexedDB.open = jest.fn(() => {
        setTimeout(() => {
          mockOpenRequest.onsuccess();
        }, 0);
        return mockOpenRequest;
      });

      await initDB();

      const deleteRequest = {
        onsuccess: null,
        onerror: null,
      };

      mockObjectStore.delete.mockReturnValue(deleteRequest);

      const deleteResult = removePendingPost(1);
      deleteRequest.onsuccess();

      await expect(deleteResult).resolves.toBeUndefined();
    });
  });

  describe('addToSyncQueue', () => {
    it('should add action to sync queue', async () => {
      global.indexedDB.open = jest.fn(() => {
        setTimeout(() => {
          mockOpenRequest.onsuccess();
        }, 0);
        return mockOpenRequest;
      });

      await initDB();

      const addRequest = {
        result: 1,
        onsuccess: null,
        onerror: null,
      };

      mockObjectStore.add.mockReturnValue(addRequest);

      const addResult = addToSyncQueue('create', { mood: '😊' });
      addRequest.onsuccess();

      const result = await addResult;
      expect(result).toBe(1);
    });
  });

  describe('getSyncQueue', () => {
    it('should retrieve sync queue', async () => {
      global.indexedDB.open = jest.fn(() => {
        setTimeout(() => {
          mockOpenRequest.onsuccess();
        }, 0);
        return mockOpenRequest;
      });

      await initDB();

      const mockQueue = [
        {
          id: 1,
          action: 'create',
          data: { mood: '😊' },
          status: 'pending',
        },
      ];

      const getRequest = {
        result: mockQueue,
        onsuccess: null,
        onerror: null,
      };

      mockObjectStore.getAll.mockReturnValue(getRequest);

      const getResult = getSyncQueue();
      getRequest.onsuccess();

      const result = await getResult;
      expect(result).toEqual(mockQueue);
    });
  });

  describe('clearSyncQueue', () => {
    it('should clear entire sync queue', async () => {
      global.indexedDB.open = jest.fn(() => {
        setTimeout(() => {
          mockOpenRequest.onsuccess();
        }, 0);
        return mockOpenRequest;
      });

      await initDB();

      const clearRequest = {
        onsuccess: null,
        onerror: null,
      };

      mockObjectStore.clear.mockReturnValue(clearRequest);

      const clearResult = clearSyncQueue();
      clearRequest.onsuccess();

      await expect(clearResult).resolves.toBeUndefined();
    });
  });
});
