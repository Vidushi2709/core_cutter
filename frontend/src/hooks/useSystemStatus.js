import { useState, useEffect } from 'react';
import { getSystemStatus } from '../utils/api';

/**
 * Custom hook to fetch and manage system status with auto-refresh
 */
export function useSystemStatus(refreshInterval = 3000) {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchStatus = async () => {
    try {
      setError(null);
      const data = await getSystemStatus();
      setStatus(data);
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  useEffect(() => {
    // Initial fetch
    fetchStatus();

    // Set up interval for auto-refresh
    const interval = setInterval(fetchStatus, refreshInterval);

    // Cleanup
    return () => clearInterval(interval);
  }, [refreshInterval]);

  return { status, loading, error, refetch: fetchStatus };
}
