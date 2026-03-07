import { useState, useEffect, useCallback } from 'react';
import { fetchPods, fetchClusterStatus } from '../utils/api';

export function useK8sData(refreshInterval = 30000) {
  const [pods, setPods] = useState([]);
  const [clusterStatus, setClusterStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    try {
      const [podData, statusData] = await Promise.all([fetchPods(), fetchClusterStatus()]);
      setPods(podData.pods || []);
      setClusterStatus(statusData);
      setError(null);
    } catch (e) {
      setError(e.message || 'Failed to load cluster data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const timer = setInterval(load, refreshInterval);
    return () => clearInterval(timer);
  }, [load, refreshInterval]);

  return { pods, clusterStatus, loading, error, refresh: load };
}
