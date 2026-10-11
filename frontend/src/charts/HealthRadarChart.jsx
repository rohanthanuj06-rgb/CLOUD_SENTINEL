import React from 'react';
import {
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  Tooltip,
} from 'recharts';

export default function HealthRadarChart({ subScores = {}, nodeName = 'Node' }) {
  const radarData = [
    { subject: 'CPU', score: subScores.cpu_score ?? 90, fullMark: 100 },
    { subject: 'RAM', score: subScores.ram_score ?? 85, fullMark: 100 },
    { subject: 'Network', score: subScores.network_score ?? 98, fullMark: 100 },
    { subject: 'Response', score: subScores.response_score ?? 95, fullMark: 100 },
    { subject: 'Heartbeat', score: subScores.heartbeat_score ?? 100, fullMark: 100 },
    { subject: 'App Health', score: subScores.application_score ?? 100, fullMark: 100 },
  ];

  return (
    <div className="glass-panel p-4 rounded-xl border border-slate-800 flex flex-col items-center">
      <div className="w-full text-left mb-2">
        <h3 className="text-sm font-bold text-white tracking-wide">Multi-Factor Health Vector</h3>
        <p className="text-xs text-slate-400">Sub-score decomposition for {nodeName}</p>
      </div>

      <div className="w-full h-[260px]">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart data={radarData}>
            <PolarGrid stroke="#1e293b" />
            <PolarAngleAxis dataKey="subject" stroke="#94a3b8" fontSize={11} />
            <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="#475569" fontSize={9} />
            <Radar
              name="Health Sub-Score"
              dataKey="score"
              stroke="#06b6d4"
              fill="#06b6d4"
              fillOpacity={0.35}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#0f172a',
                borderColor: '#334155',
                borderRadius: '8px',
                fontSize: '12px',
              }}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
