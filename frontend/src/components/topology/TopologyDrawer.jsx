import React from 'react';
import RiskBadge from '../ui/RiskBadge';
import { X, Server, ShieldAlert, GitBranch, ArrowRight } from 'lucide-react';

export default function TopologyDrawer({ hostData, paths = [], onClose, onSelectPath }) {
  if (!hostData) return null;

  // Filter paths passing through this host
  const hostPaths = paths.filter((p) => p.hops.some((h) => h.host === hostData.id));

  // Extract unique vulnerabilities on this host
  const hostVulns = [];
  const vulnSeen = new Set();
  paths.forEach((p) => {
    p.hops.forEach((h) => {
      if (h.host === hostData.id && !vulnSeen.has(h.vulnerability)) {
        vulnSeen.add(h.vulnerability);
        hostVulns.push(h);
      }
    });
  });

  return (
    <div className="fixed right-0 top-16 bottom-0 w-96 bg-white/95 border-l border-slate-200 shadow-2xl z-30 flex flex-col backdrop-blur-xl animate-slideLeft">
      {/* Header */}
      <div className="p-5 border-b border-slate-200 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-blue-50 border border-blue-200 text-blue-600">
            <Server className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-mono font-bold text-base text-slate-900">{hostData.id}</h3>
            <p className="text-xs text-slate-500 font-mono">IP: {hostData.ip || '10.0.x.x'}</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 text-slate-400 hover:text-slate-800 rounded-lg hover:bg-slate-100 transition-colors"
          aria-label="Close host inspector"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Content Body */}
      <div className="flex-1 overflow-y-auto p-5 space-y-6">
        {/* Host Risk Overview */}
        <div className="bg-slate-50/80 border border-slate-200 rounded-xl p-4 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Host Risk Status</span>
            <RiskBadge severity={hostData.severity} />
          </div>
          <div className="flex items-center justify-between text-xs font-mono pt-2 border-t border-slate-200">
            <span className="text-slate-600">Traversing Paths:</span>
            <span className="font-bold text-blue-600">{hostPaths.length}</span>
          </div>
          <div className="flex items-center justify-between text-xs font-mono">
            <span className="text-slate-600">Identified Vulnerabilities:</span>
            <span className="font-bold text-amber-600">{hostVulns.length}</span>
          </div>
        </div>

        {/* Vulnerabilities Section */}
        <div>
          <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3 flex items-center gap-1.5">
            <ShieldAlert className="w-4 h-4 text-amber-600" />
            Host Vulnerabilities ({hostVulns.length})
          </h4>
          <div className="space-y-2.5">
            {hostVulns.map((v, idx) => (
              <div
                key={idx}
                className="bg-slate-50/80 border border-slate-200 rounded-lg p-3 hover:border-slate-300 transition-colors"
              >
                <div className="flex items-center justify-between font-mono text-xs mb-1">
                  <span className="font-bold text-rose-600">{v.vulnerability}</span>
                  <span className="px-1.5 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200 text-[10px] font-semibold">
                    {v.attack_technique}
                  </span>
                </div>
                <p className="text-xs text-slate-600 mt-1 leading-normal">{v.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Traversing Attack Paths */}
        <div>
          <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3 flex items-center gap-1.5">
            <GitBranch className="w-4 h-4 text-blue-600" />
            Traversing Attack Paths ({hostPaths.length})
          </h4>
          <div className="space-y-2">
            {hostPaths.map((path) => (
              <div
                key={path.id}
                onClick={() => onSelectPath && onSelectPath(path.id)}
                className="bg-slate-50/80 border border-slate-200 rounded-lg p-3 hover:border-blue-400 cursor-pointer transition-all group flex items-center justify-between"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-blue-600">{path.id}</span>
                    <RiskBadge severity={path.severity} />
                  </div>
                  <p className="text-[11px] text-slate-600 font-mono mt-1">
                    Target: <strong className="text-slate-900">{path.target}</strong> ({path.hops.length} Hops)
                  </p>
                </div>
                <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-blue-600 group-hover:translate-x-1 transition-all" />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
