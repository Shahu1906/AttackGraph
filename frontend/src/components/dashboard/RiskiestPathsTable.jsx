import React, { useState } from 'react';
import RiskBadge from '../ui/RiskBadge';
import { ArrowUpDown, ChevronRight, Compass } from 'lucide-react';

export default function RiskiestPathsTable({ paths = [], onSelectPath }) {
  const [sortField, setSortField] = useState('risk_score');
  const [sortAsc, setSortAsc] = useState(false);

  const handleSort = (field) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  const sortedPaths = [...paths].sort((a, b) => {
    let valA = a[sortField];
    let valB = b[sortField];
    if (sortField === 'hops') {
      valA = a.hops.length;
      valB = b.hops.length;
    }
    if (valA < valB) return sortAsc ? -1 : 1;
    if (valA > valB) return sortAsc ? 1 : -1;
    return 0;
  });

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold text-slate-900">Top Riskiest Attack Paths</h3>
          <p className="text-xs text-slate-500 mt-0.5">Prioritized by multi-hop exploitability and asset critical rating</p>
        </div>
        <span className="text-xs font-mono px-2.5 py-1 rounded bg-slate-100 text-slate-700 border border-slate-200 font-medium">
          Showing {sortedPaths.length} Paths
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-slate-200 text-[11px] font-semibold text-slate-500 uppercase tracking-wider font-mono">
              <th className="py-3 px-4 cursor-pointer hover:text-blue-600 transition-colors" onClick={() => handleSort('id')}>
                <div className="flex items-center gap-1">
                  Path ID <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th className="py-3 px-4 cursor-pointer hover:text-blue-600 transition-colors" onClick={() => handleSort('target')}>
                <div className="flex items-center gap-1">
                  Target Host <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th className="py-3 px-4 cursor-pointer hover:text-blue-600 transition-colors" onClick={() => handleSort('severity')}>
                <div className="flex items-center gap-1">
                  Severity <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th className="py-3 px-4 cursor-pointer hover:text-blue-600 transition-colors" onClick={() => handleSort('risk_score')}>
                <div className="flex items-center gap-1">
                  Risk Score <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th className="py-3 px-4">Exploit Hops Preview</th>
              <th className="py-3 px-4 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-xs">
            {sortedPaths.slice(0, 7).map((path) => (
              <tr
                key={path.id}
                className="hover:bg-blue-50/50 transition-colors group cursor-pointer"
                onClick={() => onSelectPath && onSelectPath(path.id)}
              >
                <td className="py-3 px-4 font-mono text-blue-600 font-semibold">{path.id}</td>
                <td className="py-3 px-4 font-mono text-slate-800 font-medium">{path.target}</td>
                <td className="py-3 px-4">
                  <RiskBadge severity={path.severity} />
                </td>
                <td className="py-3 px-4">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-slate-900">{path.risk_score}</span>
                    <div className="w-16 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${
                          path.risk_score >= 80
                            ? 'bg-rose-500'
                            : path.risk_score >= 60
                            ? 'bg-amber-500'
                            : 'bg-yellow-500'
                        }`}
                        style={{ width: `${path.risk_score}%` }}
                      />
                    </div>
                  </div>
                </td>
                <td className="py-3 px-4">
                  <div className="flex items-center gap-1 text-[11px] text-slate-600 font-mono overflow-hidden max-w-xs truncate">
                    {path.hops.map((h, i) => (
                      <React.Fragment key={i}>
                        <span className="text-slate-800 font-medium">{h.host}</span>
                        {i < path.hops.length - 1 && <span className="text-slate-400">→</span>}
                      </React.Fragment>
                    ))}
                  </div>
                </td>
                <td className="py-3 px-4 text-right">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectPath && onSelectPath(path.id);
                    }}
                    className="inline-flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700 font-semibold opacity-90 group-hover:opacity-100 transition-opacity"
                  >
                    <span>Inspect</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
