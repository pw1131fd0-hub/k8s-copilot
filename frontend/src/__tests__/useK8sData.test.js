import { renderHook, act, waitFor } from '@testing-library/react';
import { useK8sData } from '../hooks/useK8sData';
import * as api from '../utils/api';

// Mock the API
jest.mock('../utils/api', () => ({
  fetchPods: jest.fn(),
  fetchClusterStatus: jest.fn(),
}));

describe('useK8sData Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  describe('Initial Load', () => {
    test('starts with loading state', async () => {
      api.fetchPods.mockImplementation(() => new Promise(() => {}));
      api.fetchClusterStatus.mockImplementation(() => new Promise(() => {}));

      const { result } = renderHook(() => useK8sData());

      expect(result.current.loading).toBe(true);
      expect(result.current.pods).toEqual([]);
      expect(result.current.clusterStatus).toBeNull();
    });

    test('loads pods and cluster status on mount', async () => {
      const mockPods = [{ name: 'pod-1', status: 'Running' }];
      const mockStatus = { status: 'connected', version: '1.28' };

      api.fetchPods.mockResolvedValue({ pods: mockPods });
      api.fetchClusterStatus.mockResolvedValue(mockStatus);

      const { result } = renderHook(() => useK8sData());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.pods).toEqual(mockPods);
      expect(result.current.clusterStatus).toEqual(mockStatus);
      expect(result.current.error).toBeNull();
    });

    test('handles empty pods array', async () => {
      api.fetchPods.mockResolvedValue({ pods: [] });
      api.fetchClusterStatus.mockResolvedValue({ status: 'connected' });

      const { result } = renderHook(() => useK8sData());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.pods).toEqual([]);
    });

    test('handles missing pods key in response', async () => {
      api.fetchPods.mockResolvedValue({});
      api.fetchClusterStatus.mockResolvedValue({ status: 'connected' });

      const { result } = renderHook(() => useK8sData());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.pods).toEqual([]);
    });
  });

  describe('Error Handling', () => {
    test('sets error when API fails', async () => {
      api.fetchPods.mockRejectedValue(new Error('Network error'));
      api.fetchClusterStatus.mockResolvedValue({ status: 'connected' });

      const { result } = renderHook(() => useK8sData());

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.error).toBe('Network error');
    });

    test('clears error on successful refresh', async () => {
      api.fetchPods.mockRejectedValueOnce(new Error('Network error'));
      api.fetchClusterStatus.mockResolvedValue({ status: 'connected' });

      const { result } = renderHook(() => useK8sData());

      await waitFor(() => {
        expect(result.current.error).toBe('Network error');
      });

      api.fetchPods.mockResolvedValue({ pods: [{ name: 'pod-1' }] });

      await act(async () => {
        await result.current.refresh();
      });

      expect(result.current.error).toBeNull();
    });
  });

  describe('Refresh Function', () => {
    test('refresh function reloads data', async () => {
      const mockPods1 = [{ name: 'pod-1' }];
      const mockPods2 = [{ name: 'pod-1' }, { name: 'pod-2' }];

      api.fetchPods.mockResolvedValueOnce({ pods: mockPods1 });
      api.fetchClusterStatus.mockResolvedValue({ status: 'connected' });

      const { result } = renderHook(() => useK8sData());

      await waitFor(() => {
        expect(result.current.pods).toEqual(mockPods1);
      });

      api.fetchPods.mockResolvedValueOnce({ pods: mockPods2 });

      await act(async () => {
        await result.current.refresh();
      });

      expect(result.current.pods).toEqual(mockPods2);
    });
  });

  describe('Auto Refresh', () => {
    test('auto refreshes at specified interval', async () => {
      api.fetchPods.mockResolvedValue({ pods: [] });
      api.fetchClusterStatus.mockResolvedValue({ status: 'connected' });

      renderHook(() => useK8sData(5000));

      await waitFor(() => {
        expect(api.fetchPods).toHaveBeenCalledTimes(1);
      });

      act(() => {
        jest.advanceTimersByTime(5000);
      });

      await waitFor(() => {
        expect(api.fetchPods).toHaveBeenCalledTimes(2);
      });
    });

    test('clears interval on unmount', async () => {
      api.fetchPods.mockResolvedValue({ pods: [] });
      api.fetchClusterStatus.mockResolvedValue({ status: 'connected' });

      const { unmount } = renderHook(() => useK8sData(5000));

      await waitFor(() => {
        expect(api.fetchPods).toHaveBeenCalledTimes(1);
      });

      unmount();

      act(() => {
        jest.advanceTimersByTime(10000);
      });

      // Should still be 1 since interval was cleared
      expect(api.fetchPods).toHaveBeenCalledTimes(1);
    });
  });
});
