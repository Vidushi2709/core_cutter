import { useState, useEffect } from 'react';
import { getSwitchHistory } from '../utils/api';

/**
 * Custom hook to fetch and manage switch history with auto-refresh
 */
export function useSwitchHistory(refreshInterval = 2000, limit = 5) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchHistory = async () => {
    try {
      setError(null);
      const data = await getSwitchHistory(limit);
      setHistory(data.switches || []);
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  useEffect(() => {
    // Initial fetch
    fetchHistory();

    // Set up interval for auto-refresh
    const interval = setInterval(fetchHistory, refreshInterval);

    // Cleanup
    return () => clearInterval(interval);
  }, [refreshInterval, limit]);

  return { history, loading, error, refetch: fetchHistory };
}
