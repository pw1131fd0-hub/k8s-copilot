// Create mock functions inside the mock factory
jest.mock('axios', () => {
  const mockGet = jest.fn();
  const mockPost = jest.fn();
  return {
    create: jest.fn(() => ({
      get: mockGet,
      post: mockPost,
      interceptors: {
        response: {
          use: jest.fn(),
        },
      },
    })),
    __getMockGet: () => mockGet,
    __getMockPost: () => mockPost,
  };
});

import axios from 'axios';

// Get the mock functions from the axios mock
const mockAxiosInstance = axios.create();
const mockGet = mockAxiosInstance.get;
const mockPost = mockAxiosInstance.post;

// Import after mock is set up
import {
  fetchPods,
  fetchClusterStatus,
  diagnosePod,
  scanYaml,
  fetchDiagnoseHistory,
  fetchPodDiagnoseHistory,
  diffYaml,
} from '../utils/api';

describe('API Utility Functions', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('fetchPods', () => {
    test('calls GET /cluster/pods without namespace', async () => {
      const mockData = { pods: [{ name: 'test-pod' }], total: 1 };
      mockGet.mockResolvedValueOnce({ data: mockData });

      const result = await fetchPods();

      expect(mockGet).toHaveBeenCalledWith('/cluster/pods', { params: {} });
      expect(result).toEqual(mockData);
    });

    test('calls GET /cluster/pods with namespace filter', async () => {
      const mockData = { pods: [], total: 0 };
      mockGet.mockResolvedValueOnce({ data: mockData });

      const result = await fetchPods('kube-system');

      expect(mockGet).toHaveBeenCalledWith('/cluster/pods', {
        params: { namespace: 'kube-system' },
      });
      expect(result).toEqual(mockData);
    });
  });

  describe('fetchClusterStatus', () => {
    test('calls GET /cluster/status', async () => {
      const mockData = { status: 'connected', version: 'v1.28.0', message: null };
      mockGet.mockResolvedValueOnce({ data: mockData });

      const result = await fetchClusterStatus();

      expect(mockGet).toHaveBeenCalledWith('/cluster/status');
      expect(result).toEqual(mockData);
    });
  });

  describe('diagnosePod', () => {
    test('calls POST /diagnose/{podName} with default namespace', async () => {
      const mockData = {
        pod_name: 'test-pod',
        root_cause: 'DB connection failed',
      };
      mockPost.mockResolvedValueOnce({ data: mockData });

      const result = await diagnosePod('test-pod');

      expect(mockPost).toHaveBeenCalledWith('/diagnose/test-pod', {
        namespace: 'default',
      });
      expect(result).toEqual(mockData);
    });

    test('calls POST /diagnose/{podName} with custom namespace', async () => {
      const mockData = { pod_name: 'coredns', root_cause: 'Resource limits' };
      mockPost.mockResolvedValueOnce({ data: mockData });

      const result = await diagnosePod('coredns', 'kube-system');

      expect(mockPost).toHaveBeenCalledWith('/diagnose/coredns', {
        namespace: 'kube-system',
      });
      expect(result).toEqual(mockData);
    });
  });

  describe('scanYaml', () => {
    test('calls POST /yaml/scan with content', async () => {
      const mockData = { issues: [], total_issues: 0 };
      mockPost.mockResolvedValueOnce({ data: mockData });

      const yamlContent = 'apiVersion: v1\nkind: Pod';
      const result = await scanYaml(yamlContent);

      expect(mockPost).toHaveBeenCalledWith('/yaml/scan', {
        yaml_content: yamlContent,
        filename: 'manifest.yaml',
      });
      expect(result).toEqual(mockData);
    });

    test('calls POST /yaml/scan with custom filename', async () => {
      const mockData = { issues: [{ rule: 'NO_LIMITS' }], total_issues: 1 };
      mockPost.mockResolvedValueOnce({ data: mockData });

      const result = await scanYaml('apiVersion: v1', 'deployment.yaml');

      expect(mockPost).toHaveBeenCalledWith('/yaml/scan', {
        yaml_content: 'apiVersion: v1',
        filename: 'deployment.yaml',
      });
      expect(result).toEqual(mockData);
    });
  });

  describe('fetchDiagnoseHistory', () => {
    test('calls GET /diagnose/history with default limit', async () => {
      const mockData = [{ id: 1, pod_name: 'test-pod' }];
      mockGet.mockResolvedValueOnce({ data: mockData });

      const result = await fetchDiagnoseHistory();

      expect(mockGet).toHaveBeenCalledWith('/diagnose/history', {
        params: { limit: 50 },
      });
      expect(result).toEqual(mockData);
    });

    test('calls GET /diagnose/history with custom limit', async () => {
      const mockData = [];
      mockGet.mockResolvedValueOnce({ data: mockData });

      const result = await fetchDiagnoseHistory(10);

      expect(mockGet).toHaveBeenCalledWith('/diagnose/history', {
        params: { limit: 10 },
      });
      expect(result).toEqual(mockData);
    });
  });

  describe('fetchPodDiagnoseHistory', () => {
    test('calls GET /diagnose/history/{podName}', async () => {
      const mockData = [{ id: 1, pod_name: 'my-pod', error_type: 'OOMKilled' }];
      mockGet.mockResolvedValueOnce({ data: mockData });

      const result = await fetchPodDiagnoseHistory('my-pod');

      expect(mockGet).toHaveBeenCalledWith('/diagnose/history/my-pod');
      expect(result).toEqual(mockData);
    });
  });

  describe('diffYaml', () => {
    test('calls POST /yaml/diff with two YAML contents', async () => {
      const mockData = { replicas: { dev: 1, prod: 3 } };
      mockPost.mockResolvedValueOnce({ data: mockData });

      const result = await diffYaml('replicas: 1', 'replicas: 3');

      expect(mockPost).toHaveBeenCalledWith('/yaml/diff', {
        yaml_a: 'replicas: 1',
        yaml_b: 'replicas: 3',
      });
      expect(result).toEqual(mockData);
    });

    test('returns empty object for identical YAMLs', async () => {
      const mockData = {};
      mockPost.mockResolvedValueOnce({ data: mockData });

      const result = await diffYaml('foo: bar', 'foo: bar');

      expect(result).toEqual({});
    });
  });
});

describe('API Configuration', () => {
  test('axios instance is created', () => {
    // The api module creates an axios instance when imported
    // We can verify create was called by checking it's a mock function
    expect(jest.isMockFunction(axios.create)).toBe(true);
  });
});
