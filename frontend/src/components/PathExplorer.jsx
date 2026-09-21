import React, { useState, useMemo } from 'react';
import PathStepper from './explorer/PathStepper';
import RiskBadge from './ui/RiskBadge';
import Skeleton from './ui/Skeleton';
import EmptyState from './ui/EmptyState';
import { Search, Filter, Compass, ArrowRight } from 'lucide-react';

export default function PathExplorer({
  pathsData = [],
  status,
  loading,
  selectedPathId,
  setSelectedPathId,
  onRetry,
}) {
  const [targetFilter, setTargetFilter] = useState('all');
  const [severityFilter, setSeverityFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Extract unique target hosts for dropdown filter
  const targetHosts = useMemo(() => {
    if (!pathsData) return [];
    const set = new Set();
    pathsData.forEach((p) => p.target && set.add(p.target));
    return Array.from(set).sort();
  }, [pathsData]);

  // Filter paths
  const filteredPaths = useMemo(() => {
    if (!pathsData) return [];
    return pathsData.filter((path) => {
      if (targetFilter !== 'all' && path.target.toLowerCase() !== targetFilter.toLowerCase()) {
        return false;
      }
      if (severityFilter !== 'all' && path.severity.toLowerCase() !== severityFilter.toLowerCase()) {
        return false;
      }
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        const matchesId = path.id.toLowerCase().includes(q);
        const matchesTarget = path.target.toLowerCase().includes(q);
        const matchesHost = path.hops.some((h) => h.host.toLowerCase().includes(q) || h.vulnerability.toLowerCase().includes(q));
        return matchesId || matchesTarget || matchesHost;
      }
      return true;
    });
  }, [pathsData, targetFilter, severityFilter, searchQuery]);

  // Determine active path
  const activePath = useMemo(() => {
    if (selectedPathId) {
      const found = filteredPaths.find((p) => p.id === selectedPathId) || pathsData.find((p) => p.id === selectedPathId);
      if (found) return found;
    }
    return filteredPaths.length > 0 ? filteredPaths[0] : null;
  }, [filteredPaths, pathsData, selectedPathId]);

  if (loading) {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Skeleton className="h-96 rounded-xl col-span-1" />
        <Skeleton className="h-96 rounded-xl col-span-2" />
      </div>
    );
  }

  if (status === 'unavailable' || pathsData.length === 0) {
    return (
      <EmptyState
        type="unavailable"
        title="Path Telemetry Offline"
        description="The Attack Path Explorer service is currently unreachable."
        onRetry={onRetry}
      />
    );
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Search and Filters Header */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex flex-wrap items-center justify-between gap-4">
        {/* Search */}
        <div className="relative flex-1 min-w-[240px]">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search path ID, host, CVE, or ATT&CK ID..."
            className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs text-slate-900 font-mono focus:outline-none focus:border-blue-600 focus:bg-white transition-colors"
          />
        </div>

        {/* Dropdown Filters */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-lg text-xs font-mono">
            <Filter className="w-3.5 h-3.5 text-blue-600" />
            <span className="text-slate-500 font-medium">Target:</span>
            <select
              value={targetFilter}
              onChange={(e) => setTargetFilter(e.target.value)}
              className="bg-transparent text-slate-800 font-semibold focus:outline-none cursor-pointer"
            >
              <option value="all">All Targets</option>
              {targetHosts.map((h) => (
                <option key={h} value={h} className="bg-white text-slate-800">
                  {h}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-1.5 bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-lg text-xs font-mono">
            <span className="text-slate-500 font-medium">Severity:</span>
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="bg-transparent text-slate-800 font-semibold focus:outline-none cursor-pointer"
            >
              <option value="all">All Severities</option>
              <option value="critical" className="bg-white text-rose-600">Critical</option>
              <option value="high" className="bg-white text-amber-600">High</option>
              <option value="medium" className="bg-white text-yellow-600">Medium</option>
              <option value="low" className="bg-white text-emerald-600">Low</option>
            </select>
          </div>
        </div>
      </div>

      {/* Main Grid: Path List (Left) + Hop Stepper (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Path List */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm space-y-3">
          <div className="flex items-center justify-between pb-3 border-b border-slate-200">
            <h3 className="text-xs font-semibold text-slate-800 font-mono uppercase tracking-wider flex items-center gap-1.5">
              <Compass className="w-4 h-4 text-blue-600" />
              Paths ({filteredPaths.length})
            </h3>
          </div>

          <div className="space-y-1.5 max-h-[620px] overflow-y-auto pr-1">
            {filteredPaths.length > 0 ? (
              filteredPaths.map((path, idx) => {
                const isSelected = activePath && activePath.id === path.id;
                const pathIndex = String(idx + 1).padStart(2, '0');
                const hopChainStr = path.hops.map((h) => h.host).join(' → ');

                return (
                  <div
                    key={path.id}
                    onClick={() => setSelectedPathId(path.id)}
                    className={`p-2.5 rounded-lg border transition-all cursor-pointer font-mono text-xs ${
                      isSelected
                        ? 'bg-blue-50/90 border-blue-500 shadow-sm text-slate-900 ring-1 ring-blue-500/20'
                        : 'bg-slate-50/70 border-slate-200/80 hover:border-slate-300 hover:bg-slate-100/60 text-slate-700'
                    }`}
                  >
                    {/* Top Line: Index, ID, Risk Score & Severity Badge */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-slate-400 font-bold text-[11px]">{pathIndex}</span>
                        <span className="font-bold text-blue-600">{path.id}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-slate-900">{path.risk_score}</span>
                        <RiskBadge severity={path.severity} className="py-0 px-1.5 text-[10px]" />
                      </div>
                    </div>

                    {/* Target Host */}
                    <div className="mt-1 text-slate-900 font-semibold text-[11px]">
                      {path.target}
                    </div>

                    {/* Inline Hop Chain Preview */}
                    <div className="mt-1 text-[10px] text-slate-500 truncate">
                      {hopChainStr}
                    </div>
                  </div>
                );
              })
            ) : (
              <p className="text-xs text-slate-500 text-center py-8 font-mono">
                No paths match current filters.
              </p>
            )}
          </div>
        </div>

        {/* Right Column: Active Path Stepper */}
        <div className="lg:col-span-2">
          {activePath ? (
            <PathStepper
              path={activePath}
              onAction={(action, p) => {
                if (action === 'export') {
                  alert(`Exporting telemetry for attack path ${p.id}...`);
                } else if (action === 'compare') {
                  alert(`Comparing ${p.id} with baseline security topology...`);
                } else if (action === 'whatif') {
                  alert(`Navigating to What-If simulator for ${p.id}...`);
                }
              }}
            />
          ) : (
            <EmptyState
              title="No Path Selected"
              description="Select an attack path from the left menu to inspect step-by-step exploit telemetry."
            />
          )}
        </div>
      </div>
    </div>
  );
}
