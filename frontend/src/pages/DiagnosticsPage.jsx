import React, { useState, useEffect } from 'react';
import { Stethoscope, ShieldAlert, CheckCircle2, RefreshCw, ArrowRight } from 'lucide-react';
import { api } from '../services/api';
import StatusBadge from '../components/StatusBadge';

export default function DiagnosticsPage({ onSelectNode, onNavigate }) {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDiagnostics();
  }, []);

  const loadDiagnostics = async () => {
    setLoading(true);
    try {
      const res = await api.getDiagnostics();
      setReports(res || []);
    } catch (e) {
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white tracking-wide">Intelligent Root-Cause Diagnostic Engine</h2>
          <p className="text-xs text-slate-400">
            Rule-based expert diagnostic model distinguishing infrastructure failures, resource leaks, and application crashes
          </p>
        </div>

        <button
          onClick={loadDiagnostics}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors border border-slate-700"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Re-Evaluate Infrastructure
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {reports.map((rep) => {
          const diag = rep.diagnosis || {};
          const isHealthy = diag.cause === 'HEALTHY_NORMAL';

          return (
            <div
              key={rep.node_id}
              className={`p-5 rounded-xl border transition-all ${
                isHealthy ? 'glass-panel border-slate-800' : 'bg-slate-900 border-cyan-500/40 shadow-lg shadow-cyan-950/20'
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2.5">
                  <span className="font-mono font-bold text-sm text-white">{rep.node_id}</span>
                  <StatusBadge status={rep.classification} />
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono font-semibold px-2 py-0.5 rounded bg-dark-900 text-cyan-300 border border-slate-700">
                    Confidence: {Math.round((diag.confidence || 0.95) * 100)}%
                  </span>
                  <span className="text-xs font-mono font-bold text-white">
                    Score: {Math.round(rep.health_score)}%
                  </span>
                </div>
              </div>

              {/* Root Cause Title */}
              <div className="p-3 bg-dark-950 rounded-lg border border-slate-800/80 mb-3">
                <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-500 block">
                  Diagnosed Primary Condition
                </span>
                <span className={`text-sm font-bold font-mono ${isHealthy ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {diag.cause}
                </span>
                <p className="text-xs text-slate-300 mt-1">{diag.summary}</p>
              </div>

              {/* Evidence Section */}
              <div className="space-y-1.5 mb-4">
                <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400">
                  Supporting Telemetric Evidence
                </span>
                <ul className="space-y-1 text-xs font-mono text-slate-300">
                  {diag.evidence?.map((ev, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 mt-1.5 shrink-0" />
                      <span>{ev}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Recommended Action & Trigger */}
              <div className="flex items-center justify-between pt-3 border-t border-slate-800/80 text-xs">
                <div>
                  <span className="text-slate-400 text-[11px] block">Recommended Action:</span>
                  <strong className="text-cyan-300 font-mono">{diag.recommended_action}</strong>
                </div>

                <button
                  onClick={() => {
                    onSelectNode(rep.node_id);
                    onNavigate('node-details');
                  }}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors text-xs font-semibold flex items-center gap-1"
                >
                  Inspect Node <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
