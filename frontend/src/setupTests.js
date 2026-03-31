// Setup test environment
try {
  require('@testing-library/jest-dom');
} catch (err) {
  console.warn('jest-dom not available, continuing without it');
}

// Mock IndexedDB
const mockIndexedDB = {
  open: jest.fn((name, version) => ({
    onsuccess: null,
    onerror: null,
    onupgradeneeded: null,
    result: {
      createObjectStore: jest.fn(),
      transaction: jest.fn(() => ({
        objectStore: jest.fn(() => ({
          add: jest.fn(() => ({ onsuccess: null, onerror: null })),
          put: jest.fn(() => ({ onsuccess: null, onerror: null })),
          get: jest.fn(() => ({ onsuccess: null, onerror: null })),
          getAll: jest.fn(() => ({ onsuccess: null, onerror: null })),
          delete: jest.fn(() => ({ onsuccess: null, onerror: null })),
          clear: jest.fn(() => ({ onsuccess: null, onerror: null })),
        })),
        oncomplete: null,
        onerror: null,
      })),
      objectStoreNames: [],
    },
  })),
  databases: jest.fn(() => Promise.resolve([])),
  deleteDatabase: jest.fn(() => ({ onsuccess: null, onerror: null })),
};

global.indexedDB = mockIndexedDB;

// Mock Service Worker API
global.navigator.serviceWorker = {
  register: jest.fn(() => Promise.resolve({ scope: '/' })),
  ready: Promise.resolve({}),
  controller: null,
  addEventListener: jest.fn(),
};

// Mock Notification API
global.Notification = {
  permission: 'granted',
  requestPermission: jest.fn(() => Promise.resolve('granted')),
};

// Mock navigator.onLine
Object.defineProperty(global.navigator, 'onLine', {
  writable: true,
  value: true,
});
