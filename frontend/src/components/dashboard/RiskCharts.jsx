import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts';

export default function RiskCharts({ paths = [] }) {
  // 1. Compute severity counts for Pie Chart
  const severityCounts = { critical: 0, high: 0, medium: 0, low: 0 };
  paths.forEach((p) => {
    const s = (p.severity || 'low').toLowerCase();
    if (severityCounts[s] !== undefined) {
      severityCounts[s]++;
    }
  });

  const donutData = [
    { name: 'Critical', value: severityCounts.critical, color: '#ef4444' },
    { name: 'High', value: severityCounts.high, color: '#f97316' },
    { name: 'Medium', value: severityCounts.medium, color: '#eab308' },
    { name: 'Low', value: severityCounts.low, color: '#22c55e' },
  ].filter((d) => d.value > 0);

  // 2. Compute risk distribution ranges for Bar Chart
  const ranges = [
    { range: '80-100 (Critical)', count: 0 },
    { range: '60-79 (High)', count: 0 },
    { range: '40-59 (Medium)', count: 0 },
    { range: '< 40 (Low)', count: 0 },
  ];

  paths.forEach((p) => {
    const score = p.risk_score || 0;
    if (score >= 80) ranges[0].count++;
    else if (score >= 60) ranges[1].count++;
    else if (score >= 40) ranges[2].count++;
    else ranges[3].count++;
  });

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white border border-slate-200 p-2.5 rounded-lg shadow-xl text-xs font-sans">
          <p className="font-semibold text-slate-900">{payload[0].name || payload[0].payload.range}</p>
          <p className="text-blue-600 font-mono mt-0.5">
            Paths: <strong className="text-slate-900">{payload[0].value}</strong>
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 my-6">
      {/* Risk Distribution Bar Chart */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm flex flex-col justify-between">
        <div className="mb-4">
          <h3 className="text-sm font-semibold text-slate-900 flex items-center justify-between">
            <span>Path Risk Distribution</span>
            <span className="text-xs text-slate-500 font-mono font-normal">Score Ranges</span>
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">Breakdown of attack paths by calculated risk score</p>
        </div>
        <div className="h-56 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={ranges} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <XAxis dataKey="range" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {ranges.map((entry, index) => {
                  const colors = ['#ef4444', '#f97316', '#eab308', '#22c55e'];
                  return <Cell key={`cell-${index}`} fill={colors[index]} />;
                })}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Path Severity Donut Chart */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm flex flex-col justify-between">
        <div className="mb-4">
          <h3 className="text-sm font-semibold text-slate-900 flex items-center justify-between">
            <span>Severity Breakdown</span>
            <span className="text-xs text-slate-500 font-mono font-normal">Categorical</span>
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">Total attack path count grouped by severity level</p>
        </div>
        <div className="h-56 w-full flex items-center justify-center">
          {donutData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={donutData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={80}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {donutData.map((entry, index) => (
                    <Cell key={`cell-donut-${index}`} fill={entry.color} stroke="#ffffff" strokeWidth={2} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
                <Legend
                  verticalAlign="bottom"
                  height={36}
                  iconType="circle"
                  formatter={(value) => <span className="text-xs text-slate-700 font-sans">{value}</span>}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <span className="text-xs text-slate-500 font-mono">No severity metrics available</span>
          )}
        </div>
      </div>
    </div>
  );
}
