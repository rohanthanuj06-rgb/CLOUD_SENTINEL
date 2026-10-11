import React from 'react';
import { Server, Activity, HardDrive, Cpu, Terminal, ArrowUpRight } from 'lucide-react';
import LiveTopologyMap from '../components/LiveTopologyMap';
import StatusBadge from '../components/StatusBadge';

export default function InfrastructurePage({ nodes = [], onSelectNode, onNavigate }) {
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-white tracking-wide">Virtualized Infrastructure Topology</h2>
          <p className="text-xs text-slate-400">
            Containerized cloud testbed architecture simulating microservices and virtual orchestration on Docker Desktop
          </p>
        </div>
      </div>

      {/* Main Visual Topology Map */}
      <LiveTopologyMap
        nodes={nodes}
        onSelectNode={(id) => {
          onSelectNode(id);
          onNavigate('node-details');
        }}
      />

      {/* Container Workload Specifications Grid */}
      <div className="glass-panel p-5 rounded-xl border border-slate-800">
        <h3 className="text-sm font-bold text-white tracking-wide mb-3">Container Workload Inventory</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {nodes.map((node) => (
            <div
              key={node.node_id}
              onClick={() => {
                onSelectNode(node.node_id);
                onNavigate('node-details');
              }}
              className="p-4 rounded-xl bg-dark-900 border border-slate-800 hover:border-cyan-500/40 cursor-pointer transition-all space-y-2.5"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Server className="w-4 h-4 text-cyan-400" />
                  <span className="font-mono font-bold text-white text-xs">{node.node_id}</span>
                </div>
                <StatusBadge status={node.classification} />
              </div>

              <div className="space-y-1 text-xs text-slate-300 font-mono">
                <div className="flex justify-between">
                  <span className="text-slate-500">Service:</span>
                  <span className="uppercase text-slate-200">{node.service_name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Container:</span>
                  <span className="text-slate-200">{node.container_name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Port Mapping:</span>
                  <span className="text-cyan-300">0.0.0.0:{node.port}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Health Index:</span>
                  <span className="text-emerald-400 font-bold">{Math.round(node.health_score)}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Engine Mode:</span>
                  <span className="text-slate-400">{node.is_simulated ? 'Simulator' : 'Live Docker'}</span>
                </div>
              </div>

              <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-cyan-400 font-semibold">
                <span>View Full Telemetry</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
