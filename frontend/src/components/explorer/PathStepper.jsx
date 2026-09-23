import React from 'react';
import RiskBadge from '../ui/RiskBadge';
import { Server, Eye, ShieldAlert, Cpu, ArrowRight, ArrowDown, FileText, Zap, BarChart2, CheckCircle2, Shield, AlertTriangle } from 'lucide-react';

export default function PathStepper({ path, onAction }) {
  if (!path) return null;

  const hopCount = path.hops.length;
  const entryHop = path.hops[0];
  const targetHop = path.hops[hopCount - 1];
  const fullPathStr = path.hops.map((h) => h.host).join(' → ');

  // Calculate stats
  const totalCves = path.hops.filter((h) => h.vulnerability).length;
  const totalTechniques = path.hops.filter((h) => h.attack_technique).length;

  const detectabilityConfig = {
    low: { label: 'LOW DETECTABILITY', color: 'text-rose-700 bg-rose-50 border-rose-200' },
    medium: { label: 'MEDIUM DETECTABILITY', color: 'text-amber-700 bg-amber-50 border-amber-200' },
    high: { label: 'HIGH DETECTABILITY', color: 'text-emerald-700 bg-emerald-50 border-emerald-200' },
  };

  const detectStyle = detectabilityConfig[path.detectability || 'low'];

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-6">
      {/* 1. PATH HEADER & ACTION BAR */}
      <div className="pb-5 border-b border-slate-200 space-y-4">
        {/* Top Row: Path ID, Action Bar & Dominant Risk Display */}
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <span className="text-xl font-mono font-bold text-slate-900">{path.id}</span>
              <RiskBadge severity={path.severity} />
            </div>
            <p className="text-xs font-mono text-slate-500 mt-1">
              <strong className="text-slate-900 font-bold">{path.target}</strong> / Customer Records DB
            </p>
          </div>

          <div className="flex items-center gap-5">
            {/* Subtle Action Bar */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => onAction && onAction('export', path)}
                className="px-2.5 py-1 text-xs font-mono text-slate-600 hover:text-blue-600 bg-slate-50 hover:bg-blue-50 border border-slate-200 hover:border-blue-300 rounded-md transition-colors flex items-center gap-1.5"
                title="Export path telemetry"
              >
                <FileText className="w-3.5 h-3.5 text-blue-600" />
                Export Path
              </button>
              <button
                onClick={() => onAction && onAction('compare', path)}
                className="px-2.5 py-1 text-xs font-mono text-slate-600 hover:text-blue-600 bg-slate-50 hover:bg-blue-50 border border-slate-200 hover:border-blue-300 rounded-md transition-colors flex items-center gap-1.5"
                title="Compare with baseline"
              >
                <BarChart2 className="w-3.5 h-3.5 text-blue-600" />
                Compare
              </button>
              <button
                onClick={() => onAction && onAction('whatif', path)}
                className="px-2.5 py-1 text-xs font-mono text-slate-600 hover:text-blue-600 bg-slate-50 hover:bg-blue-50 border border-slate-200 hover:border-blue-300 rounded-md transition-colors flex items-center gap-1.5"
                title="Simulate fix"
              >
                <Zap className="w-3.5 h-3.5 text-amber-500" />
                What-If
              </button>
            </div>

            {/* Dominant Risk Score Display */}
            <div className="flex items-baseline gap-2 border-l border-slate-200 pl-5">
              <div className="text-right font-mono">
                <div className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider">RISK SCORE</div>
                <div className="flex items-baseline justify-end gap-1">
                  <span className="text-3xl font-extrabold text-rose-600 tracking-tight">{path.risk_score}</span>
                  <span className="text-xs text-slate-400 font-semibold">/100</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Primary Information Hero: The Full Attack Path */}
        <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-3 text-xs font-mono text-slate-800 flex items-center gap-2 overflow-x-auto shadow-inner">
          <span className="text-slate-400 font-bold uppercase text-[10px] shrink-0">PATH:</span>
          <span className="font-bold text-blue-700 tracking-wide">{fullPathStr}</span>
        </div>

        {/* Metadata Badges */}
        <div className="flex flex-wrap items-center gap-2 text-[11px] font-mono font-semibold">
          <span className="px-2.5 py-1 rounded bg-slate-100 border border-slate-200 text-slate-700">
            {hopCount} HOPS
          </span>
          <span className={`px-2.5 py-1 rounded border ${detectStyle.color}`}>
            {detectStyle.label}
          </span>
          <span className="px-2.5 py-1 rounded bg-rose-50 border border-rose-200 text-rose-700">
            CROWN JEWEL IMPACT
          </span>
        </div>
      </div>

      {/* 2. ATTACK PATH SUMMARY GRID */}
      <div className="space-y-2">
        <h4 className="text-xs font-mono font-bold text-slate-400 uppercase tracking-wider">
          ATTACK PATH SUMMARY
        </h4>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
          <div className="bg-slate-50/90 border border-slate-200 rounded-lg p-2.5 font-mono">
            <span className="text-[10px] text-slate-400 uppercase">Entry Point</span>
            <p className="text-xs font-bold text-slate-900 truncate mt-0.5">{entryHop?.host}</p>
          </div>
          <div className="bg-slate-50/90 border border-slate-200 rounded-lg p-2.5 font-mono">
            <span className="text-[10px] text-slate-400 uppercase">Target Asset</span>
            <p className="text-xs font-bold text-slate-900 truncate mt-0.5">{targetHop?.host}</p>
          </div>
          <div className="bg-slate-50/90 border border-slate-200 rounded-lg p-2.5 font-mono">
            <span className="text-[10px] text-slate-400 uppercase">Path Length</span>
            <p className="text-xs font-bold text-slate-900 truncate mt-0.5">{hopCount} Hops</p>
          </div>
          <div className="bg-slate-50/90 border border-slate-200 rounded-lg p-2.5 font-mono">
            <span className="text-[10px] text-slate-400 uppercase">Techniques</span>
            <p className="text-xs font-bold text-blue-600 truncate mt-0.5">{totalTechniques} ATT&CK</p>
          </div>
          <div className="bg-slate-50/90 border border-slate-200 rounded-lg p-2.5 font-mono">
            <span className="text-[10px] text-slate-400 uppercase">Critical CVEs</span>
            <p className="text-xs font-bold text-rose-600 truncate mt-0.5">{totalCves} Vulnerabilities</p>
          </div>
          <div className="bg-slate-50/90 border border-slate-200 rounded-lg p-2.5 font-mono">
            <span className="text-[10px] text-slate-400 uppercase">Detectability</span>
            <p className="text-xs font-bold text-amber-600 truncate mt-0.5 capitalize">{path.detectability || 'Low'}</p>
          </div>
        </div>
      </div>

      {/* 3. CONNECTED ATTACK CHAIN VISUALIZATION WITH DIRECTED ARROWS */}
      <div className="space-y-3 pt-2">
        <h4 className="text-xs font-mono font-bold text-slate-400 uppercase tracking-wider">
          ATTACK CHAIN
        </h4>

        <div className="space-y-3 font-mono text-xs">
          {path.hops.map((hop, idx) => {
            const isFirst = idx === 0;
            const isLast = idx === path.hops.length - 1;
            const stepNum = String(idx + 1).padStart(2, '0');

            return (
              <div key={idx} className="flex items-stretch gap-4 group">
                {/* Left Column: Number Circle + Centered Directional Arrow Connector */}
                <div className="flex flex-col items-center shrink-0 w-8">
                  {/* Step Circle Badge */}
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs z-10 border shadow-sm transition-transform group-hover:scale-105 ${
                      isFirst
                        ? 'bg-amber-100 border-amber-400 text-amber-900 ring-2 ring-amber-400/20'
                        : isLast
                        ? 'bg-rose-100 border-rose-400 text-rose-900 ring-2 ring-rose-400/20'
                        : 'bg-white border-slate-300 text-slate-700'
                    }`}
                  >
                    {stepNum}
                  </div>

                  {/* Vertical Arrow Line Connector to Next Step */}
                  {!isLast && (
                    <div className="flex-1 flex flex-col items-center my-1">
                      <div className="w-0.5 bg-blue-400/70 flex-1 min-h-[16px]" />
                      <ArrowDown className="w-3.5 h-3.5 text-blue-500 shrink-0 -mt-0.5" />
                    </div>
                  )}
                </div>

                {/* Node Details Container */}
                <div
                  className={`flex-1 rounded-xl p-3.5 transition-all ${
                    isFirst
                      ? 'bg-amber-50/60 border border-amber-200/80'
                      : isLast
                      ? 'bg-rose-50/60 border border-rose-200/80'
                      : 'bg-slate-50/60 border border-slate-200/60'
                  }`}
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-slate-900 text-sm">{hop.host}</span>
                      <span className="text-slate-400 text-[11px]">({hop.ip || `10.0.${idx + 1}.5`})</span>
                    </div>

                    <div className="flex items-center gap-2">
                      {hop.vulnerability && (
                        <span className="px-2 py-0.5 rounded bg-rose-100/80 border border-rose-200 text-rose-800 text-[11px] font-semibold">
                          {hop.vulnerability}
                        </span>
                      )}
                      {hop.attack_technique && (
                        <span className="px-2 py-0.5 rounded bg-blue-100/80 border border-blue-200 text-blue-800 text-[11px] font-semibold">
                          ATT&CK {hop.attack_technique}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="mt-1 flex items-center justify-between text-[11px] text-slate-500">
                    <span className="font-semibold text-slate-700">
                      {isFirst ? 'Initial Access' : isLast ? 'Crown Jewel Impact' : 'Lateral Movement'}
                    </span>
                  </div>

                  {hop.description && (
                    <p className="text-xs text-slate-600 mt-2 font-sans leading-relaxed">
                      {hop.description}
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 4. RISK DRIVERS ("WHY THIS PATH MATTERS") */}
      <div className="pt-4 border-t border-slate-200 space-y-3">
        <h4 className="text-xs font-mono font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
          <AlertTriangle className="w-4 h-4 text-amber-500" />
          RISK DRIVERS
        </h4>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-200/80 flex items-start gap-2.5">
            <div className="w-2 h-2 rounded-full bg-rose-500 mt-1 shrink-0" />
            <div>
              <span className="text-slate-400 text-[11px]">Critical asset reached</span>
              <p className="font-bold text-slate-900 mt-0.5">{path.target} / Customer Records DB</p>
            </div>
          </div>

          <div className="p-3 rounded-lg bg-slate-50 border border-slate-200/80 flex items-start gap-2.5">
            <div className="w-2 h-2 rounded-full bg-amber-500 mt-1 shrink-0" />
            <div>
              <span className="text-slate-400 text-[11px]">Initial access vector</span>
              <p className="font-bold text-slate-900 mt-0.5">Public-facing RCE ({entryHop?.vulnerability || 'MOVEit Vuln'})</p>
            </div>
          </div>

          <div className="p-3 rounded-lg bg-slate-50 border border-slate-200/80 flex items-start gap-2.5">
            <div className="w-2 h-2 rounded-full bg-blue-500 mt-1 shrink-0" />
            <div>
              <span className="text-slate-400 text-[11px]">Privilege escalation</span>
              <p className="font-bold text-slate-900 mt-0.5">Hardcoded DB administrator credentials</p>
            </div>
          </div>

          <div className="p-3 rounded-lg bg-slate-50 border border-slate-200/80 flex items-start gap-2.5">
            <div className="w-2 h-2 rounded-full bg-slate-500 mt-1 shrink-0" />
            <div>
              <span className="text-slate-400 text-[11px]">Path exposure</span>
              <p className="font-bold text-slate-900 mt-0.5">{hopCount} hosts / {hopCount - 1} lateral transitions</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
