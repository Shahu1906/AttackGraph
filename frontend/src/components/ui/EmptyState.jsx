import React from 'react';
import { ShieldAlert, RefreshCw, AlertCircle } from 'lucide-react';

export default function EmptyState({
  title = "No Data Available",
  description = "The requested telemetry could not be retrieved at this time.",
  icon: Icon = ShieldAlert,
  onRetry,
  actionLabel = "Retry",
  type = "empty" // "empty" | "unavailable"
}) {
  const isUnavailable = type === 'unavailable';

  return (
    <div className="flex flex-col items-center justify-center p-8 my-6 text-center border border-dashed rounded-xl border-slate-300 bg-slate-50/80 backdrop-blur-sm min-h-[240px]">
      <div
        className={`p-4 rounded-full mb-4 border ${
          isUnavailable
            ? 'bg-rose-50 border-rose-200 text-rose-600'
            : 'bg-slate-100 border-slate-200 text-slate-500'
        }`}
      >
        <Icon className="w-8 h-8" />
      </div>

      <h3 className="text-base font-semibold text-slate-900">{title}</h3>
      <p className="mt-1 text-sm text-slate-500 max-w-md font-sans">{description}</p>

      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-5 inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg bg-blue-600 hover:bg-blue-700 text-white shadow-sm transition-all duration-150 active:scale-95"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          {actionLabel}
        </button>
      )}
    </div>
  );
}
