import React, { useState, useEffect } from 'react';
import { AlertTriangle, AlertOctagon, X, RefreshCw } from 'lucide-react';

export default function StatusBanner({ status, onRetry }) {
  const [dismissed, setDismissed] = useState(false);

  // Reset dismissal if status changes
  useEffect(() => {
    setDismissed(false);
  }, [status]);

  if (!status || status === 'live' || dismissed) {
    return null;
  }

  if (status === 'stale_cache') {
    return (
      <div className="bg-amber-50 border-b border-amber-200 text-amber-900 px-4 py-2.5 text-sm flex items-center justify-between shadow-sm animate-fadeIn">
        <div className="flex items-center gap-2.5">
          <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 animate-pulse" />
          <span>
            <strong className="font-semibold text-amber-950">Stale Cache:</strong> Analysis service unreachable, showing last known results.
          </span>
        </div>
        <div className="flex items-center gap-3">
          {onRetry && (
            <button
              onClick={onRetry}
              className="text-xs flex items-center gap-1.5 px-2.5 py-1 bg-amber-100 hover:bg-amber-200 border border-amber-300 rounded transition-colors text-amber-900 font-medium"
            >
              <RefreshCw className="w-3 h-3" /> Recheck
            </button>
          )}
          <button
            onClick={() => setDismissed(true)}
            className="text-amber-600 hover:text-amber-900 p-1 rounded hover:bg-amber-100 transition-colors"
            title="Dismiss banner"
            aria-label="Dismiss banner"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>
    );
  }

  if (status === 'unavailable') {
    return (
      <div className="bg-rose-50 border-b border-rose-200 text-rose-900 px-4 py-2.5 text-sm flex items-center justify-between shadow-sm animate-fadeIn">
        <div className="flex items-center gap-2.5">
          <AlertOctagon className="w-4 h-4 text-rose-600 shrink-0" />
          <span>
            <strong className="font-semibold text-rose-950">Service Unavailable:</strong> Attack analysis gateway is currently offline or unreachable.
          </span>
        </div>
        <div className="flex items-center gap-3">
          {onRetry && (
            <button
              onClick={onRetry}
              className="text-xs flex items-center gap-1.5 px-3 py-1 bg-rose-600 hover:bg-rose-700 text-white font-medium rounded transition-colors shadow-sm"
            >
              <RefreshCw className="w-3 h-3" /> Retry Connection
            </button>
          )}
        </div>
      </div>
    );
  }

  return null;
}
