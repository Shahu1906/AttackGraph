import React, { useState, useEffect } from 'react';
import { useAuth } from '../../auth/AuthContext';
import { Play, LogOut, Shield, ChevronRight, Activity } from 'lucide-react';
import { fetchHealth, triggerScan } from '../../api/client';

export default function Topbar({ activeTab, simulatedStatus, setSimulatedStatus, onToast }) {
  const { user, logout, isAdmin } = useAuth();
  const [health, setHealth] = useState({
    status: 'healthy',
    dependencies: { recon: 'up', analysis: 'up', gateway: 'up' },
  });
  const [isScanning, setIsScanning] = useState(false);

  // Poll health every 15 seconds
  useEffect(() => {
    let isMounted = true;
    const checkHealth = async () => {
      try {
        const data = await fetchHealth();
        if (isMounted && data) {
          setHealth(data);
        }
      } catch (err) {
        if (isMounted) {
          setHealth((prev) => ({
            ...prev,
            status: 'degraded',
            dependencies: { ...prev.dependencies, gateway: 'down' },
          }));
        }
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 15000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const handleTriggerScan = async () => {
    if (!isAdmin) return;
    setIsScanning(true);
    try {
      const res = await triggerScan();
      onToast(res.message || 'Scan initiated successfully', 'success');
    } catch (err) {
      onToast(err.message || 'Failed to trigger scan', 'error');
    } finally {
      setIsScanning(false);
    }
  };

  const breadcrumbs = {
    dashboard: 'Executive Risk Dashboard',
    topology: 'Network Attack Path Topology',
    explorer: 'Attack Path Explorer',
    whatif: 'What-If Remediation Engine',
    reports: 'Report Generation & Export',
  };

  const getDotColor = (state) => {
    return state === 'up' ? 'bg-emerald-500' : 'bg-rose-500';
  };

  return (
    <header className="h-[72px] bg-white border-b border-slate-200 px-6 flex items-center justify-between sticky top-0 z-20 font-mono text-xs select-none">
      {/* 1. BRANDING & BREADCRUMB */}
      <div className="flex items-center gap-2">
        <span className="font-extrabold tracking-tight text-slate-900 text-sm flex items-center gap-1.5">
          <Shield className="w-4 h-4 text-blue-600" />
          <span>AttackGraphX</span>
        </span>
        <span className="text-slate-300 font-bold mx-1">/</span>
        <span className="font-semibold text-slate-700 text-xs">
          {breadcrumbs[activeTab] || 'Dashboard'}
        </span>
      </div>

      {/* 2. RIGHT CONTROLS */}
      <div className="flex items-center gap-4">
        {/* Status Dev Toggle */}
        <div className="flex items-center gap-1.5 bg-slate-50 p-1 rounded-md border border-slate-200/80 text-[11px]">
          <span className="text-[10px] text-slate-400 font-semibold px-1">STATUS:</span>
          
          <div className="flex items-center gap-1">
            {[
              { id: 'live', label: 'LIVE', dot: 'bg-emerald-500', activeBg: 'bg-emerald-50 border-emerald-300 text-emerald-800' },
              { id: 'stale_cache', label: 'STALE', dot: 'bg-amber-500', activeBg: 'bg-amber-50 border-amber-300 text-amber-800' },
              { id: 'unavailable', label: 'OFFLINE', dot: 'bg-rose-500', activeBg: 'bg-rose-50 border-rose-300 text-rose-800' },
            ].map((mode) => {
              const isActive = simulatedStatus === mode.id;
              return (
                <button
                  key={mode.id}
                  onClick={() => setSimulatedStatus(mode.id)}
                  className={`px-2 py-0.5 rounded border text-[10px] font-bold flex items-center gap-1 transition-colors ${
                    isActive
                      ? mode.activeBg
                      : 'border-transparent text-slate-500 hover:text-slate-800 hover:bg-slate-200/50'
                  }`}
                >
                  <span className={`w-1.5 h-1.5 rounded-full ${mode.dot}`} />
                  {mode.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Operational Scan Action */}
        {isAdmin && (
          <button
            onClick={handleTriggerScan}
            disabled={isScanning}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-bold bg-blue-600 hover:bg-blue-700 text-white shadow-sm transition-all disabled:opacity-50 active:scale-95"
          >
            <Play className={`w-3 h-3 ${isScanning ? 'animate-spin' : ''}`} />
            <span>{isScanning ? 'SCANNING...' : 'RUN SCAN'}</span>
          </button>
        )}

        {/* User Account & Logout */}
        <div className="flex items-center gap-3 pl-3 border-l border-slate-200">
          <div className="flex items-center gap-2">
            <span className="font-bold text-slate-900 text-xs">{user?.username || 'analyst'}</span>
            <span className="text-[10px] font-bold px-1.5 py-0.5 rounded border border-slate-200 text-slate-600 bg-slate-100 uppercase">
              {user?.role || 'ANALYST'}
            </span>
          </div>

          <button
            onClick={logout}
            className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded transition-colors"
            title="Sign out"
            aria-label="Sign out"
          >
            <LogOut className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </header>
  );
}
