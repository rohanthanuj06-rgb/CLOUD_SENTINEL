import React, { useState, useEffect } from 'react';
import { TrendingUp, AlertCircle, ShieldAlert, Cpu, HardDrive, RefreshCw, Zap } from 'lucide-react';
import { api } from '../services/api';

export default function PredictionsPage() {
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPredictions();
  }, []);

  const loadPredictions = async () => {
    setLoading(true);
    try {
      const res = await api.getPredictions();
      setPredictions(res || []);
    } catch (e) {
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-white tracking-wide">Predictive Failure & Anomaly Intelligence</h2>
          <p className="text-xs text-slate-400">
            Machine Learning projections via Scikit-Learn Linear Regression and Multivariate Isolation Forest
          </p>
        </div>

        <button
          onClick={loadPredictions}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors border border-slate-700"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Recompute ML Models
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {predictions.map((p) => {
          const trend = p.trend || {};
          const anomaly = p.anomaly || {};
          const hasRisk = p.overall_risk_score > 30;

          return (
            <div
              key={p.node_id}
              className={`p-5 rounded-xl border transition-all ${
                hasRisk ? 'bg-slate-900 border-amber-500/40 shadow-lg shadow-amber-950/20' : 'glass-panel border-slate-800'
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="font-mono font-bold text-sm text-white">{p.node_id}</span>
                  <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                    {p.service_name}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <span
                    className={`text-xs font-mono font-bold px-2 py-0.5 rounded ${
                      p.overall_risk_score > 60
                        ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                        : p.overall_risk_score > 30
                        ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                        : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                    }`}
                  >
                    Risk: {p.overall_risk_score}%
                  </span>
                </div>
              </div>

              {/* Predicted Condition Banner */}
              <div className="p-3 bg-dark-950 rounded-lg border border-slate-800 mb-3 text-xs">
                <span className="text-[10px] font-mono uppercase text-slate-500 font-bold block">
                  Predicted Trajectory
                </span>
                <span className="font-mono font-bold text-cyan-300">{trend.predicted_condition}</span>
                <p className="text-slate-300 text-[11px] mt-1">{trend.explainability}</p>
              </div>

              {/* Time to Breach Projection */}
              <div className="grid grid-cols-2 gap-2 text-xs font-mono mb-3 p-2 bg-dark-900 rounded-lg border border-slate-800/80">
                <div>
                  <span className="text-slate-500 text-[10px] block">CPU Breach (90%)</span>
                  <span className="font-bold text-white">
                    {trend.time_to_cpu_breach_min ? `${trend.time_to_cpu_breach_min} mins` : 'Nominal'}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 text-[10px] block">RAM Breach (90%)</span>
                  <span className="font-bold text-white">
                    {trend.time_to_mem_breach_min ? `${trend.time_to_mem_breach_min} mins` : 'Nominal'}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500 text-[10px] block">CPU Slope</span>
                  <span className="text-slate-200">{trend.cpu_trend_slope}%/min</span>
                </div>
                <div>
                  <span className="text-slate-500 text-[10px] block">RAM Slope</span>
                  <span className="text-slate-200">{trend.memory_trend_slope}%/min</span>
                </div>
              </div>

              {/* Isolation Forest Anomaly Section */}
              <div className="space-y-1 text-xs mb-3">
                <div className="flex justify-between items-center">
                  <span className="text-slate-400 text-[11px]">Isolation Forest Anomaly Score:</span>
                  <span className={`font-mono font-bold ${anomaly.is_anomaly ? 'text-rose-400' : 'text-emerald-400'}`}>
                    {(anomaly.anomaly_score * 100).toFixed(0)}%
                  </span>
                </div>

                {anomaly.anomalous_features && anomaly.anomalous_features.length > 0 && (
                  <div className="text-[11px] font-mono text-amber-300 bg-amber-500/10 p-2 rounded border border-amber-500/20">
                    <span className="font-bold">Outliers: </span>
                    {anomaly.anomalous_features.map((f, i) => (
                      <span key={i}>
                        {f.feature} (z={f.z_score}){' '}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Recommended Preventive Action */}
              <div className="pt-2 border-t border-slate-800/80 text-xs">
                <span className="text-slate-400 text-[11px] block">Preventive Recommendation:</span>
                <p className="text-slate-200 font-semibold mt-0.5">{trend.recommended_action}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
