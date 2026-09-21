import React from 'react';
import { Shield, LayoutDashboard, GitFork, Compass, Zap, FileText, Activity } from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab }) {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'topology', label: 'Topology View', icon: GitFork },
    { id: 'explorer', label: 'Attack Paths', icon: Compass },
    { id: 'whatif', label: 'What-If Engine', icon: Zap },
    { id: 'reports', label: 'Report Export', icon: FileText },
  ];

  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col h-screen sticky top-0 z-30 select-none shadow-sm">
      {/* Brand Header */}
      <div className="h-16 px-6 flex items-center gap-3 border-b border-slate-200">
        <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center shadow-md shadow-blue-500/20">
          <Shield className="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 className="font-bold text-base tracking-wide text-slate-900 flex items-center gap-1">
            AttackGraph<span className="text-blue-600">X</span>
          </h1>
          <p className="text-[10px] text-slate-500 font-mono uppercase tracking-widest">Path Analysis & Remediation</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-6 px-3 space-y-1 overflow-y-auto">
        <div className="px-3 pb-2 text-[10px] font-semibold text-slate-400 uppercase tracking-wider font-mono">
          Core Modules
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 group ${
                isActive
                  ? 'bg-blue-50 text-blue-700 border border-blue-200 shadow-sm font-semibold'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/80'
              }`}
            >
              <Icon
                className={`w-4 h-4 transition-colors ${
                  isActive ? 'text-blue-600' : 'text-slate-400 group-hover:text-slate-600'
                }`}
              />
              <span>{item.label}</span>
              {isActive && (
                <div className="ml-auto w-1.5 h-1.5 rounded-full bg-blue-600 shadow-glow-blue" />
              )}
            </button>
          );
        })}
      </nav>

      {/* Footer info */}
      <div className="p-4 border-t border-slate-200 bg-slate-50/50">
        <div className="flex items-center gap-2 text-xs text-slate-600">
          <Activity className="w-3.5 h-3.5 text-blue-600" />
          <span className="font-mono text-[11px]">v2.4.0-Enterprise</span>
        </div>
        <p className="mt-1 text-[10px] text-slate-500">Strict Resilience & RBAC Ready</p>
      </div>
    </aside>
  );
}
