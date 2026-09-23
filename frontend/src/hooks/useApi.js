import { useState, useEffect, useCallback } from 'react';

/**
 * Execute an API function while tracking its data, service status, loading, and error state.
 *
 * The hook can run on mount and when caller-supplied dependencies change. It
 * exposes `refetch` for explicit retries; it does not retry failed calls
 * automatically.
 *
 * @param {Function} apiFunc - Async function to execute.
 * @param {Array} params - Default arguments passed to `apiFunc`.
 * @param {Object} options - Auto-fetch and effect dependency configuration.
 * @returns {Object} Request state, state setters, and a `refetch` function.
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
