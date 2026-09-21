import React, { useState } from 'react';
import { simulateFix, resetSimulation } from '../api/client';
import { useAuth } from '../auth/AuthContext';
import Skeleton from './ui/Skeleton';
import EmptyState from './ui/EmptyState';
import { Zap, RotateCcw, ShieldCheck, TrendingDown, AlertCircle, ArrowDownRight, CheckCircle } from 'lucide-react';

export default function WhatIfPanel({
  patchesData = [],
  status,
  loading,
  onSimulationApplied,
  onToast,
  onRetry,
}) {
  const { isAdmin } = useAuth();
  const [selectedVuln, setSelectedVuln] = useState('');
  const [simResult, setSimResult] = useState(null);
  const [simulating, setSimulating] = useState(false);
  const [simError, setSimError] = useState(null);
  const [appliedFixes, setAppliedFixes] = useState([]);

  const handleSimulate = async () => {
    if (!selectedVuln) return;
    setSimulating(true);
    setSimError(null);

    try {
      const res = await simulateFix(selectedVuln);
      setSimResult(res);
      setAppliedFixes((prev) => Array.from(new Set([...prev, selectedVuln])));
      if (onToast) {
        onToast(`Simulated fix applied for ${selectedVuln}`, 'success');
      }
      if (onSimulationApplied) {
        onSimulationApplied();
      }
    } catch (err) {
      setSimError(err.message || 'Failed to execute remediation simulation');
      if (onToast) onToast('Simulation failed', 'error');
    } finally {
      setSimulating(false);
    }
  };

  const handleReset = async () => {
    setSimulating(true);
    try {
      await resetSimulation();
      setSimResult(null);
      setAppliedFixes([]);
      setSelectedVuln('');
      if (onToast) onToast('Simulations reset to baseline', 'info');
      if (onSimulationApplied) onSimulationApplied();
    } catch (err) {
      setSimError('Failed to reset simulation');
    } finally {
      setSimulating(false);
    }
  };

  if (loading) {
    return <Skeleton className="h-80 w-full rounded-2xl" />;
  }

  if (status === 'unavailable') {
    return (
      <EmptyState
        type="unavailable"
        title="Simulation Gateway Offline"
        description="The What-If remediation engine is unreachable."
        onRetry={onRetry}
      />
    );
  }

  const selectedPatchObj = patchesData.find((p) => p.vulnerability_id === selectedVuln);

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Simulation Controls Header */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-200">
          <div>
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Zap className="w-5 h-5 text-blue-600" />
              <span>What-If Remediation Simulator</span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5 font-sans">
              Select a target CVE vulnerability to model attack path closures and risk score reduction before patching.
            </p>
          </div>

          {appliedFixes.length > 0 && (
            <button
              onClick={handleReset}
              disabled={simulating}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-mono border border-slate-300 transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5 text-amber-600" />
              Reset Simulations ({appliedFixes.length})
            </button>
          )}
        </div>

        {simError && (
          <div className="mt-4 p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
            <span>{simError}</span>
          </div>
        )}

        {/* Form Selection */}
        <div className="mt-5 grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
          <div className="md:col-span-2">
            <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2 font-mono">
              Target Vulnerability / CVE Patch
            </label>
            <select
              value={selectedVuln}
              onChange={(e) => setSelectedVuln(e.target.value)}
              className="w-full bg-slate-50 border border-slate-300 rounded-xl px-4 py-3 text-xs text-slate-900 font-mono focus:outline-none focus:border-blue-600 focus:bg-white transition-colors"
            >
              <option value="">-- Choose Vulnerability to Remediate --</option>
              {patchesData.map((p) => {
                const isFixed = appliedFixes.includes(p.vulnerability_id);
                return (
                  <option key={p.id} value={p.vulnerability_id} disabled={isFixed} className="bg-white text-slate-800">
                    {p.vulnerability_id} ({p.host}) - Closes {p.paths_closed} paths {isFixed ? '[APPLIED]' : ''}
                  </option>
                );
              })}
            </select>
          </div>

          <button
            onClick={handleSimulate}
            disabled={!selectedVuln || simulating}
            className="w-full py-3 px-5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs shadow-sm flex items-center justify-center gap-2 transition-all disabled:opacity-50 active:scale-95"
          >
            <Zap className={`w-4 h-4 ${simulating ? 'animate-spin' : ''}`} />
            <span>{simulating ? 'Simulating Impact...' : 'Simulate Fix'}</span>
          </button>
        </div>

        {selectedPatchObj && (
          <div className="mt-4 p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-700 flex items-center justify-between font-mono">
            <span>
              Target Host: <strong className="text-blue-600">{selectedPatchObj.host}</strong> | Estimated Risk Reduction:{' '}
              <strong className="text-emerald-600">-{selectedPatchObj.risk_reduction}%</strong>
            </span>
            <span>Closes {selectedPatchObj.paths_closed} vectors</span>
          </div>
        )}
      </div>

      {/* Before / After Comparison Results */}
      {simResult ? (
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-6">
          <div className="flex items-center justify-between pb-3 border-b border-slate-200">
            <h4 className="text-sm font-semibold text-slate-900 font-mono uppercase tracking-wider flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-emerald-600" />
              Remediation Impact Analysis
            </h4>
            <span className="text-xs font-mono text-blue-700 bg-blue-50 px-2.5 py-1 rounded border border-blue-200">
              Vulnerability: {simResult.vulnerability_id}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Metric 1: Path Count */}
            <div className="bg-slate-50/80 border border-slate-200 rounded-xl p-5 relative overflow-hidden group">
              <span className="text-xs text-slate-500 uppercase font-mono font-semibold">Total Attack Paths</span>
              <div className="mt-3 flex items-baseline justify-between">
                <div>
                  <span className="text-slate-400 font-mono text-xs line-through mr-2">{simResult.before.path_count}</span>
                  <span className="text-3xl font-bold font-mono text-slate-900">{simResult.after.path_count}</span>
                </div>
                <span className="px-2.5 py-1 rounded bg-emerald-50 border border-emerald-200 text-emerald-700 font-mono text-xs font-bold flex items-center gap-1">
                  <ArrowDownRight className="w-3.5 h-3.5" />
                  {simResult.after.path_count - simResult.before.path_count} paths
                </span>
              </div>
            </div>

            {/* Metric 2: Critical Paths */}
            <div className="bg-slate-50/80 border border-slate-200 rounded-xl p-5 relative overflow-hidden group">
              <span className="text-xs text-slate-500 uppercase font-mono font-semibold">Critical Paths</span>
              <div className="mt-3 flex items-baseline justify-between">
                <div>
                  <span className="text-slate-400 font-mono text-xs line-through mr-2">{simResult.before.critical_paths}</span>
                  <span className="text-3xl font-bold font-mono text-slate-900">{simResult.after.critical_paths}</span>
                </div>
                <span className="px-2.5 py-1 rounded bg-emerald-50 border border-emerald-200 text-emerald-700 font-mono text-xs font-bold flex items-center gap-1">
                  <ArrowDownRight className="w-3.5 h-3.5" />
                  {simResult.after.critical_paths - simResult.before.critical_paths} critical
                </span>
              </div>
            </div>

            {/* Metric 3: Avg Risk Score */}
            <div className="bg-slate-50/80 border border-slate-200 rounded-xl p-5 relative overflow-hidden group">
              <span className="text-xs text-slate-500 uppercase font-mono font-semibold">Avg Risk Score</span>
              <div className="mt-3 flex items-baseline justify-between">
                <div>
                  <span className="text-slate-400 font-mono text-xs line-through mr-2">{simResult.before.avg_risk}</span>
                  <span className="text-3xl font-bold font-mono text-slate-900">{simResult.after.avg_risk}</span>
                </div>
                <span className="px-2.5 py-1 rounded bg-emerald-50 border border-emerald-200 text-emerald-700 font-mono text-xs font-bold flex items-center gap-1">
                  <TrendingDown className="w-3.5 h-3.5" />
                  {simResult.after.avg_risk - simResult.before.avg_risk} pts
                </span>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <EmptyState
          title="No Active Simulation"
          description="Select a vulnerability from the dropdown above and click 'Simulate Fix' to model risk reduction."
        />
      )}
    </div>
  );
}
