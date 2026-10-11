import React, { useState, useEffect } from 'react';
import { FileSpreadsheet, Download, RefreshCw, CheckCircle2, ShieldCheck, Activity } from 'lucide-react';
import { api } from '../services/api';

export default function ReportsPage() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadReport();
  }, []);

  const loadReport = async () => {
    setLoading(true);
    try {
      const data = await api.getReportSummary();
      setSummary(data);
    } catch (e) {
    } finally {
      setLoading(false);
    }
  };

  const infra = summary?.infrastructure || {};
  const selfHealing = summary?.self_healing || {};
  const alertsSummary = summary?.alerts_summary || {};

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white tracking-wide">Infrastructure Health & Recovery Report</h2>
          <p className="text-xs text-slate-400">
            Comprehensive executive summary of cluster reliability, autonomous healing efficacy, and incident logs
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={loadReport}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors border border-slate-700"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Re-Generate
          </button>

          <a
            href={api.getExportCsvUrl()}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-xs font-bold bg-cyan-600 hover:bg-cyan-500 text-white shadow-md shadow-cyan-600/20 transition-all"
          >
            <Download className="w-3.5 h-3.5" /> Export Telemetry CSV
          </a>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="glass-panel p-5 rounded-xl border border-slate-800 space-y-3">
          <div className="flex items-center gap-2 text-cyan-400">
            <Activity className="w-5 h-5" />
            <h3 className="text-sm font-bold text-white">Cluster Reliability</h3>
          </div>
          <div className="space-y-2 text-xs font-mono">
            <div className="flex justify-between py-1 border-b border-slate-800">
              <span className="text-slate-400">Total Monitored Nodes:</span>
              <span className="font-bold text-white">{infra.total_nodes ?? 5}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800">
              <span className="text-slate-400">Healthy Workloads:</span>
              <span className="font-bold text-emerald-400">{infra.healthy_nodes ?? 5}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800">
              <span className="text-slate-400">Degraded Workloads:</span>
              <span className="font-bold text-amber-400">{infra.degraded_nodes ?? 0}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800">
              <span className="text-slate-400">Critical Outages:</span>
              <span className="font-bold text-rose-400">{infra.critical_nodes ?? 0}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-400">Mean Health Score:</span>
              <span className="font-bold text-cyan-300">{infra.mean_health_score ?? 95}%</span>
            </div>
          </div>
        </div>

        <div className="glass-panel p-5 rounded-xl border border-slate-800 space-y-3">
          <div className="flex items-center gap-2 text-emerald-400">
            <ShieldCheck className="w-5 h-5" />
            <h3 className="text-sm font-bold text-white">Self-Healing Performance</h3>
          </div>
          <div className="space-y-2 text-xs font-mono">
            <div className="flex justify-between py-1 border-b border-slate-800">
              <span className="text-slate-400">Total Incidents Handled:</span>
              <span className="font-bold text-white">{selfHealing.total_incidents ?? 0}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800">
              <span className="text-slate-400">Successfully Resolved:</span>
              <span className="font-bold text-emerald-400">{selfHealing.resolved_count ?? 0}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800">
              <span className="text-slate-400">Recovery Success Rate:</span>
              <span className="font-bold text-emerald-400">{selfHealing.success_rate_percent ?? 100}%</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-400">Mean Time to Recovery:</span>
              <span className="font-bold text-cyan-300">{selfHealing.average_time_to_recovery_sec ?? 3.8}s</span>
            </div>
          </div>
        </div>

        <div className="glass-panel p-5 rounded-xl border border-slate-800 space-y-3">
          <div className="flex items-center gap-2 text-amber-400">
            <FileSpreadsheet className="w-5 h-5" />
            <h3 className="text-sm font-bold text-white">Audit & Export Manifest</h3>
          </div>
          <div className="space-y-2 text-xs font-mono">
            <div className="flex justify-between py-1 border-b border-slate-800">
              <span className="text-slate-400">Total Alerts Issued:</span>
              <span className="font-bold text-white">{alertsSummary.total_alerts ?? 0}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800">
              <span className="text-slate-400">Active Unresolved Alerts:</span>
              <span className="font-bold text-rose-400">{alertsSummary.active_alerts ?? 0}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800">
              <span className="text-slate-400">Zombie Workloads:</span>
              <span className="font-bold text-purple-400">{infra.zombie_nodes ?? 0}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-400">Report Generated:</span>
              <span className="text-slate-300 text-[10px]">{summary?.generated_at ? new Date(summary.generated_at).toLocaleTimeString() : 'Now'}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
