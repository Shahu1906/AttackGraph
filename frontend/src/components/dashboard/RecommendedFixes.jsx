import React from 'react';
import { Wrench, ShieldCheck, Zap } from 'lucide-react';
import { useAuth } from '../../auth/AuthContext';

export default function RecommendedFixes({ patches = [], onSimulateFix }) {
  const { isAdmin } = useAuth();

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm my-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
            <Wrench className="w-4 h-4 text-blue-600" />
            <span>Top Recommended Remediation Patches</span>
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">Ranked by maximum reduction of global attack topology exposure</p>
        </div>
        <span className="text-xs font-mono px-2.5 py-1 rounded bg-blue-50 text-blue-700 border border-blue-200 font-semibold">
          Ranked Fixes ({patches.length})
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {patches.slice(0, 4).map((patch, idx) => (
          <div
            key={patch.id}
            className="bg-slate-50/80 border border-slate-200 hover:border-blue-300 rounded-xl p-4 flex flex-col justify-between transition-all group hover:shadow-md"
          >
            <div>
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono font-bold text-slate-600 bg-slate-200/80 px-2 py-0.5 rounded">
                  RANK #{idx + 1}
                </span>
                <span className="text-xs font-mono text-blue-600 font-semibold flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  Closes {patch.paths_closed} {patch.paths_closed === 1 ? 'path' : 'paths'}
                </span>
              </div>

              <div className="mt-3">
                <span className="text-xs font-mono font-bold text-slate-900 block truncate">
                  {patch.vulnerability_id}
                </span>
                <span className="text-[11px] font-mono text-slate-500 block mt-0.5">
                  Host: <strong className="text-slate-800">{patch.host}</strong>
                </span>
                <p className="text-xs text-slate-600 mt-2 line-clamp-2 leading-relaxed">
                  {patch.description}
                </p>
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-200">
              <div className="flex items-center justify-between text-[11px] mb-1.5">
                <span className="text-slate-500 font-medium">Risk Reduction</span>
                <span className="text-emerald-600 font-mono font-bold">-{patch.risk_reduction}%</span>
              </div>
              <div className="w-full h-2 bg-slate-200/70 rounded-full overflow-hidden mb-3">
                <div
                  className="h-full bg-gradient-to-r from-blue-600 to-emerald-500 rounded-full transition-all duration-500"
                  style={{ width: `${patch.risk_reduction}%` }}
                />
              </div>

              {isAdmin && onSimulateFix && (
                <button
                  onClick={() => onSimulateFix(patch.vulnerability_id)}
                  className="w-full py-1.5 px-2 rounded bg-blue-50 hover:bg-blue-600 text-blue-700 hover:text-white border border-blue-200 text-xs font-semibold flex items-center justify-center gap-1.5 transition-all group-hover:border-blue-400"
                >
                  <Zap className="w-3.5 h-3.5 text-blue-600 group-hover:text-white" />
                  Simulate Fix
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
