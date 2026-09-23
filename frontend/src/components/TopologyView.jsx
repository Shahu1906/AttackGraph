import React, { useState, useMemo, useRef, useEffect } from 'react';
import CytoscapeComponent from 'react-cytoscapejs';
import TopologyControls from './topology/TopologyControls';
import TopologyDrawer from './topology/TopologyDrawer';
import EmptyState from './ui/EmptyState';
import Skeleton from './ui/Skeleton';

export default function TopologyView({
  pathsData = [],
  status,
  loading,
  selectedPathId,
  setSelectedPathId,
  onRetry,
}) {
  const [layoutName, setLayoutName] = useState('cose');
  const [selectedHost, setSelectedHost] = useState(null);
  const cyRef = useRef(null);

  // Extract Nodes and Edges from Paths data
  const { elements, nodeMap } = useMemo(() => {
    if (!pathsData || pathsData.length === 0) return { elements: [], nodeMap: {} };

    const nodeDict = {};
    const edgeSet = new Set();
    const edges = [];

    const getSevRank = (sev) => {
      const s = (sev || 'low').toLowerCase();
      if (s === 'critical') return 4;
      if (s === 'high') return 3;
      if (s === 'medium') return 2;
      return 1;
    };

    pathsData.forEach((path) => {
      const pathSev = path.severity || 'low';
      const pathRisk = path.risk_score || 0;
      const isSelected = selectedPathId === path.id;

      (path.hops || []).forEach((hop, i) => {
        const host = hop.host;

        if (!nodeDict[host]) {
          nodeDict[host] = {
            id: host,
            ip: hop.ip || '10.0.x.x',
            pathCount: 0,
            severity: pathSev,
            riskScore: pathRisk,
          };
        }

        nodeDict[host].pathCount += 1;
        if (getSevRank(pathSev) > getSevRank(nodeDict[host].severity)) {
          nodeDict[host].severity = pathSev;
        }
        if (pathRisk > nodeDict[host].riskScore) {
          nodeDict[host].riskScore = pathRisk;
        }

        // Add edge to next hop
        if (i < path.hops.length - 1) {
          const nextHost = path.hops[i + 1].host;
          const edgeId = `${host}->${nextHost}`;
          const edgeKey = `${edgeId}:${path.id}`;

          if (!edgeSet.has(edgeKey)) {
            edgeSet.add(edgeKey);
            edges.push({
              data: {
                id: `e-${edges.length}`,
                source: host,
                target: nextHost,
                pathId: path.id,
                isSelected: isSelected,
              },
            });
          }
        }
      });
    });

    const nodes = Object.values(nodeDict).map((n) => {
      const size = Math.min(70, Math.max(38, 38 + n.pathCount * 5));
      const colors = {
        critical: '#ef4444',
        high: '#f97316',
        medium: '#eab308',
        low: '#22c55e',
      };

      return {
        data: {
          id: n.id,
          label: n.id,
          ip: n.ip,
          size: size,
          bgColor: colors[n.severity] || colors.low,
          severity: n.severity,
          pathCount: n.pathCount,
        },
      };
    });

    return { elements: [...nodes, ...edges], nodeMap: nodeDict };
  }, [pathsData, selectedPathId]);

  // Cytoscape Layout Configuration
  const layout = useMemo(() => {
    return {
      name: layoutName,
      animate: true,
      animationDuration: 400,
      padding: 50,
      nodeRepulsion: 8000,
      idealEdgeLength: 100,
    };
  }, [layoutName]);

  // Cytoscape Stylesheet definition
  const stylesheet = [
    {
      selector: 'node',
      style: {
        label: 'data(label)',
        'background-color': 'data(bgColor)',
        width: 'data(size)',
        height: 'data(size)',
        color: '#0f172a',
        'font-family': 'JetBrains Mono, monospace',
        'font-size': '11px',
        'font-weight': 'bold',
        'text-valign': 'center',
        'text-halign': 'center',
        'border-width': '2px',
        'border-color': '#ffffff',
        'border-opacity': 0.9,
        'overlay-padding': '6px',
        'transition-property': 'background-color, width, height, border-color',
        'transition-duration': '0.2s',
      },
    },
    {
      selector: 'edge',
      style: {
        width: 2,
        'line-color': '#94a3b8',
        'target-arrow-color': '#94a3b8',
        'target-arrow-shape': 'triangle',
        'curve-style': 'bezier',
        opacity: selectedPathId ? 0.3 : 0.8,
      },
    },
    {
      selector: 'edge[?isSelected]',
      style: {
        width: 4,
        'line-color': '#2563eb',
        'target-arrow-color': '#2563eb',
        'target-arrow-shape': 'triangle',
        opacity: 1,
        'z-index': 999,
      },
    },
    {
      selector: 'node:selected',
      style: {
        'border-width': '4px',
        'border-color': '#2563eb',
        'border-opacity': 1,
        'shadow-blur': 20,
        'shadow-color': '#2563eb',
      },
    },
  ];

  // Set up Cytoscape instance handlers
  const handleCy = (cy) => {
    cyRef.current = cy;

    cy.off('tap', 'node');
    cy.on('tap', 'node', (evt) => {
      const node = evt.target;
      const nodeId = node.id();
      if (nodeMap[nodeId]) {
        setSelectedHost(nodeMap[nodeId]);
      }
    });

    cy.off('tap');
    cy.on('tap', (evt) => {
      if (evt.target === cy) {
        setSelectedHost(null);
      }
    });
  };

  const handleZoomIn = () => cyRef.current && cyRef.current.zoom(cyRef.current.zoom() * 1.25);
  const handleZoomOut = () => cyRef.current && cyRef.current.zoom(cyRef.current.zoom() * 0.8);
  const handleFit = () => cyRef.current && cyRef.current.fit();

  if (loading) {
    return <Skeleton className="h-[600px] w-full rounded-2xl" />;
  }

  if (status === 'unavailable' || elements.length === 0) {
    return (
      <EmptyState
        type="unavailable"
        title="Topology Service Offline"
        description="The network attack graph topology cannot be rendered at this time."
        onRetry={onRetry}
      />
    );
  }

  return (
    <div className="relative w-full h-[650px] bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
      {/* Controls Overlay */}
      <TopologyControls
        currentLayout={layoutName}
        onChangeLayout={setLayoutName}
        onZoomIn={handleZoomIn}
        onZoomOut={handleZoomOut}
        onFit={handleFit}
        selectedPathId={selectedPathId}
        onClearSelectedPath={() => setSelectedPathId(null)}
      />

      {/* Cytoscape Canvas */}
      <CytoscapeComponent
        elements={elements}
        layout={layout}
        stylesheet={stylesheet}
        style={{ width: '100%', height: '100%', backgroundColor: '#f8fafc' }}
        cy={handleCy}
      />

      {/* Side Host Inspector Drawer */}
      <TopologyDrawer
        hostData={selectedHost}
        paths={pathsData}
        onClose={() => setSelectedHost(null)}
        onSelectPath={(pid) => setSelectedPathId(pid)}
      />
    </div>
  );
}
