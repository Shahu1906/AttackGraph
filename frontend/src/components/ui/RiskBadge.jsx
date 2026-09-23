import React from 'react';

export default function RiskBadge({ severity, score, className = '' }) {
  const normSeverity = (severity || 'low').toLowerCase();

  const config = {
    critical: {
      bg: 'bg-rose-50 border-rose-200 text-rose-700',
      dot: 'bg-rose-500',
      label: 'Critical',
    },
    high: {
      bg: 'bg-amber-50 border-amber-200 text-amber-700',
      dot: 'bg-amber-500',
      label: 'High',
    },
    medium: {
      bg: 'bg-yellow-50 border-yellow-200 text-yellow-800',
      dot: 'bg-yellow-500',
      label: 'Medium',
    },
    low: {
      bg: 'bg-emerald-50 border-emerald-200 text-emerald-700',
      dot: 'bg-emerald-500',
      label: 'Low',
    },
  };

  const style = config[normSeverity] || config.low;

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${style.bg} ${className}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${style.dot} animate-pulse`} />
      <span>{style.label}</span>
      {score !== undefined && (
        <span className="ml-1 opacity-80 font-mono">({score})</span>
      )}
    </span>
  );
}
