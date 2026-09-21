import React, { useEffect } from 'react';
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react';

export default function Toast({ message, type = 'info', onClose, duration = 4000 }) {
  useEffect(() => {
    if (duration && onClose) {
      const timer = setTimeout(() => {
        onClose();
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [duration, onClose]);

  if (!message) return null;

  const styles = {
    success: 'bg-white border-emerald-300 text-slate-900 icon-emerald-600',
    error: 'bg-white border-rose-300 text-slate-900 icon-rose-600',
    info: 'bg-white border-blue-300 text-slate-900 icon-blue-600',
  };

  const icons = {
    success: CheckCircle2,
    error: AlertCircle,
    info: Info,
  };

  const Icon = icons[type] || Info;
  const iconColor = type === 'success' ? 'text-emerald-600' : type === 'error' ? 'text-rose-600' : 'text-blue-600';

  return (
    <div className="fixed bottom-5 right-5 z-50 animate-bounce-short">
      <div
        className={`flex items-center gap-3 px-4 py-3 rounded-xl border shadow-xl text-sm font-medium ${
          styles[type] || styles.info
        }`}
      >
        <Icon className={`w-5 h-5 shrink-0 ${iconColor}`} />
        <span>{message}</span>
        {onClose && (
          <button
            onClick={onClose}
            className="ml-2 text-slate-400 hover:text-slate-800 p-0.5 rounded transition-colors"
            aria-label="Close notification"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
}
