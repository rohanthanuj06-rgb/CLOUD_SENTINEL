import React from 'react';

export default function StatCard({ title, value, subtext, icon: Icon, color = 'cyan', onClick, className = '' }) {
  const colorMap = {
    cyan: 'border-cyan-500/30 text-cyan-400 bg-cyan-500/10',
    emerald: 'border-emerald-500/30 text-emerald-400 bg-emerald-500/10',
    amber: 'border-amber-500/30 text-amber-400 bg-amber-500/10',
    rose: 'border-rose-500/30 text-rose-400 bg-rose-500/10',
    purple: 'border-purple-500/30 text-purple-400 bg-purple-500/10',
    blue: 'border-blue-500/30 text-blue-400 bg-blue-500/10',
  };

  const badgeStyle = colorMap[color] || colorMap.cyan;

  return (
    <div
      onClick={onClick}
      className={`glass-panel p-4 rounded-xl border border-slate-800 hover:border-slate-700 transition-all duration-200 ${
        onClick ? 'cursor-pointer hover:bg-slate-800/40' : ''
      } ${className}`}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">{title}</span>
        {Icon && (
          <div className={`p-2 rounded-lg border ${badgeStyle}`}>
            <Icon className="w-4 h-4" />
          </div>
        )}
      </div>

      <div className="mt-2 flex items-baseline gap-2">
        <span className="text-2xl font-bold font-mono tracking-tight text-white">{value}</span>
        {subtext && <span className="text-xs text-slate-400">{subtext}</span>}
      </div>
    </div>
  );
}
