import React, { useState, useEffect } from 'react';
import { Settings, Sliders, Shield, Save, CheckCircle2, RotateCcw } from 'lucide-react';
import { api } from '../services/api';

export default function SettingsPage({ showNotification, currentRole }) {
  const [config, setConfig] = useState(null);
  const [weights, setWeights] = useState({
    cpu: 0.20,
    ram: 0.20,
    network: 0.10,
    response_time: 0.20,
    heartbeat: 0.20,
    application: 0.10,
  });
  const [thresholds, setThresholds] = useState({
    cpu_warning: 75.0,
    cpu_critical: 90.0,
    ram_warning: 75.0,
    ram_critical: 90.0,
    response_warning_ms: 400.0,
    response_critical_ms: 2000.0,
    idle_threshold: 5.0,
    idle_duration: 120.0,
  });
  const [autoRecovery, setAutoRecovery] = useState(true);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      const data = await api.getSystemConfig();
      setConfig(data);
      if (data.weights) setWeights(data.weights);
      if (data.thresholds) setThresholds(data.thresholds);
      if (data.auto_recovery_enabled != null) setAutoRecovery(data.auto_recovery_enabled);
    } catch (e) {}
  };

  const handleSaveWeights = async () => {
    if (currentRole !== 'ADMIN') {
      showNotification('Administrator privilege required to update weights.', 'error');
      return;
    }
    setLoading(true);
    try {
      await api.updateWeights({
        weight_cpu: weights.cpu,
        weight_ram: weights.ram,
        weight_network: weights.network,
        weight_response_time: weights.response_time,
        weight_heartbeat: weights.heartbeat,
        weight_application: weights.application,
      });
      showNotification('Health scoring weights updated and applied across monitoring engine.', 'success');
      loadConfig();
    } catch (err) {
      showNotification(err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveThresholds = async () => {
    if (currentRole !== 'ADMIN') {
      showNotification('Administrator privilege required to update thresholds.', 'error');
      return;
    }
    setLoading(true);
    try {
      await api.updateThresholds(thresholds);
      showNotification('State classification thresholds successfully saved.', 'success');
      loadConfig();
    } catch (err) {
      showNotification(err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleAutoRecovery = async () => {
    if (currentRole !== 'ADMIN') {
      showNotification('Administrator privilege required to toggle self-healing.', 'error');
      return;
    }
    try {
      const next = !autoRecovery;
      await api.toggleAutoRecovery(next);
      setAutoRecovery(next);
      showNotification(`Autonomous self-healing ${next ? 'ENABLED' : 'DISABLED'}`, 'info');
    } catch (err) {
      showNotification(err.message, 'error');
    }
  };

  const totalWeight = Object.values(weights).reduce((a, b) => a + b, 0);

  return (
    <div className="space-y-6 animate-fade-in max-w-5xl">
      <div>
        <h2 className="text-lg font-bold text-white tracking-wide">Platform Configuration & Thresholds</h2>
        <p className="text-xs text-slate-400">
          Fine-tune multi-factor health scoring weights, classification thresholds, and autonomous self-healing policies
        </p>
      </div>

      {/* Auto-Recovery Master Toggle */}
      <div className="glass-panel p-5 rounded-xl border border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={`p-2.5 rounded-lg ${autoRecovery ? 'bg-emerald-500/10 text-emerald-400' : 'bg-slate-800 text-slate-400'}`}>
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">Autonomous Self-Healing Engine</h3>
            <p className="text-xs text-slate-400">
              When enabled, high-confidence failures automatically trigger hierarchical recovery without manual intervention.
            </p>
          </div>
        </div>

        <button
          onClick={handleToggleAutoRecovery}
          className={`px-4 py-2 rounded-lg text-xs font-bold transition-all ${
            autoRecovery
              ? 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-md shadow-emerald-600/20'
              : 'bg-slate-800 hover:bg-slate-700 text-slate-300'
          }`}
        >
          {autoRecovery ? 'ENABLED' : 'DISABLED'}
        </button>
      </div>

      {/* Health Scoring Weights Card */}
      <div className="glass-panel p-5 rounded-xl border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sliders className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-bold text-white">Multi-Factor Health Scoring Weights</h3>
          </div>
          <span className={`text-xs font-mono font-bold ${Math.abs(totalWeight - 1.0) < 0.01 ? 'text-emerald-400' : 'text-amber-400'}`}>
            Sum: {(totalWeight * 100).toFixed(0)}%
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-xs">
          {Object.entries(weights).map(([k, v]) => (
            <div key={k} className="p-3 bg-dark-900 rounded-lg border border-slate-800 space-y-1">
              <div className="flex justify-between font-mono text-[11px]">
                <span className="uppercase text-slate-400">{k.replace('_', ' ')}</span>
                <span className="font-bold text-white">{Math.round(v * 100)}%</span>
              </div>
              <input
                type="range"
                min="0.0"
                max="0.5"
                step="0.05"
                value={v}
                onChange={(e) => setWeights({ ...weights, [k]: Number(e.target.value) })}
                className="w-full accent-cyan-500"
              />
            </div>
          ))}
        </div>

        {currentRole === 'ADMIN' && (
          <div className="pt-2 flex justify-end">
            <button
              onClick={handleSaveWeights}
              disabled={loading}
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-bold bg-cyan-600 hover:bg-cyan-500 text-white shadow-md shadow-cyan-600/20 transition-all"
            >
              <Save className="w-3.5 h-3.5" /> Save Weights
            </button>
          </div>
        )}
      </div>

      {/* State Classification Thresholds */}
      <div className="glass-panel p-5 rounded-xl border border-slate-800 space-y-4">
        <div className="flex items-center gap-2">
          <Settings className="w-4 h-4 text-cyan-400" />
          <h3 className="text-sm font-bold text-white">Intelligent Classification Thresholds</h3>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 text-xs font-mono">
          <div className="p-3 bg-dark-900 rounded-lg border border-slate-800">
            <span className="text-[10px] text-slate-500 block uppercase">CPU Warning (%)</span>
            <input
              type="number"
              value={thresholds.cpu_warning}
              onChange={(e) => setThresholds({ ...thresholds, cpu_warning: Number(e.target.value) })}
              className="mt-1 w-full bg-slate-800 border border-slate-700 rounded px-2 py-1 text-white font-bold"
            />
          </div>

          <div className="p-3 bg-dark-900 rounded-lg border border-slate-800">
            <span className="text-[10px] text-slate-500 block uppercase">CPU Critical (%)</span>
            <input
              type="number"
              value={thresholds.cpu_critical}
              onChange={(e) => setThresholds({ ...thresholds, cpu_critical: Number(e.target.value) })}
              className="mt-1 w-full bg-slate-800 border border-slate-700 rounded px-2 py-1 text-rose-400 font-bold"
            />
          </div>

          <div className="p-3 bg-dark-900 rounded-lg border border-slate-800">
            <span className="text-[10px] text-slate-500 block uppercase">RAM Warning (%)</span>
            <input
              type="number"
              value={thresholds.ram_warning}
              onChange={(e) => setThresholds({ ...thresholds, ram_warning: Number(e.target.value) })}
              className="mt-1 w-full bg-slate-800 border border-slate-700 rounded px-2 py-1 text-white font-bold"
            />
          </div>

          <div className="p-3 bg-dark-900 rounded-lg border border-slate-800">
            <span className="text-[10px] text-slate-500 block uppercase">RAM Critical (%)</span>
            <input
              type="number"
              value={thresholds.ram_critical}
              onChange={(e) => setThresholds({ ...thresholds, ram_critical: Number(e.target.value) })}
              className="mt-1 w-full bg-slate-800 border border-slate-700 rounded px-2 py-1 text-rose-400 font-bold"
            />
          </div>

          <div className="p-3 bg-dark-900 rounded-lg border border-slate-800">
            <span className="text-[10px] text-slate-500 block uppercase">Response Warning (ms)</span>
            <input
              type="number"
              value={thresholds.response_warning_ms}
              onChange={(e) => setThresholds({ ...thresholds, response_warning_ms: Number(e.target.value) })}
              className="mt-1 w-full bg-slate-800 border border-slate-700 rounded px-2 py-1 text-white font-bold"
            />
          </div>

          <div className="p-3 bg-dark-900 rounded-lg border border-slate-800">
            <span className="text-[10px] text-slate-500 block uppercase">Response Critical (ms)</span>
            <input
              type="number"
              value={thresholds.response_critical_ms}
              onChange={(e) => setThresholds({ ...thresholds, response_critical_ms: Number(e.target.value) })}
              className="mt-1 w-full bg-slate-800 border border-slate-700 rounded px-2 py-1 text-rose-400 font-bold"
            />
          </div>

          <div className="p-3 bg-dark-900 rounded-lg border border-slate-800">
            <span className="text-[10px] text-slate-500 block uppercase">Idle CPU Threshold (%)</span>
            <input
              type="number"
              value={thresholds.idle_threshold}
              onChange={(e) => setThresholds({ ...thresholds, idle_threshold: Number(e.target.value) })}
              className="mt-1 w-full bg-slate-800 border border-slate-700 rounded px-2 py-1 text-cyan-300 font-bold"
            />
          </div>

          <div className="p-3 bg-dark-900 rounded-lg border border-slate-800">
            <span className="text-[10px] text-slate-500 block uppercase">Zombie Duration (sec)</span>
            <input
              type="number"
              value={thresholds.idle_duration}
              onChange={(e) => setThresholds({ ...thresholds, idle_duration: Number(e.target.value) })}
              className="mt-1 w-full bg-slate-800 border border-slate-700 rounded px-2 py-1 text-purple-300 font-bold"
            />
          </div>
        </div>

        {currentRole === 'ADMIN' && (
          <div className="pt-2 flex justify-end">
            <button
              onClick={handleSaveThresholds}
              disabled={loading}
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-bold bg-cyan-600 hover:bg-cyan-500 text-white shadow-md shadow-cyan-600/20 transition-all"
            >
              <Save className="w-3.5 h-3.5" /> Save Thresholds
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
