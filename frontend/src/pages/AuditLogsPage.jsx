import React, { useState, useEffect } from 'react';
import { FileText, RefreshCw, Filter, ShieldCheck, CheckCircle2, AlertCircle } from 'lucide-react';
import { api } from '../services/api';

export default function AuditLogsPage() {
  const [logs, setLogs] = useState([]);
  const [filterNode, setFilterNode] = useState('');
  const [filterType, setFilterType] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadLogs();
  }, [filterNode, filterType]);

  const loadLogs = async () => {
    setLoading(true);
    try {
      const data = await api.getAuditLogs(100, filterNode || null, filterType || null);
      setLogs(data || []);
    } catch (e) {
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white tracking-wide">Immutable System Audit Trail</h2>
          <p className="text-xs text-slate-400">
            Chronological audit recording all autonomous self-healing, fault injection, configuration updates, and manual operator commands
          </p>
        </div>

        {/* Filter Controls */}
        <div className="flex items-center gap-2">
          <input
            type="text"
            placeholder="Filter by node (e.g. cs-node-web)"
            value={filterNode}
            onChange={(e) => setFilterNode(e.target.value)}
            className="bg-dark-900 border border-slate-800 text-xs text-slate-300 rounded-lg px-3 py-1.5 focus:outline-none placeholder-slate-500 font-mono"
          />

          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="bg-dark-900 border border-slate-800 text-xs text-slate-300 rounded-lg px-2.5 py-1.5 focus:outline-none"
          >
            <option value="">All Events</option>
            <option value="SELF_HEALING">Self Healing</option>
            <option value="FAULT_INJECTION">Fault Injection</option>
            <option value="MANUAL_RECOVERY">Manual Recovery</option>
            <option value="SYSTEM_CONFIG">System Config</option>
            <option value="ALERT_RESOLVED">Alert Resolved</option>
          </select>

          <button
            onClick={loadLogs}
            className="p-1.5 rounded-lg border border-slate-800 hover:border-slate-700 bg-dark-900 text-slate-400"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="glass-panel rounded-xl border border-slate-800 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-dark-900/80 text-slate-400 uppercase text-[10px] font-mono tracking-wider border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Timestamp</th>
                <th className="py-3 px-3">Actor</th>
                <th className="py-3 px-3">Role</th>
                <th className="py-3 px-3">Target Node</th>
                <th className="py-3 px-3">Event Type</th>
                <th className="py-3 px-4">Action Summary</th>
                <th className="py-3 px-3">Outcome</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {logs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500 font-sans">
                    No audit records match the current filter.
                  </td>
                </tr>
              ) : (
                logs.map((log) => {
                  const isSuccess = log.result === 'SUCCESS';
                  return (
                    <tr key={log.id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="py-3 px-4 text-slate-400 whitespace-nowrap">
                        {new Date(log.timestamp).toLocaleString()}
                      </td>
                      <td className="py-3 px-3 font-bold text-white font-mono">{log.actor}</td>
                      <td className="py-3 px-3">
                        <span className="px-1.5 py-0.5 rounded text-[10px] bg-slate-800 text-cyan-300 font-semibold">
                          {log.role}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-cyan-400 font-bold">{log.target_node || 'CLUSTER'}</td>
                      <td className="py-3 px-3 text-slate-300 font-sans font-semibold text-[11px]">
                        {log.event_type}
                      </td>
                      <td className="py-3 px-4 text-slate-200 font-sans">{log.action}</td>
                      <td className="py-3 px-3">
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                            isSuccess
                              ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                              : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                          }`}
                        >
                          {log.result}
                        </span>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
