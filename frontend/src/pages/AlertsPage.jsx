import React, { useState } from 'react';
import { AlertTriangle, CheckCircle2, ShieldAlert, Check, RefreshCw, Filter } from 'lucide-react';
import { api } from '../services/api';

export default function AlertsPage({ alerts = [], showNotification, refreshAll, currentRole }) {
  const [filterSeverity, setFilterSeverity] = useState('ALL');
  const [filterStatus, setFilterStatus] = useState('ALL');

  const filtered = alerts.filter((a) => {
    if (filterSeverity !== 'ALL' && a.severity !== filterSeverity) return false;
    if (filterStatus !== 'ALL' && a.status !== filterStatus) return false;
    return true;
  });

  const handleAcknowledge = async (id) => {
    try {
      await api.acknowledgeAlert(id);
      showNotification(`Alert ${id} acknowledged`, 'info');
      refreshAll();
    } catch (e) {
      showNotification(e.message, 'error');
    }
  };

  const handleResolve = async (id) => {
    try {
      await api.resolveAlert(id);
      showNotification(`Alert ${id} resolved`, 'success');
      refreshAll();
    } catch (e) {
      showNotification(e.message, 'error');
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white tracking-wide">Infrastructure Alert Center</h2>
          <p className="text-xs text-slate-400">
            Real-time feed of multi-factor threshold breaches, crashes, and degradation warnings
          </p>
        </div>

        {/* Filter Controls */}
        <div className="flex items-center gap-2">
          <select
            value={filterSeverity}
            onChange={(e) => setFilterSeverity(e.target.value)}
            className="bg-dark-900 border border-slate-800 text-xs text-slate-300 rounded-lg px-2.5 py-1.5 focus:outline-none"
          >
            <option value="ALL">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="WARNING">Warning</option>
            <option value="INFO">Info</option>
          </select>

          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="bg-dark-900 border border-slate-800 text-xs text-slate-300 rounded-lg px-2.5 py-1.5 focus:outline-none"
          >
            <option value="ALL">All Statuses</option>
            <option value="ACTIVE">Active</option>
            <option value="ACKNOWLEDGED">Acknowledged</option>
            <option value="RESOLVED">Resolved</option>
          </select>

          <button
            onClick={refreshAll}
            className="p-1.5 rounded-lg border border-slate-800 hover:border-slate-700 bg-dark-900 text-slate-400"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="glass-panel p-12 text-center text-slate-400 rounded-xl border border-slate-800">
          <CheckCircle2 className="w-10 h-10 mx-auto text-emerald-400 mb-2" />
          <h3 className="text-sm font-semibold text-white">No Matching Alerts</h3>
          <p className="text-xs text-slate-500 mt-1">Infrastructure conditions remain within normal baselines.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((alert) => {
            const isCritical = alert.severity === 'CRITICAL';
            const isActive = alert.status === 'ACTIVE';

            return (
              <div
                key={alert.id}
                className={`p-4 rounded-xl border transition-all ${
                  isActive
                    ? isCritical
                      ? 'bg-rose-500/10 border-rose-500/30'
                      : 'bg-amber-500/10 border-amber-500/30'
                    : 'bg-dark-900/60 border-slate-800'
                }`}
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2.5">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
                        isCritical ? 'bg-rose-500/20 text-rose-300' : 'bg-amber-500/20 text-amber-300'
                      }`}
                    >
                      {alert.severity}
                    </span>
                    <span className="font-mono font-bold text-xs text-white">{alert.node_id}</span>
                    <span className="text-xs font-semibold text-slate-200">{alert.title}</span>
                  </div>

                  <div className="flex items-center gap-2 text-xs">
                    <span className="text-slate-400 font-mono text-[11px]">
                      {new Date(alert.timestamp).toLocaleTimeString()}
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold ${
                        alert.status === 'ACTIVE'
                          ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                          : alert.status === 'ACKNOWLEDGED'
                          ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                          : 'bg-slate-700/30 text-slate-400'
                      }`}
                    >
                      {alert.status}
                    </span>
                  </div>
                </div>

                <p className="text-xs text-slate-300 mb-2">{alert.description}</p>

                {alert.evidence && alert.evidence.length > 0 && (
                  <div className="mb-3 text-[11px] font-mono text-slate-400 bg-dark-950/60 p-2 rounded border border-slate-800">
                    <span className="font-bold text-slate-300">Supporting Evidence: </span>
                    {alert.evidence.join(' | ')}
                  </div>
                )}

                <div className="flex items-center justify-between pt-2 border-t border-slate-800/80 text-xs">
                  <span className="text-slate-400">
                    Recommended Action:{' '}
                    <strong className="text-cyan-300 font-mono">{alert.recommended_action}</strong>
                  </span>

                  {currentRole !== 'VIEWER' && isActive && (
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleAcknowledge(alert.id)}
                        className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition-colors"
                      >
                        Acknowledge
                      </button>
                      <button
                        onClick={() => handleResolve(alert.id)}
                        className="px-2.5 py-1 rounded bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/30 text-xs font-semibold transition-colors"
                      >
                        Resolve
                      </button>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
