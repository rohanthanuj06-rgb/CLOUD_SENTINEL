import React from 'react';
import { Server, Activity, ShieldCheck, Cpu, HardDrive, Wifi } from 'lucide-react';
import StatusBadge from './StatusBadge';

export default function LiveTopologyMap({ nodes = [], onSelectNode, selectedNodeId }) {
  // Mapping layout coordinates for topology
  const layout = [
    { id: 'cs-node-web', label: 'Web Server', x: 120, y: 260 },
    { id: 'cs-node-api', label: 'REST API', x: 280, y: 300 },
    { id: 'cs-node-worker', label: 'Worker Queue', x: 440, y: 300 },
    { id: 'cs-node-auth', label: 'Auth Service', x: 600, y: 260 },
    { id: 'cs-node-storage', label: 'Storage Node', x: 360, y: 380 },
  ];

  const controllerPos = { x: 360, y: 80 };

  const getNodeColor = (classification) => {
    switch (classification) {
      case 'HEALTHY': return '#10b981';
      case 'GOOD': return '#14b8a6';
      case 'WARNING': return '#f59e0b';
      case 'OVERLOADED': return '#f97316';
      case 'CRITICAL':
      case 'DEAD': return '#f43f5e';
      case 'UNRESPONSIVE': return '#a855f7';
      case 'RECOVERING': return '#38bdf8';
      default: return '#10b981';
    }
  };

  return (
    <div className="glass-panel rounded-xl p-5 border border-slate-800">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-sm font-bold text-white tracking-wide">Live Infrastructure Topology</h2>
          <p className="text-xs text-slate-400">
            Real-time topology map connecting Controller to containerized virtual workloads. Click any node to inspect.
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span>Active Telemetry Probes</span>
        </div>
      </div>

      <div className="relative w-full h-[460px] bg-dark-900/60 rounded-xl border border-slate-800/80 overflow-hidden flex items-center justify-center">
        <svg viewBox="0 0 720 440" className="w-full h-full">
          <defs>
            <linearGradient id="controllerGlow" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#0284c7" />
              <stop offset="100%" stopColor="#38bdf8" />
            </linearGradient>
            <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* Connection Lines from Controller to Nodes */}
          {layout.map((pos) => {
            const node = nodes.find((n) => n.node_id === pos.id);
            const color = getNodeColor(node?.classification);
            const isSelected = selectedNodeId === pos.id;

            return (
              <g key={`line-${pos.id}`}>
                <path
                  d={`M ${controllerPos.x} ${controllerPos.y + 35} C ${controllerPos.x} ${(controllerPos.y + pos.y) / 2}, ${pos.x} ${(controllerPos.y + pos.y) / 2}, ${pos.x} ${pos.y - 25}`}
                  fill="none"
                  stroke={isSelected ? '#38bdf8' : color}
                  strokeWidth={isSelected ? 2.5 : 1.5}
                  strokeDasharray="4 4"
                  strokeOpacity={isSelected ? 0.9 : 0.6}
                  className="animate-pulse"
                />
              </g>
            );
          })}

          {/* Central Controller Node */}
          <g transform={`translate(${controllerPos.x}, ${controllerPos.y})`}>
            {/* Halo */}
            <circle r="42" fill="#0284c7" fillOpacity="0.12" filter="url(#glow)" />
            <circle r="32" fill="#0f172a" stroke="#38bdf8" strokeWidth="2" />
            <foreignObject x="-24" y="-24" width="48" height="48">
              <div className="w-full h-full flex items-center justify-center text-cyan-400">
                <ShieldCheck className="w-7 h-7" />
              </div>
            </foreignObject>
            <text y="48" textAnchor="middle" fill="#f8fafc" fontSize="11" fontWeight="700" letterSpacing="0.5">
              CloudSentinel Controller
            </text>
            <text y="62" textAnchor="middle" fill="#94a3b8" fontSize="9" fontFamily="monospace">
              FastAPI Orchestrator
            </text>
          </g>

          {/* Workload Container Nodes */}
          {layout.map((pos) => {
            const node = nodes.find((n) => n.node_id === pos.id);
            const color = getNodeColor(node?.classification);
            const isSelected = selectedNodeId === pos.id;
            const score = node?.health_score ?? 100;

            return (
              <g
                key={`node-${pos.id}`}
                transform={`translate(${pos.x}, ${pos.y})`}
                onClick={() => onSelectNode && onSelectNode(pos.id)}
                className="cursor-pointer transition-transform duration-200 hover:scale-105"
              >
                {/* Halo */}
                <circle
                  r={isSelected ? 36 : 30}
                  fill={color}
                  fillOpacity="0.15"
                  filter="url(#glow)"
                />
                <circle
                  r={isSelected ? 28 : 24}
                  fill="#0f172a"
                  stroke={isSelected ? '#38bdf8' : color}
                  strokeWidth={isSelected ? 2.5 : 1.5}
                />

                <foreignObject x="-14" y="-14" width="28" height="28">
                  <div className="w-full h-full flex items-center justify-center" style={{ color }}>
                    <Server className="w-5 h-5" />
                  </div>
                </foreignObject>

                {/* Node ID label */}
                <text y="40" textAnchor="middle" fill="#ffffff" fontSize="11" fontWeight="600">
                  {pos.id}
                </text>
                <text y="53" textAnchor="middle" fill="#94a3b8" fontSize="9">
                  {pos.label}
                </text>

                {/* Score Pill */}
                <g transform="translate(0, -32)">
                  <rect
                    x="-18"
                    y="-8"
                    width="36"
                    height="16"
                    rx="8"
                    fill="#0b111c"
                    stroke={color}
                    strokeWidth="1"
                  />
                  <text
                    y="3"
                    textAnchor="middle"
                    fill="#ffffff"
                    fontSize="9"
                    fontWeight="700"
                    fontFamily="monospace"
                  >
                    {Math.round(score)}%
                  </text>
                </g>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}
