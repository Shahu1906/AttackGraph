import React from 'react';
import { ZoomIn, ZoomOut, Maximize2, Layers } from 'lucide-react';

export default function TopologyControls({
  currentLayout,
  onChangeLayout,
  onZoomIn,
  onZoomOut,
  onFit,
  selectedPathId,
  onClearSelectedPath,
}) {
  const layouts = [
    { id: 'cose', label: 'Force-Directed' },
    { id: 'breadthfirst', label: 'Hierarchical' },
    { id: 'circle', label: 'Circular' },
    { id: 'concentric', label: 'Concentric' },
    { id: 'grid', label: 'Grid' },
  ];

  return (
    <div className="absolute top-4 left-4 right-4 z-10 flex flex-wrap items-center justify-between gap-3 pointer-events-none">
      {/* Left: Layout selector & path filter status */}
      <div className="flex items-center gap-2 pointer-events-auto">
        <div className="bg-white/90 border border-slate-200 rounded-lg p-1.5 flex items-center gap-2 shadow-sm backdrop-blur-md">
          <Layers className="w-4 h-4 text-blue-600 ml-1.5" />
          <span className="text-xs text-slate-500 font-mono hidden sm:inline font-medium">Layout:</span>
          <select
            value={currentLayout}
            onChange={(e) => onChangeLayout(e.target.value)}
            className="bg-slate-50 text-slate-800 text-xs font-mono font-medium rounded px-2 py-1 border border-slate-300 focus:outline-none focus:border-blue-600"
          >
            {layouts.map((l) => (
              <option key={l.id} value={l.id}>
                {l.label}
              </option>
            ))}
          </select>
        </div>

        {selectedPathId && (
          <div className="bg-blue-50 border border-blue-200 text-blue-700 text-xs font-mono px-3 py-1.5 rounded-lg flex items-center gap-2 shadow-sm backdrop-blur-md font-medium">
            <span>Highlighting Path: <strong>{selectedPathId}</strong></span>
            <button
              onClick={onClearSelectedPath}
              className="text-blue-600 hover:text-blue-800 font-bold ml-1"
              title="Clear path highlight"
            >
              ✕
            </button>
          </div>
        )}
      </div>

      {/* Right: Zoom controls & Legend */}
      <div className="flex items-center gap-3 pointer-events-auto">
        {/* Zoom Buttons */}
        <div className="bg-white/90 border border-slate-200 rounded-lg p-1 flex items-center gap-1 shadow-sm backdrop-blur-md">
          <button
            onClick={onZoomIn}
            className="p-1.5 text-slate-600 hover:text-blue-600 hover:bg-slate-100 rounded transition-colors"
            title="Zoom In"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            onClick={onZoomOut}
            className="p-1.5 text-slate-600 hover:text-blue-600 hover:bg-slate-100 rounded transition-colors"
            title="Zoom Out"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <button
            onClick={onFit}
            className="p-1.5 text-slate-600 hover:text-blue-600 hover:bg-slate-100 rounded transition-colors"
            title="Fit to Screen"
          >
            <Maximize2 className="w-4 h-4" />
          </button>
        </div>

        {/* Legend */}
        <div className="hidden md:flex items-center gap-3 bg-white/90 border border-slate-200 rounded-lg px-3 py-1.5 shadow-sm backdrop-blur-md text-[11px] font-mono font-medium">
          <span className="text-slate-400 uppercase">Risk:</span>
          <span className="flex items-center gap-1 text-rose-700">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500" /> Critical
          </span>
          <span className="flex items-center gap-1 text-amber-700">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500" /> High
          </span>
          <span className="flex items-center gap-1 text-yellow-700">
            <span className="w-2.5 h-2.5 rounded-full bg-yellow-500" /> Medium
          </span>
          <span className="flex items-center gap-1 text-emerald-700">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" /> Low
          </span>
        </div>
      </div>
    </div>
  );
}
