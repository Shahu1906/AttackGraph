import React from 'react';

export default function Skeleton({ className = 'h-6 w-full', count = 1 }) {
  return (
    <div className="space-y-3 w-full animate-pulse">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className={`bg-slate-200/70 rounded border border-slate-200/60 ${className}`}
        />
      ))}
    </div>
  );
}

export function StatCardSkeleton() {
  return (
    <div className="rounded-xl p-5 bg-white border border-slate-200 animate-pulse">
      <div className="h-3 bg-slate-200 rounded w-1/2 mb-3" />
      <div className="h-8 bg-slate-200 rounded w-1/3 mb-2" />
      <div className="h-3 bg-slate-100 rounded w-3/4" />
    </div>
  );
}

export function TableSkeleton({ rows = 5 }) {
  return (
    <div className="w-full space-y-2 animate-pulse">
      <div className="h-10 bg-slate-100 border border-slate-200 rounded-lg w-full" />
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="h-12 bg-slate-50 border border-slate-200 rounded-lg w-full" />
      ))}
    </div>
  );
}
