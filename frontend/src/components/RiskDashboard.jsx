import React from 'react';
import StatCard from './ui/StatCard';
import RiskCharts from './dashboard/RiskCharts';
import RiskiestPathsTable from './dashboard/RiskiestPathsTable';
import RecommendedFixes from './dashboard/RecommendedFixes';
import Skeleton, { StatCardSkeleton, TableSkeleton } from './ui/Skeleton';
import EmptyState from './ui/EmptyState';
import ErrorBoundary from './ui/ErrorBoundary';
import { Network, ShieldAlert, Activity, Server } from 'lucide-react';

export default function RiskDashboard({
  pathsData,
  patchesData,
  status,
  loading,
  onRetry,
  onSelectPath,
  onSimulateFix,
}) {
  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCardSkeleton />
          <StatCardSkeleton />
          <StatCardSkeleton />
          <StatCardSkeleton />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Skeleton className="h-64 rounded-xl" />
          <Skeleton className="h-64 rounded-xl" />
        </div>
        <TableSkeleton rows={5} />
      </div>
    );
  }

  if (status === 'unavailable' || !pathsData) {
    return (
      <EmptyState
        type="unavailable"
        title="Attack Telemetry Unavailable"
        description="Unable to fetch attack paths and vulnerability risk scores from the analysis engine."
        onRetry={onRetry}
      />
    );
  }

  const paths = pathsData || [];
  const patches = patchesData || [];

  // Compute key statistics
  const totalPaths = paths.length;
  const criticalPaths = paths.filter((p) => p.severity === 'critical').length;
  const avgRisk = totalPaths
    ? Math.round(paths.reduce((acc, p) => acc + (p.risk_score || 0), 0) / totalPaths)
    : 0;

  // Extract unique hosts exposed across all path hops
  const exposedHostsSet = new Set();
  paths.forEach((p) => {
    (p.hops || []).forEach((h) => exposedHostsSet.add(h.host));
  });
  const exposedHosts = exposedHostsSet.size;

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Top Telemetry Row: 4 StatCards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Attack Paths"
          value={totalPaths}
          subtitle="Identified exploit vectors"
          icon={Network}
          accentColor="cyan"
        />
        <StatCard
          title="Critical Risk Paths"
          value={criticalPaths}
          subtitle="Immediate remediation required"
          icon={ShieldAlert}
          accentColor="rose"
        />
        <StatCard
          title="Avg Risk Score"
          value={avgRisk}
          subtitle="Out of 100 max exposure"
          icon={Activity}
          accentColor="amber"
        />
        <StatCard
          title="Exposed Target Hosts"
          value={exposedHosts}
          subtitle="Across network segments"
          icon={Server}
          accentColor="emerald"
        />
      </div>

      {/* Visual Analytics Section */}
      <ErrorBoundary componentName="Risk Analytics Charts">
        <RiskCharts paths={paths} />
      </ErrorBoundary>

      {/* Recommended Patches Section */}
      <ErrorBoundary componentName="Recommended Patches">
        <RecommendedFixes patches={patches} onSimulateFix={onSimulateFix} />
      </ErrorBoundary>

      {/* Riskiest Paths Overview Table */}
      <ErrorBoundary componentName="Riskiest Attack Paths Table">
        <RiskiestPathsTable paths={paths} onSelectPath={onSelectPath} />
      </ErrorBoundary>
    </div>
  );
}
