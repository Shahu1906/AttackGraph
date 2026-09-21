import React, { useState } from 'react';
import Sidebar from '../components/layout/Sidebar';
import Topbar from '../components/layout/Topbar';
import StatusBanner from '../components/ui/StatusBanner';
import Toast from '../components/ui/Toast';
import ErrorBoundary from '../components/ui/ErrorBoundary';

import RiskDashboard from '../components/RiskDashboard';
import TopologyView from '../components/TopologyView';
import PathExplorer from '../components/PathExplorer';
import WhatIfPanel from '../components/WhatIfPanel';
import ReportExport from '../components/ReportExport';

import { useApi } from '../hooks/useApi';
import { fetchPaths, fetchPatches, setDevSimulatedStatus } from '../api/client';

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedPathId, setSelectedPathId] = useState(null);
  const [simulatedStatus, setSimulatedStatusState] = useState('live');
  const [toast, setToast] = useState(null);

  // API Hooks
  const {
    data: pathsData,
    status: pathsStatus,
    loading: pathsLoading,
    refetch: refetchPaths,
  } = useApi(fetchPaths, ['all'], { autoFetch: true });

  const {
    data: patchesData,
    loading: patchesLoading,
    refetch: refetchPatches,
  } = useApi(fetchPatches, [], { autoFetch: true });

  // Update dev status override when topbar toggle changes
  const handleSetSimulatedStatus = (newStatus) => {
    setDevSimulatedStatus(newStatus);
    setSimulatedStatusState(newStatus);
    refetchPaths();
    refetchPatches();
  };

  const showToast = (message, type = 'info') => {
    setToast({ message, type });
  };

  const handleSelectPathAndNavigate = (pathId) => {
    setSelectedPathId(pathId);
    setActiveTab('topology');
  };

  // Determine current active status flag
  const effectiveStatus = simulatedStatus !== 'live' ? simulatedStatus : pathsStatus;

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex">
      {/* Left Navigation Sidebar */}
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Header Bar */}
        <Topbar
          activeTab={activeTab}
          simulatedStatus={simulatedStatus}
          setSimulatedStatus={handleSetSimulatedStatus}
          onToast={showToast}
        />

        {/* Status Warning Banner (stale_cache or unavailable) */}
        <StatusBanner
          status={effectiveStatus}
          onRetry={() => {
            refetchPaths();
            refetchPatches();
          }}
        />

        {/* Content Body */}
        <main className="flex-1 p-6 max-w-7xl w-full mx-auto overflow-y-auto">
          {activeTab === 'dashboard' && (
            <ErrorBoundary componentName="Risk Dashboard">
              <RiskDashboard
                pathsData={pathsData}
                patchesData={patchesData}
                status={effectiveStatus}
                loading={pathsLoading}
                onRetry={refetchPaths}
                onSelectPath={handleSelectPathAndNavigate}
                onSimulateFix={() => setActiveTab('whatif')}
              />
            </ErrorBoundary>
          )}

          {activeTab === 'topology' && (
            <ErrorBoundary componentName="Topology View">
              <TopologyView
                pathsData={pathsData}
                status={effectiveStatus}
                loading={pathsLoading}
                selectedPathId={selectedPathId}
                setSelectedPathId={setSelectedPathId}
                onRetry={refetchPaths}
              />
            </ErrorBoundary>
          )}

          {activeTab === 'explorer' && (
            <ErrorBoundary componentName="Attack Path Explorer">
              <PathExplorer
                pathsData={pathsData}
                status={effectiveStatus}
                loading={pathsLoading}
                selectedPathId={selectedPathId}
                setSelectedPathId={setSelectedPathId}
                onRetry={refetchPaths}
              />
            </ErrorBoundary>
          )}

          {activeTab === 'whatif' && (
            <ErrorBoundary componentName="What-If Remediation Panel">
              <WhatIfPanel
                patchesData={patchesData}
                status={effectiveStatus}
                loading={patchesLoading}
                onSimulationApplied={() => {
                  refetchPaths();
                  refetchPatches();
                }}
                onToast={showToast}
                onRetry={refetchPaths}
              />
            </ErrorBoundary>
          )}

          {activeTab === 'reports' && (
            <ErrorBoundary componentName="Report Export Module">
              <ReportExport pathsData={pathsData} onToast={showToast} />
            </ErrorBoundary>
          )}
        </main>
      </div>

      {/* Global Toast Notifications */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  );
}
