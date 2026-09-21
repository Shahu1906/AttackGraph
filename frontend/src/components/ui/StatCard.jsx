import React from 'react';

export default function StatCard({ title, value, subtitle, icon: Icon, trend, accentColor = 'cyan' }) {
  const borderColors = {
    cyan: 'border-slate-200 hover:border-blue-400 bg-white',
    blue: 'border-blue-200 hover:border-blue-400 bg-blue-50/40',
    rose: 'border-rose-200 hover:border-rose-300 bg-rose-50/40',
    amber: 'border-amber-200 hover:border-amber-300 bg-amber-50/40',
    emerald: 'border-emerald-200 hover:border-emerald-300 bg-emerald-50/40',
  };

  const iconColors = {
    cyan: 'text-blue-600 bg-blue-50 border-blue-200',
    blue: 'text-blue-600 bg-blue-50 border-blue-200',
    rose: 'text-rose-600 bg-rose-50 border-rose-200',
    amber: 'text-amber-600 bg-amber-50 border-amber-200',
    emerald: 'text-emerald-600 bg-emerald-50 border-emerald-200',
  };

  return (
    <div
      className={`rounded-xl p-5 border ${borderColors[accentColor] || borderColors.cyan} transition-all duration-200 shadow-sm relative overflow-hidden group`}
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{title}</p>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-bold font-mono text-slate-900 group-hover:scale-105 transition-transform duration-200 inline-block">
              {value}
            </span>
            {trend && (
              <span
                className={`text-xs font-semibold ${
                  trend.startsWith('-') ? 'text-emerald-600' : 'text-rose-600'
                }`}
              >
                {trend}
              </span>
            )}
          </div>
          {subtitle && <p className="mt-1 text-xs text-slate-500 font-medium">{subtitle}</p>}
        </div>

        {Icon && (
          <div className={`p-3 rounded-lg border ${iconColors[accentColor] || iconColors.cyan} shrink-0`}>
            <Icon className="w-5 h-5" />
          </div>
        )}
      </div>
      <div className="absolute inset-x-0 bottom-0 h-0.5 bg-gradient-to-r from-transparent via-blue-500/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
    </div>
  );
}
