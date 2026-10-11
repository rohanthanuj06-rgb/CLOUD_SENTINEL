import React from 'react';
import {
  LayoutDashboard,
  Network,
  Activity,
  AlertTriangle,
  ShieldCheck,
  Stethoscope,
  TrendingUp,
  Flame,
  FileText,
  FileSpreadsheet,
  Settings,
  ShieldAlert
} from 'lucide-react';

export default function Sidebar({ activeTab, onTabSelect, activeAlertCount = 0 }) {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'infrastructure', label: 'Infrastructure Map', icon: Network },
    { id: 'health', label: 'Health Monitor', icon: Activity },
    { id: 'alerts', label: 'Alert Center', icon: AlertTriangle, badge: activeAlertCount },
    { id: 'recovery', label: 'Recovery Center', icon: ShieldCheck },
    { id: 'diagnostics', label: 'Diagnostics', icon: Stethoscope },
    { id: 'predictions', label: 'Predictions & ML', icon: TrendingUp },
    { id: 'faults', label: 'Fault Injection', icon: Flame, highlight: true },
    { id: 'audit', label: 'Audit Logs', icon: FileText },
    { id: 'reports', label: 'Reports', icon: FileSpreadsheet },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <aside className="w-64 glass-panel border-r border-slate-800/80 min-h-[calc(100vh-61px)] p-3 flex flex-col justify-between">
      <nav className="space-y-1">
        <div className="px-3 py-2 text-[10px] font-bold uppercase tracking-wider text-slate-500">
          Operations Center
        </div>

        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onTabSelect(item.id)}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-semibold transition-all duration-150 ${
                isActive
                  ? 'bg-gradient-to-r from-cyan-500/20 to-blue-500/10 text-cyan-300 border border-cyan-500/30 shadow-sm'
                  : item.highlight
                  ? 'text-amber-400 hover:bg-amber-500/10 hover:text-amber-300'
                  : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
              }`}
            >
              <div className="flex items-center gap-2.5">
                <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-400' : ''}`} />
                <span>{item.label}</span>
              </div>

              {item.badge > 0 && (
                <span className="px-1.5 py-0.2 rounded-full text-[10px] font-bold font-mono bg-rose-500/20 text-rose-400 border border-rose-500/40">
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Controller Integrity Pill */}
      <div className="p-3 rounded-lg bg-dark-900 border border-slate-800/80 text-[11px]">
        <div className="flex items-center gap-2 text-cyan-400 font-semibold mb-1">
          <ShieldAlert className="w-3.5 h-3.5" />
          <span>Self-Healing Engine</span>
        </div>
        <p className="text-slate-400 text-[10px] leading-tight">
          Active surveillance across 5 container nodes with hierarchical recovery tiers.
        </p>
      </div>
    </aside>
  );
}
