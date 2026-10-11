import React from 'react';

const STATE_CONFIG = {
  HEALTHY: { bg: 'bg-emerald-500/15', text: 'text-emerald-400', border: 'border-emerald-500/30', dot: 'bg-emerald-400' },
  GOOD: { bg: 'bg-teal-500/15', text: 'text-teal-300', border: 'border-teal-500/30', dot: 'bg-teal-400' },
  WARNING: { bg: 'bg-amber-500/15', text: 'text-amber-400', border: 'border-amber-500/30', dot: 'bg-amber-400' },
  OVERLOADED: { bg: 'bg-orange-500/15', text: 'text-orange-400', border: 'border-orange-500/30', dot: 'bg-orange-400' },
  POOR: { bg: 'bg-rose-500/15', text: 'text-rose-300', border: 'border-rose-500/30', dot: 'bg-rose-300' },
  CRITICAL: { bg: 'bg-rose-500/20', text: 'text-rose-400', border: 'border-rose-500/40', dot: 'bg-rose-500 animate-ping' },
  UNRESPONSIVE: { bg: 'bg-purple-500/20', text: 'text-purple-300', border: 'border-purple-500/40', dot: 'bg-purple-400' },
  DEAD: { bg: 'bg-slate-700/40', text: 'text-slate-400', border: 'border-slate-600/40', dot: 'bg-slate-500' },
  IDLE: { bg: 'bg-cyan-500/15', text: 'text-cyan-300', border: 'border-cyan-500/30', dot: 'bg-cyan-400' },
  ZOMBIE: { bg: 'bg-fuchsia-500/15', text: 'text-fuchsia-300', border: 'border-fuchsia-500/30', dot: 'bg-fuchsia-400' },
  RECOVERING: { bg: 'bg-blue-500/20', text: 'text-blue-400', border: 'border-blue-500/40', dot: 'bg-blue-400 animate-pulse' },
  RECOVERY_FAILED: { bg: 'bg-red-900/30', text: 'text-red-400', border: 'border-red-600/40', dot: 'bg-red-500' },
};

export default function StatusBadge({ status, className = '' }) {
  const norm = (status || 'HEALTHY').toUpperCase();
  const conf = STATE_CONFIG[norm] || STATE_CONFIG.HEALTHY;

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${conf.bg} ${conf.text} ${conf.border} ${className}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${conf.dot}`} />
      {norm}
    </span>
  );
}
