import React, { useState } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from 'recharts';

export default function MetricHistoryChart({ data = [], title = 'Telemetry History', onRangeChange, currentRange = '15m' }) {
  const [activeMetric, setActiveMetric] = useState('all');

  // Format timestamp for x-axis
  const formattedData = data.map((d) => {
    let timeStr = d.timestamp;
    try {
      const dt = new Date(d.timestamp);
      timeStr = dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch (e) {
      // ignore
    }
    return {
      ...d,
      formattedTime: timeStr,
    };
  });

  return (
    <div className="glass-panel p-4 rounded-xl border border-slate-800">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div>
          <h3 className="text-sm font-bold text-white tracking-wide">{title}</h3>
          <p className="text-xs text-slate-400">Time-series metric telemetry stream</p>
        </div>

        <div className="flex items-center gap-2">
          {/* Range selector */}
          <div className="flex items-center bg-dark-900 border border-slate-800 rounded-lg p-0.5">
            {['5m', '15m', '1h', '6h', '24h'].map((r) => (
              <button
                key={r}
                onClick={() => onRangeChange && onRangeChange(r)}
                className={`px-2 py-1 rounded text-xs font-mono font-medium transition-colors ${
                  currentRange === r
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {r}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="w-full h-[280px]">
        {formattedData.length === 0 ? (
          <div className="w-full h-full flex items-center justify-center text-xs text-slate-500">
            Awaiting telemetry data stream...
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={formattedData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" opacity={0.5} />
              <XAxis dataKey="formattedTime" stroke="#64748b" fontSize={10} tickLine={false} />
              <YAxis stroke="#64748b" fontSize={10} domain={[0, 100]} tickLine={false} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0f172a',
                  borderColor: '#334155',
                  borderRadius: '8px',
                  fontSize: '12px',
                }}
              />
              <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
              <Line
                type="monotone"
                dataKey="health_score"
                name="Health Score (%)"
                stroke="#10b981"
                strokeWidth={2}
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="cpu"
                name="CPU (%)"
                stroke="#38bdf8"
                strokeWidth={1.5}
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="memory"
                name="RAM (%)"
                stroke="#a855f7"
                strokeWidth={1.5}
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="response_time"
                name="Latency (ms)"
                stroke="#f59e0b"
                strokeWidth={1.5}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
