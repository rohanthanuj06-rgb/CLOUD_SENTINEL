import React, { useState } from 'react';
import {
  ShieldCheck,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  ArrowRight,
  RotateCcw,
  RefreshCw,
  ThumbsUp,
  ThumbsDown
} from 'lucide-react';
import StatCard from '../components/StatCard';
import RecoveryTimelineChart from '../charts/RecoveryTimelineChart';
import { api } from '../services/api';

export default function RecoveryCenterPage({ recoveries = [], showNotification, refreshAll, currentRole }) {
  const [approvingId, setApprovingId] = useState(null);

  const total = recoveries.length;
  const successful = recoveries.filter((r) => r.result === 'SUCCESS').length;
  const failed = recoveries.filter((r) => r.result === 'FAILED').length;
  const escalated = recoveries.filter((r) => r.result === 'ESCALATED').length;
  const inProgress = recoveries.filter((r) => r.result === 'IN_PROGRESS').length;
  const pendingApproval = recoveries.filter((r) => r.result === 'REQUIRES_APPROVAL');

  const rate = total > 0 ? ((successful / total) * 100).toFixed(1) : '100.0';

  const handleApprove = async (recoveryId, approved) => {
    try {
      setApprovingId(recoveryId);
      await api.approveRecovery(recoveryId, approved, approved ? 'Approved by Admin' : 'Rejected');
      showNotification(
        approved ? `Approved recovery ${recoveryId}` : `Rejected recovery ${recoveryId}`,
        approved ? 'success' : 'info'
      );
      refreshAll();
    } catch (err) {
      showNotification(`Action failed: ${err.message}`, 'error');
    } finally {
      setApprovingId(null);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white tracking-wide">Self-Healing Recovery Operations</h2>
          <p className="text-xs text-slate-400">
            Hierarchical autonomous recovery engine with multi-tier escalation and health verification
          </p>
        </div>

        <button
          onClick={refreshAll}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors border border-slate-700"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Refresh Timeline
        </button>
      </div>

      {/* KPI Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        <StatCard title="Total Actions" value={total} icon={ShieldCheck} color="cyan" />
        <StatCard title="Successful" value={successful} icon={CheckCircle2} color="emerald" />
        <StatCard title="Failed" value={failed} icon={XCircle} color="rose" />
        <StatCard title="Admin Escalated" value={escalated} icon={AlertTriangle} color="amber" />
        <StatCard title="Success Rate" value={`${rate}%`} icon={ShieldCheck} color="emerald" />
      </div>

      {/* Pending Approvals Section (Low Confidence Gate) */}
      {pendingApproval.length > 0 && (
        <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 space-y-3">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-400" />
            <h3 className="text-sm font-bold text-amber-300">
              Low-Confidence Recovery Actions Pending Administrator Approval
            </h3>
          </div>
          <p className="text-xs text-slate-300">
            The self-healing policy suspended these actions because root-cause diagnostic confidence fell below the safety threshold.
          </p>

          <div className="space-y-2">
            {pendingApproval.map((rec) => (
              <div
                key={rec.recovery_id}
                className="p-3 bg-dark-900 rounded-lg border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs"
              >
                <div>
                  <span className="font-bold font-mono text-cyan-300">{rec.node_id}</span>
                  <span className="text-slate-400"> — {rec.failure_type}</span>
                  <span className="ml-2 font-mono text-amber-400 font-semibold">
                    (Confidence: {Math.round(rec.confidence_score * 100)}%)
                  </span>
                </div>

                {currentRole === 'ADMIN' ? (
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleApprove(rec.recovery_id, true)}
                      disabled={approvingId === rec.recovery_id}
                      className="flex items-center gap-1 px-3 py-1 rounded bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/40 font-semibold"
                    >
                      <ThumbsUp className="w-3.5 h-3.5" /> Approve Self-Healing
                    </button>
                    <button
                      onClick={() => handleApprove(rec.recovery_id, false)}
                      disabled={approvingId === rec.recovery_id}
                      className="flex items-center gap-1 px-3 py-1 rounded bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 border border-rose-500/40 font-semibold"
                    >
                      <ThumbsDown className="w-3.5 h-3.5" /> Reject
                    </button>
                  </div>
                ) : (
                  <span className="text-[11px] font-mono text-amber-400">
                    Administrator privilege required to approve
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Hierarchical Explanation Card */}
      <div className="glass-panel p-4 rounded-xl border border-slate-800">
        <h3 className="text-xs font-mono font-bold uppercase text-slate-400 tracking-wider mb-2">
          Hierarchical Self-Healing Progression
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-5 gap-2 text-xs">
          <div className="p-2.5 rounded bg-dark-900 border border-slate-800">
            <span className="text-[10px] font-mono text-cyan-400 font-bold block">TIER 1</span>
            <strong className="text-white text-[11px]">Restart Application</strong>
            <p className="text-[10px] text-slate-400 mt-1">Resets process without recycling container</p>
          </div>
          <div className="p-2.5 rounded bg-dark-900 border border-slate-800">
            <span className="text-[10px] font-mono text-cyan-400 font-bold block">TIER 2</span>
            <strong className="text-white text-[11px]">Restart Container</strong>
            <p className="text-[10px] text-slate-400 mt-1">Docker daemon container restart</p>
          </div>
          <div className="p-2.5 rounded bg-dark-900 border border-slate-800">
            <span className="text-[10px] font-mono text-cyan-400 font-bold block">TIER 3</span>
            <strong className="text-white text-[11px]">Recreate Container</strong>
            <p className="text-[10px] text-slate-400 mt-1">Purge layer & rebuild fresh from image</p>
          </div>
          <div className="p-2.5 rounded bg-dark-900 border border-slate-800">
            <span className="text-[10px] font-mono text-cyan-400 font-bold block">TIER 4</span>
            <strong className="text-white text-[11px]">Failover Workload</strong>
            <p className="text-[10px] text-slate-400 mt-1">Redirect traffic to healthy replica</p>
          </div>
          <div className="p-2.5 rounded bg-dark-900 border border-slate-800">
            <span className="text-[10px] font-mono text-rose-400 font-bold block">TIER 5</span>
            <strong className="text-white text-[11px]">Escalate to Admin</strong>
            <p className="text-[10px] text-slate-400 mt-1">Critical alert & manual intervention</p>
          </div>
        </div>
      </div>

      {/* Recovery Timeline Chart Component */}
      <RecoveryTimelineChart recoveries={recoveries} />
    </div>
  );
}
