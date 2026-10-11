import React, { useState, useEffect } from 'react';
import {
  Server,
  Activity,
  Cpu,
  HardDrive,
  Wifi,
  Clock,
  RotateCcw,
  RefreshCw,
  Terminal,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  FileText,
  Play
} from 'lucide-react';
import StatusBadge from '../components/StatusBadge';
import HealthGauge from '../components/HealthGauge';
import MetricHistoryChart from '../charts/MetricHistoryChart';
import HealthRadarChart from '../charts/HealthRadarChart';
import ConfirmationModal from '../components/ConfirmationModal';
import { api } from '../services/api';

export default function NodeDetailsPage({
  nodeId,
  detail = null,
  onRefresh,
  showNotification,
  currentRole
}) {
  const [metricsRange, setMetricsRange] = useState('15m');
  const [metricsData, setMetricsData] = useState([]);
  const [logs, setLogs] = useState([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalConfig, setModalConfig] = useState(null);
  const [loadingAction, setLoadingAction] = useState(false);

  const node = detail?.node;

  useEffect(() => {
    if (nodeId) {
      loadMetrics(nodeId, metricsRange);
      loadLogs(nodeId);
    }
  }, [nodeId, metricsRange]);

  const loadMetrics = async (nid, range) => {
    try {
      const res = await api.getNodeMetrics(nid, range);
      setMetricsData(res.metrics || []);
    } catch (e) {}
  };

  const loadLogs = async (nid) => {
    try {
      const res = await api.getNodeLogs(nid, 40);
      setLogs(res.logs || []);
    } catch (e) {}
  };

  const handleActionClick = (type) => {
    if (type === 'restart') {
      setModalConfig({
        type: 'restart',
        title: 'Restart Container',
        message: `Confirm cycling Docker container ${node?.container_name || nodeId}? The application and container will reboot and run self-verification.`,
        danger: true,
      });
    } else if (type === 'recreate') {
      setModalConfig({
        type: 'recreate',
        title: 'Recreate Container Fresh',
        message: `Confirm destroying and recreating container ${node?.container_name || nodeId} from base image? Temporary container files will be wiped.`,
        danger: true,
      });
    }
    setModalOpen(true);
  };

  const handleConfirmAction = async () => {
    if (!modalConfig) return;
    setLoadingAction(true);
    try {
      if (modalConfig.type === 'restart') {
        await api.restartNode(nodeId);
        showNotification(`Container restart command dispatched for ${nodeId}`, 'info');
      } else if (modalConfig.type === 'recreate') {
        await api.recreateNode(nodeId);
        showNotification(`Container recreation initiated for ${nodeId}`, 'info');
      }
      onRefresh();
      loadLogs(nodeId);
    } catch (err) {
      showNotification(`Action failed: ${err.message}`, 'error');
    } finally {
      setLoadingAction(false);
      setModalOpen(false);
      setModalConfig(null);
    }
  };

  if (!node) {
    return (
      <div className="glass-panel p-12 text-center text-slate-400">
        <Server className="w-12 h-12 mx-auto mb-3 text-slate-600 animate-pulse" />
        <h3 className="text-sm font-semibold">Loading node telemetry details...</h3>
      </div>
    );
  }

  const diagnosis = node.latest_diagnosis;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Node Header Banner */}
      <div className="glass-panel p-5 rounded-xl border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center text-cyan-400">
            <Server className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <h2 className="text-lg font-bold font-mono text-white">{node.node_id}</h2>
              <StatusBadge status={node.classification} />
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                Port {node.port}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Container Name: <strong className="text-slate-200 font-mono">{node.container_name}</strong> | Service: <strong className="text-slate-200 uppercase">{node.service_name}</strong> | ID: <span className="font-mono">{node.container_id || 'sim-01'}</span>
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              onRefresh();
              loadLogs(nodeId);
            }}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Probe Health
          </button>

          {currentRole !== 'VIEWER' && (
            <button
              onClick={() => handleActionClick('restart')}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-300 border border-cyan-500/30 transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5" /> Restart
            </button>
          )}

          {currentRole === 'ADMIN' && (
            <button
              onClick={() => handleActionClick('recreate')}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 border border-rose-500/30 transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5" /> Recreate
            </button>
          )}
        </div>
      </div>

      {/* Metrics Row: Gauges & Sub-scores */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="glass-panel p-4 rounded-xl border border-slate-800 flex flex-col items-center justify-center">
          <HealthGauge score={node.health_score} size={130} strokeWidth={10} label="Current Health Score" />
        </div>

        <div className="glass-panel p-4 rounded-xl border border-slate-800 space-y-2.5">
          <span className="text-[11px] font-mono font-bold uppercase text-slate-400">Resource Consumption</span>
          <div className="space-y-2">
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-300">CPU Usage</span>
                <span className="font-mono font-bold text-white">{node.cpu_percent?.toFixed(1)}%</span>
              </div>
              <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                <div className="h-full bg-cyan-400" style={{ width: `${Math.min(100, node.cpu_percent || 0)}%` }} />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-300">RAM Allocated</span>
                <span className="font-mono font-bold text-white">{node.memory_percent?.toFixed(1)}%</span>
              </div>
              <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                <div className="h-full bg-purple-400" style={{ width: `${Math.min(100, node.memory_percent || 0)}%` }} />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-300">Disk Volume</span>
                <span className="font-mono font-bold text-white">{node.disk_percent?.toFixed(1)}%</span>
              </div>
              <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                <div className="h-full bg-amber-400" style={{ width: `${Math.min(100, node.disk_percent || 0)}%` }} />
              </div>
            </div>
          </div>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-slate-800 space-y-2">
          <span className="text-[11px] font-mono font-bold uppercase text-slate-400">Network & Heartbeat</span>
          <div className="space-y-1.5 text-xs">
            <div className="flex justify-between py-1 border-b border-slate-800">
              <span className="text-slate-400">Heartbeat State:</span>
              <span className={`font-bold font-mono ${node.heartbeat ? 'text-emerald-400' : 'text-rose-400'}`}>
                {node.heartbeat ? 'ACTIVE' : 'LOST'}
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800">
              <span className="text-slate-400">Application Health:</span>
              <span className={`font-bold font-mono ${node.application_healthy ? 'text-emerald-400' : 'text-rose-400'}`}>
                {node.application_healthy ? 'HTTP 200 OK' : 'FAILED / 500'}
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800">
              <span className="text-slate-400">Response Latency:</span>
              <span className="font-mono font-bold text-white">{Math.round(node.response_time_ms || 0)} ms</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-400">Network Ingress:</span>
              <span className="font-mono text-cyan-300">{node.network_rx_rate_kb?.toFixed(1)} KB/s</span>
            </div>
          </div>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-slate-800 space-y-2">
          <span className="text-[11px] font-mono font-bold uppercase text-slate-400">Lifecycle & Restarts</span>
          <div className="space-y-1.5 text-xs">
            <div className="flex justify-between py-1 border-b border-slate-800">
              <span className="text-slate-400">Container Uptime:</span>
              <span className="font-mono text-white">{Math.round(node.uptime_seconds || 0)}s</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800">
              <span className="text-slate-400">Restart Cycles:</span>
              <span className="font-mono font-bold text-cyan-400">{node.restart_count}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800">
              <span className="text-slate-400">Missed Heartbeats:</span>
              <span className="font-mono font-bold text-amber-400">{node.missed_heartbeats}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-400">Active Faults:</span>
              <span className="font-mono text-rose-300">
                {node.active_faults?.length > 0 ? node.active_faults.join(', ') : 'None'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Root Cause Diagnostic Card */}
      {diagnosis && (
        <div className="p-4 rounded-xl bg-slate-900 border border-cyan-500/30">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-cyan-400" />
              <h3 className="text-sm font-bold text-white">Intelligent Diagnostic Evaluation</h3>
            </div>
            <span className="text-xs font-mono font-semibold px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/30">
              Confidence: {Math.round((diagnosis.confidence || 0) * 100)}%
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs mt-3">
            <div>
              <span className="text-slate-400 uppercase text-[10px] font-mono">Probable Root Cause</span>
              <p className="font-bold text-rose-300 font-mono mt-0.5">{diagnosis.cause}</p>
              <p className="text-slate-300 text-[11px] mt-1">{diagnosis.summary}</p>
            </div>

            <div>
              <span className="text-slate-400 uppercase text-[10px] font-mono">Diagnostic Evidence</span>
              <ul className="list-disc list-inside text-slate-300 mt-1 space-y-0.5 font-mono text-[11px]">
                {diagnosis.evidence?.map((ev, i) => (
                  <li key={i}>{ev}</li>
                ))}
              </ul>
            </div>

            <div>
              <span className="text-slate-400 uppercase text-[10px] font-mono">Recommended Self-Healing</span>
              <p className="font-bold text-emerald-400 font-mono mt-0.5">{diagnosis.recommended_action}</p>
            </div>
          </div>
        </div>
      )}

      {/* Time Series History & Radar Decomposition */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <MetricHistoryChart
            data={metricsData}
            title={`${node.node_id} Telemetry History`}
            currentRange={metricsRange}
            onRangeChange={setMetricsRange}
          />
        </div>
        <div>
          <HealthRadarChart nodeName={node.node_id} />
        </div>
      </div>

      {/* Container Logs Section */}
      <div className="glass-panel p-4 rounded-xl border border-slate-800">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-bold text-white tracking-wide">Live Container Logs</h3>
          </div>
          <button
            onClick={() => loadLogs(nodeId)}
            className="text-[11px] text-cyan-400 hover:underline flex items-center gap-1 font-mono"
          >
            <RefreshCw className="w-3 h-3" /> Refresh Logs
          </button>
        </div>

        <div className="p-3 bg-dark-950 rounded-lg border border-slate-800/80 font-mono text-xs text-slate-300 max-h-56 overflow-y-auto space-y-1">
          {logs.length === 0 ? (
            <p className="text-slate-500">No log entries available.</p>
          ) : (
            logs.map((line, idx) => (
              <div key={idx} className="whitespace-pre-wrap leading-relaxed">
                {line}
              </div>
            ))
          )}
        </div>
      </div>

      <ConfirmationModal
        isOpen={modalOpen}
        title={modalConfig?.title}
        message={modalConfig?.message}
        confirmText="Execute"
        danger={modalConfig?.danger}
        onConfirm={handleConfirmAction}
        onCancel={() => {
          setModalOpen(false);
          setModalConfig(null);
        }}
      />
    </div>
  );
}
