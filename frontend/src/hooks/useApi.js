import { useState, useEffect, useCallback } from 'react';

/**
 * Custom hook to execute API calls with automatic state management & retry logic
 * @param {Function} apiFunc - The async API function from client.js
 * @param {Array} params - Parameters to pass to apiFunc
 * @param {Object} options - Options { autoFetch: true, dependencies: [] }
 */
export function useApi(apiFunc, params = [], options = {}) {
  const { autoFetch = true, dependencies = [] } = options;

  const [data, setData] = useState(null);
  const [status, setStatus] = useState('live'); // 'live' | 'stale_cache' | 'unavailable'
  const [loading, setLoading] = useState(autoFetch);
  const [error, setError] = useState(null);

  const execute = useCallback(async (...overrideParams) => {
    setLoading(true);
    setError(null);
    
    try {
      const finalParams = overrideParams.length > 0 ? overrideParams : params;
      const res = await apiFunc(...finalParams);

      if (res && typeof res === 'object' && 'status' in res) {
        setStatus(res.status || 'live');
        if (res.data !== undefined) {
          setData(res.data);
        } else {
          setData(res);
        }
      } else {
        setData(res);
        setStatus('live');
      }
    } catch (err) {
      setError(err.message || 'An unexpected error occurred');
      setStatus('unavailable');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [apiFunc, JSON.stringify(params)]);

  useEffect(() => {
    if (autoFetch) {
      execute();
    }
  }, [execute, ...dependencies]);

  return {
    data,
    status,
    loading,
    error,
    refetch: execute,
    setData,
    setStatus,
  };
}
