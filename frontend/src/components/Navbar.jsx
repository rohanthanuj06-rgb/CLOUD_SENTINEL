import React from 'react';
import { Activity, ShieldCheck, RefreshCw, Zap, Server, Shield, User } from 'lucide-react';
import { api } from '../services/api';

export default function Navbar({ systemStatus, isWsConnected, currentRole, onRoleChange, onRefresh }) {
  return (
    <header className="glass-panel sticky top-0 z-40 border-b border-slate-800/80 px-6 py-3 flex items-center justify-between">
      {/* Brand & Subtitle */}
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-cyan-600 to-blue-500 flex items-center justify-center shadow-lg shadow-cyan-500/20">
          <Activity className="w-5 h-5 text-white" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-base font-extrabold tracking-wider bg-gradient-to-r from-white via-slate-100 to-cyan-300 bg-clip-text text-transparent">
              CLOUDSENTINEL
            </h1>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-cyan-400 border border-cyan-500/30">
              v1.0
            </span>
          </div>
          <p className="text-[11px] text-slate-400 hidden sm:block">
            Intelligent Virtual Infrastructure Health Monitoring & Self-Recovery
          </p>
        </div>
      </div>

      {/* Status Badges & Controls */}
      <div className="flex items-center gap-3">
        {/* Local Demo Mode Banner */}
        {systemStatus?.demo_mode && (
          <span className="hidden md:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
            Local Demo Mode
          </span>
        )}

        {/* Docker Engine Mode */}
        <span className="hidden lg:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-mono bg-slate-800/80 text-slate-300 border border-slate-700">
          <Server className="w-3 h-3 text-cyan-400" />
          {systemStatus?.docker_engine_mode || 'Connecting...'}
        </span>

        {/* WebSocket Live Telemetry Pulse */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-mono bg-dark-900 border border-slate-800">
          <span className={`w-2 h-2 rounded-full ${isWsConnected ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'}`} />
          <span className={isWsConnected ? 'text-emerald-400' : 'text-rose-400'}>
            {isWsConnected ? 'LIVE WS' : 'DISCONNECTED'}
          </span>
        </div>

        {/* RBAC Role Selector */}
        <div className="flex items-center gap-1.5 bg-slate-900/90 border border-slate-800 rounded-lg px-2.5 py-1">
          <User className="w-3.5 h-3.5 text-cyan-400" />
          <select
            value={currentRole}
            onChange={(e) => {
              const r = e.target.value;
              api.setRole(r);
              onRoleChange(r);
            }}
            className="bg-transparent text-xs font-semibold text-slate-200 focus:outline-none cursor-pointer"
          >
            <option value="ADMIN" className="bg-slate-900 text-white">ADMIN</option>
            <option value="OPERATOR" className="bg-slate-900 text-white">OPERATOR</option>
            <option value="VIEWER" className="bg-slate-900 text-white">VIEWER</option>
          </select>
        </div>

        {/* Manual Refresh */}
        <button
          onClick={onRefresh}
          title="Refresh Telemetry"
          className="p-1.5 rounded-lg border border-slate-800 hover:border-cyan-500/40 text-slate-400 hover:text-cyan-400 transition-colors bg-slate-900/60"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
}
