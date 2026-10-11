import React, { useState } from 'react';
import {
  Flame,
  Cpu,
  HardDrive,
  Wifi,
  PowerOff,
  AlertTriangle,
  RotateCcw,
  CheckCircle2,
  ShieldCheck,
  Server
} from 'lucide-react';
import ConfirmationModal from '../components/ConfirmationModal';
import { api } from '../services/api';

export default function FaultInjectionPage({ nodes = [], showNotification, refreshAll, currentRole }) {
  const [selectedNodeId, setSelectedNodeId] = useState('cs-node-web');
  const [duration, setDuration] = useState(45);
  const [cpuIntensity, setCpuIntensity] = useState(0.95);
  const [memoryMb, setMemoryMb] = useState(350);
  const [latencyMs, setLatencyMs] = useState(2500);
  const [diskMb, setDiskMb] = useState(150);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalConfig, setModalConfig] = useState(null);

  const targetNode = nodes.find((n) => n.node_id === selectedNodeId);

  const handleTriggerFault = async (type) => {
    if (currentRole === 'VIEWER') {
      showNotification('Viewers lack privilege to trigger fault injection.', 'error');
      return;
    }

    setLoading(true);
    try {
      if (type === 'cpu') {
        await api.injectCpuFault({ node_id: selectedNodeId, duration, intensity: cpuIntensity });
        showNotification(`Injected CPU stress on ${selectedNodeId} (${Math.round(cpuIntensity * 100)}% load)`, 'warning');
      } else if (type === 'memory') {
        await api.injectMemoryFault({ node_id: selectedNodeId, duration, mb: memoryMb });
        showNotification(`Injected Memory leak on ${selectedNodeId} (${memoryMb}MB)`, 'warning');
      } else if (type === 'application') {
        await api.injectAppFailure(selectedNodeId);
        showNotification(`Injected Application Failure on ${selectedNodeId} (/health 500)`, 'warning');
      } else if (type === 'container') {
        await api.injectContainerStop(selectedNodeId);
        showNotification(`Stopped container on ${selectedNodeId}`, 'error');
      } else if (type === 'network') {
        await api.injectNetworkFault({ node_id: selectedNodeId, duration, delay_ms: latencyMs });
        showNotification(`Injected network latency (+${latencyMs}ms) on ${selectedNodeId}`, 'warning');
      } else if (type === 'disk') {
        await api.injectDiskFault({ node_id: selectedNodeId, duration, size_mb: diskMb });
        showNotification(`Injected disk pressure (${diskMb}MB) on ${selectedNodeId}`, 'warning');
      }
      refreshAll();
    } catch (err) {
      showNotification(`Fault injection error: ${err.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleResetClick = () => {
    setModalConfig({
      title: 'Confirm Reset All Faults',
      message: 'This will purge all injected CPU stress threads, free leaked memory, remove temporary disk files, and restart stopped demo containers.',
      action: async () => {
        setLoading(true);
        try {
          await api.resetFaults();
          showNotification('All active faults successfully cleared and baseline restored.', 'success');
          refreshAll();
        } catch (err) {
          showNotification(`Reset failed: ${err.message}`, 'error');
        } finally {
          setLoading(false);
          setModalOpen(false);
        }
      },
    });
    setModalOpen(true);
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Top Warning Banner (Section 47) */}
      <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-amber-500/20 text-amber-400">
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-amber-300">Isolated Fault Injection Testbed</h3>
            <p className="text-xs text-slate-300 mt-0.5">
              Safety Boundary: Fault injection is strictly restricted to designated demo containers. Host OS is protected.
            </p>
          </div>
        </div>

        <button
          onClick={handleResetClick}
          className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white shadow-md shadow-emerald-600/20 transition-all"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          RESET ALL FAULTS
        </button>
      </div>

      {/* Target Selector & Current Status */}
      <div className="glass-panel p-5 rounded-xl border border-slate-800 grid grid-cols-1 md:grid-cols-3 gap-6">
        <div>
          <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
            Select Target Node
          </label>
          <select
            value={selectedNodeId}
            onChange={(e) => setSelectedNodeId(e.target.value)}
            className="w-full bg-dark-900 border border-slate-700 rounded-lg px-3 py-2 text-sm font-mono text-cyan-300 focus:outline-none focus:border-cyan-500"
          >
            {nodes.map((n) => (
              <option key={n.node_id} value={n.node_id}>
                {n.node_id} ({n.service_name.toUpperCase()}) - Score: {Math.round(n.health_score)}%
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
            Fault Duration (seconds)
          </label>
          <div className="flex items-center gap-3">
            <input
              type="range"
              min="10"
              max="180"
              step="5"
              value={duration}
              onChange={(e) => setDuration(Number(e.target.value))}
              className="w-full accent-cyan-500"
            />
            <span className="font-mono text-xs font-bold text-white w-12 text-right">{duration}s</span>
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
            Target Live State
          </label>
          <div className="flex items-center gap-3 p-2 bg-dark-900 rounded-lg border border-slate-800 text-xs">
            <Server className="w-4 h-4 text-cyan-400" />
            <span className="font-mono text-white font-bold">{selectedNodeId}</span>
            <span className="text-slate-400">•</span>
            <span className={`font-mono font-bold ${targetNode?.health_score < 50 ? 'text-rose-400' : 'text-emerald-400'}`}>
              {Math.round(targetNode?.health_score || 100)}%
            </span>
            <span className="text-slate-400">•</span>
            <span className="text-slate-300">
              {targetNode?.active_faults?.length > 0 ? targetNode.active_faults.join(', ') : 'Normal'}
            </span>
          </div>
        </div>
      </div>

      {/* Fault Injection Buttons Grid (Section 17) */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {/* 1. CPU Stress */}
        <div className="glass-panel p-5 rounded-xl border border-slate-800 hover:border-slate-700 transition-all space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Cpu className="w-5 h-5 text-amber-400" />
              <h4 className="text-sm font-bold text-white">CPU Stress</h4>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/30">
              Compute Overload
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Spawns background SHA256 hashing threads inside the container to force 95%+ CPU saturation.
          </p>
          <div className="space-y-1 text-xs">
            <div className="flex justify-between text-slate-400">
              <span>Intensity:</span>
              <span className="font-mono text-white font-bold">{Math.round(cpuIntensity * 100)}%</span>
            </div>
            <input
              type="range"
              min="0.5"
              max="1.0"
              step="0.05"
              value={cpuIntensity}
              onChange={(e) => setCpuIntensity(Number(e.target.value))}
              className="w-full accent-amber-500"
            />
          </div>
          <button
            onClick={() => handleTriggerFault('cpu')}
            disabled={loading}
            className="w-full py-2 rounded-lg text-xs font-bold bg-amber-600/20 hover:bg-amber-600/30 text-amber-300 border border-amber-500/40 transition-colors"
          >
            INJECT CPU STRESS
          </button>
        </div>

        {/* 2. Memory Stress */}
        <div className="glass-panel p-5 rounded-xl border border-slate-800 hover:border-slate-700 transition-all space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <HardDrive className="w-5 h-5 text-purple-400" />
              <h4 className="text-sm font-bold text-white">Memory Leak</h4>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-500/10 text-purple-400 border border-purple-500/30">
              RAM Pressure
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Allocates controlled bytearray buffers inside the container process to push cgroup RAM limits.
          </p>
          <div className="space-y-1 text-xs">
            <div className="flex justify-between text-slate-400">
              <span>Allocation Buffer:</span>
              <span className="font-mono text-white font-bold">{memoryMb} MB</span>
            </div>
            <input
              type="range"
              min="100"
              max="600"
              step="50"
              value={memoryMb}
              onChange={(e) => setMemoryMb(Number(e.target.value))}
              className="w-full accent-purple-500"
            />
          </div>
          <button
            onClick={() => handleTriggerFault('memory')}
            disabled={loading}
            className="w-full py-2 rounded-lg text-xs font-bold bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 border border-purple-500/40 transition-colors"
          >
            INJECT MEMORY PRESSURE
          </button>
        </div>

        {/* 3. Application Failure */}
        <div className="glass-panel p-5 rounded-xl border border-slate-800 hover:border-slate-700 transition-all space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Flame className="w-5 h-5 text-rose-400" />
              <h4 className="text-sm font-bold text-white">Application Crash</h4>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/30">
              HTTP 500 Crash
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Container remains running, but internal application crashes. Forces /health endpoint to return HTTP 500.
          </p>
          <div className="h-[42px] flex items-center text-xs text-slate-500 font-mono">
            Tests container alive + app dead distinction.
          </div>
          <button
            onClick={() => handleTriggerFault('application')}
            disabled={loading}
            className="w-full py-2 rounded-lg text-xs font-bold bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 border border-rose-500/40 transition-colors"
          >
            CRASH APPLICATION LAYER
          </button>
        </div>

        {/* 4. Container Stop */}
        <div className="glass-panel p-5 rounded-xl border border-slate-800 hover:border-slate-700 transition-all space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <PowerOff className="w-5 h-5 text-red-500" />
              <h4 className="text-sm font-bold text-white">Container Failure</h4>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-red-500/10 text-red-400 border border-red-500/30">
              Process Death
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Terminates the target container, causing immediate heartbeat loss and socket probe drops.
          </p>
          <div className="h-[42px] flex items-center text-xs text-slate-500 font-mono">
            Triggers heartbeat loss & self-healing restart.
          </div>
          <button
            onClick={() => handleTriggerFault('container')}
            disabled={loading}
            className="w-full py-2 rounded-lg text-xs font-bold bg-red-600/20 hover:bg-red-600/30 text-red-300 border border-red-500/40 transition-colors"
          >
            TERMINATE CONTAINER
          </button>
        </div>

        {/* 5. Network Latency */}
        <div className="glass-panel p-5 rounded-xl border border-slate-800 hover:border-slate-700 transition-all space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Wifi className="w-5 h-5 text-cyan-400" />
              <h4 className="text-sm font-bold text-white">Network Degradation</h4>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
              Latency Injection
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Injects artificial delays into all HTTP and heartbeat response handlers to simulate congestion.
          </p>
          <div className="space-y-1 text-xs">
            <div className="flex justify-between text-slate-400">
              <span>Artificial Delay:</span>
              <span className="font-mono text-white font-bold">+{latencyMs} ms</span>
            </div>
            <input
              type="range"
              min="500"
              max="4000"
              step="250"
              value={latencyMs}
              onChange={(e) => setLatencyMs(Number(e.target.value))}
              className="w-full accent-cyan-500"
            />
          </div>
          <button
            onClick={() => handleTriggerFault('network')}
            disabled={loading}
            className="w-full py-2 rounded-lg text-xs font-bold bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-300 border border-cyan-500/40 transition-colors"
          >
            INJECT NETWORK DELAY
          </button>
        </div>

        {/* 6. Disk Pressure */}
        <div className="glass-panel p-5 rounded-xl border border-slate-800 hover:border-slate-700 transition-all space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <HardDrive className="w-5 h-5 text-amber-500" />
              <h4 className="text-sm font-bold text-white">Disk Pressure</h4>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/30">
              Storage Stress
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Writes temporary buffer payload files inside the container temporary folder and auto-cleans.
          </p>
          <div className="space-y-1 text-xs">
            <div className="flex justify-between text-slate-400">
              <span>Temporary Buffer:</span>
              <span className="font-mono text-white font-bold">{diskMb} MB</span>
            </div>
            <input
              type="range"
              min="50"
              max="300"
              step="25"
              value={diskMb}
              onChange={(e) => setDiskMb(Number(e.target.value))}
              className="w-full accent-amber-500"
            />
          </div>
          <button
            onClick={() => handleTriggerFault('disk')}
            disabled={loading}
            className="w-full py-2 rounded-lg text-xs font-bold bg-amber-600/20 hover:bg-amber-600/30 text-amber-300 border border-amber-500/40 transition-colors"
          >
            INJECT DISK PRESSURE
          </button>
        </div>
      </div>

      <ConfirmationModal
        isOpen={modalOpen}
        title={modalConfig?.title}
        message={modalConfig?.message}
        confirmText="Confirm Reset"
        danger={false}
        onConfirm={modalConfig?.action}
        onCancel={() => setModalOpen(false)}
      />
    </div>
  );
}
