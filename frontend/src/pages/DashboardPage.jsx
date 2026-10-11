import React, { useState } from 'react';
import {
  Server,
  Activity,
  AlertTriangle,
  ShieldCheck,
  Cpu,
  HardDrive,
  RefreshCw,
  ExternalLink,
  Flame,
  Zap,
  CheckCircle2,
  XCircle,
  HelpCircle,
  ArrowUpRight
} from 'lucide-react';
import StatCard from '../components/StatCard';
import StatusBadge from '../components/StatusBadge';
import HealthGauge from '../components/HealthGauge';
import LiveTopologyMap from '../components/LiveTopologyMap';
import ConfirmationModal from '../components/ConfirmationModal';
import { api } from '../services/api';

export default function DashboardPage({
  nodes = [],
  summary = {},
  alerts = [],
  recoveries = [],
  onSelectNode,
  onNavigate,
  showNotification,
  refreshAll,
  currentRole
}) {
  const [modalOpen, setModalOpen] = useState(false);
  const [modalAction, setModalAction] = useState(null);

  const handleRestartClick = (nodeId) => {
    setModalAction({
      type: 'restart',
      nodeId,
      title: `Confirm Container Restart`,
      message: `Are you sure you want to trigger a container restart on ${nodeId}? This will cycle the container process and verify post-restart health.`,
    });
    setModalOpen(true);
  };

  const handleConfirmAction = async () => {
    if (!modalAction) return;
    try {
      if (modalAction.type === 'restart') {
        await api.restartNode(modalAction.nodeId);
        showNotification(`Restart initiated for ${modalAction.nodeId}`, 'info');
      }
      refreshAll();
    } catch (err) {
      showNotification(`Action failed: ${err.message}`, 'error');
    } finally {
      setModalOpen(false);
      setModalAction(null);
    }
  };

  // Generate dynamic system insight sentence
  const healthyCount = nodes.filter(n => n.classification === 'HEALTHY' || n.classification === 'GOOD').length;
  const criticalCount = nodes.filter(n => n.classification === 'CRITICAL' || n.classification === 'DEAD').length;
  const warningCount = nodes.filter(n => n.classification === 'WARNING' || n.classification === 'OVERLOADED').length;
  const zombieNode = nodes.find(n => n.classification === 'ZOMBIE');

  let insightText = `${healthyCount} of ${nodes.length} containerized nodes are currently operating normally.`;
  if (criticalCount > 0) {
    insightText = `Critical condition detected on ${criticalCount} workload(s). Autonomous hierarchical self-healing active.`;
  } else if (warningCount > 0) {
    insightText = `Performance degradation detected on ${warningCount} node(s). Telemetry collector monitoring trend.`;
  } else if (zombieNode) {
    insightText = `Node ${zombieNode.node_id} has shown near-zero activity for prolonged duration and is flagged as a zombie workload.`;
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* System Insights Bar (Section 52) */}
      <div className="p-4 rounded-xl bg-gradient-to-r from-blue-950/60 via-slate-900/80 to-cyan-950/40 border border-cyan-500/30 flex items-center justify-between shadow-lg shadow-cyan-950/20">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
            <Zap className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <span className="text-[10px] font-mono font-bold tracking-wider uppercase text-cyan-400">
              Live Infrastructure Intelligence Insight
            </span>
            <p className="text-sm font-semibold text-slate-100 mt-0.5">{insightText}</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => onNavigate('faults')}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-amber-500/15 text-amber-300 border border-amber-500/30 hover:bg-amber-500/25 transition-all"
          >
            <Flame className="w-3.5 h-3.5" />
            Inject Fault
          </button>
        </div>
      </div>

      {/* KPI Stat Cards Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
        <StatCard title="Total Nodes" value={summary.total_nodes ?? 5} icon={Server} color="cyan" />
        <StatCard title="Healthy" value={summary.healthy ?? 5} icon={CheckCircle2} color="emerald" />
        <StatCard title="Warning" value={summary.warning ?? 0} icon={AlertTriangle} color="amber" />
        <StatCard title="Overloaded" value={summary.overloaded ?? 0} icon={Cpu} color="amber" />
        <StatCard title="Critical" value={summary.critical ?? 0} icon={XCircle} color="rose" />
        <StatCard title="Recovering" value={summary.recovering ?? 0} icon={Activity} color="blue" />
        <StatCard title="Zombie" value={summary.zombie ?? 0} icon={HelpCircle} color="purple" />
        <StatCard
          title="Recovery Rate"
          value={`${summary.recovery_success_rate ?? 100}%`}
          icon={ShieldCheck}
          color="emerald"
        />
      </div>

      {/* Centerpiece: Topology & Quick Telemetry Split */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <LiveTopologyMap
            nodes={nodes}
            onSelectNode={(id) => {
              onSelectNode(id);
              onNavigate('node-details');
            }}
          />
        </div>

        {/* Global Average Health Gauge & Alert Summary */}
        <div className="glass-panel p-5 rounded-xl border border-slate-800 flex flex-col justify-between space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white tracking-wide">Cluster Health Index</h3>
            <span className="text-xs font-mono text-cyan-400">Multi-Factor Engine</span>
          </div>

          <div className="py-2 flex justify-center">
            <HealthGauge score={summary.average_health_score ?? 95} size={150} strokeWidth={12} label="Average Cluster Health" />
          </div>

          {/* Quick Active Alerts List */}
          <div className="pt-3 border-t border-slate-800">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-slate-300">Active Critical Alerts</span>
              <button
                onClick={() => onNavigate('alerts')}
                className="text-[11px] text-cyan-400 hover:underline flex items-center gap-0.5"
              >
                View All <ArrowUpRight className="w-3 h-3" />
              </button>
            </div>

            {alerts.filter(a => a.status === 'ACTIVE').length === 0 ? (
              <p className="text-xs text-emerald-400/80 flex items-center gap-1.5 py-1">
                <CheckCircle2 className="w-3.5 h-3.5" /> No active infrastructure alerts.
              </p>
            ) : (
              <div className="space-y-1.5 max-h-36 overflow-y-auto pr-1">
                {alerts.filter(a => a.status === 'ACTIVE').slice(0, 3).map((a) => (
                  <div key={a.id} className="p-2 rounded bg-rose-500/10 border border-rose-500/20 text-xs">
                    <span className="font-bold text-rose-300 font-mono">{a.node_id}:</span>{' '}
                    <span className="text-slate-300">{a.title}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Main Nodes Telemetry Table (Section 26) */}
      <div className="glass-panel rounded-xl border border-slate-800 overflow-hidden">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-white tracking-wide">Containerized Virtual Nodes</h3>
            <p className="text-xs text-slate-400">Live multi-metric status across containerized infrastructure workloads</p>
          </div>
          <button
            onClick={refreshAll}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-dark-900/80 text-slate-400 uppercase text-[10px] font-mono tracking-wider border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Node / Container</th>
                <th className="py-3 px-3">Service</th>
                <th className="py-3 px-3">CPU</th>
                <th className="py-3 px-3">RAM</th>
                <th className="py-3 px-3">Response</th>
                <th className="py-3 px-3">Heartbeat</th>
                <th className="py-3 px-3">Health Score</th>
                <th className="py-3 px-3">Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {nodes.map((node) => {
                const score = node.health_score ?? 100;
                let scoreColor = 'text-emerald-400';
                if (score < 30) scoreColor = 'text-rose-400';
                else if (score < 50) scoreColor = 'text-orange-400';
                else if (score < 75) scoreColor = 'text-amber-400';

                return (
                  <tr key={node.node_id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-4 font-bold text-white flex items-center gap-2 font-mono">
                      <span className={`w-2 h-2 rounded-full ${node.heartbeat ? 'bg-emerald-400' : 'bg-rose-500'}`} />
                      <button
                        onClick={() => {
                          onSelectNode(node.node_id);
                          onNavigate('node-details');
                        }}
                        className="hover:text-cyan-400 hover:underline"
                      >
                        {node.node_id}
                      </button>
                    </td>
                    <td className="py-3 px-3 text-slate-300 font-sans uppercase font-semibold text-[11px]">
                      {node.service_name}
                    </td>
                    <td className="py-3 px-3 text-slate-200">
                      <div className="flex items-center gap-1.5">
                        <span className="w-12 text-right">{node.cpu_percent?.toFixed(1)}%</span>
                        <div className="w-12 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                          <div
                            className={`h-full ${node.cpu_percent > 85 ? 'bg-rose-500' : 'bg-cyan-500'}`}
                            style={{ width: `${Math.min(100, node.cpu_percent || 0)}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-3 text-slate-200">
                      <div className="flex items-center gap-1.5">
                        <span className="w-12 text-right">{node.memory_percent?.toFixed(1)}%</span>
                        <div className="w-12 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                          <div
                            className={`h-full ${node.memory_percent > 85 ? 'bg-rose-500' : 'bg-purple-500'}`}
                            style={{ width: `${Math.min(100, node.memory_percent || 0)}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-3 text-slate-300">
                      {node.response_time_ms ? `${Math.round(node.response_time_ms)}ms` : '—'}
                    </td>
                    <td className="py-3 px-3">
                      {node.heartbeat ? (
                        <span className="text-emerald-400 font-semibold text-[11px]">ALIVE</span>
                      ) : (
                        <span className="text-rose-400 font-semibold text-[11px] animate-pulse">LOST</span>
                      )}
                    </td>
                    <td className="py-3 px-3 font-bold">
                      <span className={scoreColor}>{Math.round(score)} / 100</span>
                    </td>
                    <td className="py-3 px-3">
                      <StatusBadge status={node.classification} />
                    </td>
                    <td className="py-3 px-4 text-right space-x-2">
                      <button
                        onClick={() => {
                          onSelectNode(node.node_id);
                          onNavigate('node-details');
                        }}
                        className="px-2.5 py-1 rounded bg-slate-800 hover:bg-cyan-600/30 text-slate-300 hover:text-cyan-300 border border-slate-700 transition-colors font-sans text-xs"
                      >
                        Inspect
                      </button>
                      {currentRole !== 'VIEWER' && (
                        <button
                          onClick={() => handleRestartClick(node.node_id)}
                          className="px-2.5 py-1 rounded bg-slate-800 hover:bg-rose-600/30 text-slate-300 hover:text-rose-300 border border-slate-700 transition-colors font-sans text-xs"
                        >
                          Restart
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      <ConfirmationModal
        isOpen={modalOpen}
        title={modalAction?.title}
        message={modalAction?.message}
        confirmText="Restart Container"
        danger={true}
        onConfirm={handleConfirmAction}
        onCancel={() => {
          setModalOpen(false);
          setModalAction(null);
        }}
      />
    </div>
  );
}
