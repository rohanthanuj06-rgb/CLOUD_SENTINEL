import React from 'react';
import { Activity, Cpu, HardDrive, Wifi, Clock, Server } from 'lucide-react';
import HealthGauge from '../components/HealthGauge';
import StatusBadge from '../components/StatusBadge';
import HealthRadarChart from '../charts/HealthRadarChart';

export default function HealthMonitorPage({ nodes = [], onSelectNode, onNavigate }) {
  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h2 className="text-lg font-bold text-white tracking-wide">Multi-Factor Infrastructure Health Monitor</h2>
        <p className="text-xs text-slate-400">
          Composite health scoring combining CPU (20%), RAM (20%), Network (10%), Response Time (20%), Heartbeat (20%), and App Health (10%)
        </p>
      </div>

      {/* Grid of All Node Health Gauges */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
        {nodes.map((node) => (
          <div
            key={node.node_id}
            onClick={() => {
              onSelectNode(node.node_id);
              onNavigate('node-details');
            }}
            className="glass-panel p-4 rounded-xl border border-slate-800 hover:border-cyan-500/40 cursor-pointer transition-all flex flex-col items-center text-center group"
          >
            <div className="w-full flex items-center justify-between mb-2">
              <span className="font-mono font-bold text-xs text-white group-hover:text-cyan-300">
                {node.node_id}
              </span>
              <StatusBadge status={node.classification} />
            </div>

            <HealthGauge score={node.health_score} size={110} strokeWidth={9} label="Health Index" />

            <div className="w-full mt-3 pt-3 border-t border-slate-800/80 grid grid-cols-2 gap-2 text-[11px] text-slate-400 font-mono">
              <div className="text-left">
                <span>CPU: </span>
                <span className="text-white font-bold">{node.cpu_percent?.toFixed(1)}%</span>
              </div>
              <div className="text-right">
                <span>RAM: </span>
                <span className="text-white font-bold">{node.memory_percent?.toFixed(1)}%</span>
              </div>
              <div className="text-left">
                <span>Latency: </span>
                <span className="text-white font-bold">{Math.round(node.response_time_ms || 0)}ms</span>
              </div>
              <div className="text-right">
                <span>HB: </span>
                <span className={node.heartbeat ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'}>
                  {node.heartbeat ? 'OK' : 'LOST'}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Deep Dive Multi-Factor Radar Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {nodes.slice(0, 2).map((node) => (
          <div key={node.node_id}>
            <HealthRadarChart nodeName={node.node_id} />
          </div>
        ))}
      </div>
    </div>
  );
}
