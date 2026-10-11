import React from 'react';
import { ShieldCheck, AlertCircle, ArrowRight, Clock, CheckCircle2, XCircle } from 'lucide-react';

export default function RecoveryTimelineChart({ recoveries = [] }) {
  if (recoveries.length === 0) {
    return (
      <div className="glass-panel p-6 rounded-xl border border-slate-800 text-center text-xs text-slate-500">
        No self-healing events recorded in this session.
      </div>
    );
  }

  return (
    <div className="glass-panel p-5 rounded-xl border border-slate-800">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-bold text-white tracking-wide">Self-Recovery Incident Timeline</h3>
          <p className="text-xs text-slate-400">Hierarchical recovery executions and before/after verification logs</p>
        </div>
        <span className="text-xs font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
          {recoveries.length} Incidents
        </span>
      </div>

      <div className="space-y-4">
        {recoveries.slice(0, 10).map((rec, index) => {
          const isSuccess = rec.result === 'SUCCESS';
          const isEscalated = rec.result === 'ESCALATED';
          const isPending = rec.result === 'IN_PROGRESS' || rec.result === 'REQUIRES_APPROVAL';

          let timeStr = rec.started_at;
          try {
            timeStr = new Date(rec.started_at).toLocaleTimeString();
          } catch (e) {}

          return (
            <div
              key={rec.recovery_id || index}
              className="p-3.5 rounded-lg bg-dark-900 border border-slate-800 hover:border-slate-700 transition-colors"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                <div className="flex items-center gap-2">
                  {isSuccess ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                  ) : isEscalated ? (
                    <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
                  ) : (
                    <Clock className="w-4 h-4 text-amber-400 shrink-0 animate-spin" />
                  )}
                  <span className="text-xs font-bold font-mono text-cyan-300">{rec.node_id}</span>
                  <span className="text-[11px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-semibold">
                    {rec.failure_type}
                  </span>
                </div>

                <div className="flex items-center gap-3 text-xs">
                  <span className="text-slate-400 font-mono">{timeStr}</span>
                  <span
                    className={`px-2 py-0.5 rounded-full text-[10px] font-bold font-mono ${
                      isSuccess
                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                        : isEscalated
                        ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                        : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                    }`}
                  >
                    {rec.result}
                  </span>
                </div>
              </div>

              {/* Action Tier & Confidence */}
              <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400 mb-2">
                <span>
                  Tier: <strong className="text-slate-200">{rec.action_name}</strong>
                </span>
                <span>•</span>
                <span>
                  Confidence: <strong className="text-cyan-300">{Math.round((rec.confidence_score || 0) * 100)}%</strong>
                </span>
                <span>•</span>
                <span className="flex items-center gap-1">
                  Health:{' '}
                  <span className="text-rose-400 font-mono font-bold">{Math.round(rec.health_before)}%</span>
                  <ArrowRight className="w-3 h-3 text-slate-500 inline" />
                  <span className="text-emerald-400 font-mono font-bold">
                    {rec.health_after != null ? `${Math.round(rec.health_after)}%` : 'Verifying...'}
                  </span>
                </span>
              </div>

              {/* Step Logs Accordion/Snippet */}
              {rec.steps_log && rec.steps_log.length > 0 && (
                <div className="pt-2 border-t border-slate-800/80 text-[11px] font-mono text-slate-400 space-y-1">
                  {rec.steps_log.map((step, sIdx) => (
                    <div key={sIdx} className="flex items-center gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-slate-600" />
                      <span className="text-slate-300">{step.step}:</span>
                      <span className="text-slate-400">{step.detail || step.status}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
