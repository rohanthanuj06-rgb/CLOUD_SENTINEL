import React, { useState } from 'react';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import DashboardPage from './pages/DashboardPage';
import InfrastructurePage from './pages/InfrastructurePage';
import NodeDetailsPage from './pages/NodeDetailsPage';
import HealthMonitorPage from './pages/HealthMonitorPage';
import AlertsPage from './pages/AlertsPage';
import RecoveryCenterPage from './pages/RecoveryCenterPage';
import DiagnosticsPage from './pages/DiagnosticsPage';
import PredictionsPage from './pages/PredictionsPage';
import FaultInjectionPage from './pages/FaultInjectionPage';
import AuditLogsPage from './pages/AuditLogsPage';
import ReportsPage from './pages/ReportsPage';
import SettingsPage from './pages/SettingsPage';
import { useNodes } from './hooks/useNodes';
import { AlertCircle, CheckCircle2, Info } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const {
    nodes,
    summary,
    alerts,
    recoveries,
    systemStatus,
    selectedNodeId,
    setSelectedNodeId,
    selectedNodeDetail,
    currentRole,
    setCurrentRole,
    isWsConnected,
    notification,
    showNotification,
    refreshAll,
    refreshNodeDetail,
  } = useNodes();

  const activeAlertCount = alerts.filter((a) => a.status === 'ACTIVE').length;

  return (
    <div className="min-h-screen bg-dark-950 text-slate-100 flex flex-col font-sans">
      {/* Top Operations Navbar */}
      <Navbar
        systemStatus={systemStatus}
        isWsConnected={isWsConnected}
        currentRole={currentRole}
        onRoleChange={setCurrentRole}
        onRefresh={refreshAll}
      />

      {/* Floating Notification Toast */}
      {notification && (
        <div className="fixed bottom-5 right-5 z-50 flex items-center gap-2.5 px-4 py-2.5 rounded-xl glass-panel-glow border border-slate-700 shadow-2xl text-xs font-semibold animate-slide-up">
          {notification.type === 'success' && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
          {notification.type === 'warning' && <AlertCircle className="w-4 h-4 text-amber-400" />}
          {notification.type === 'error' && <AlertCircle className="w-4 h-4 text-rose-400" />}
          {notification.type === 'info' && <Info className="w-4 h-4 text-cyan-400" />}
          <span>{notification.message}</span>
        </div>
      )}

      {/* Main Workspace Layout */}
      <div className="flex-1 flex overflow-hidden">
        <Sidebar
          activeTab={activeTab}
          onTabSelect={setActiveTab}
          activeAlertCount={activeAlertCount}
        />

        <main className="flex-1 p-6 overflow-y-auto max-h-[calc(100vh-61px)]">
          {activeTab === 'dashboard' && (
            <DashboardPage
              nodes={nodes}
              summary={summary}
              alerts={alerts}
              recoveries={recoveries}
              onSelectNode={setSelectedNodeId}
              onNavigate={setActiveTab}
              showNotification={showNotification}
              refreshAll={refreshAll}
              currentRole={currentRole}
            />
          )}

          {activeTab === 'infrastructure' && (
            <InfrastructurePage
              nodes={nodes}
              onSelectNode={setSelectedNodeId}
              onNavigate={setActiveTab}
            />
          )}

          {activeTab === 'node-details' && (
            <NodeDetailsPage
              nodeId={selectedNodeId}
              detail={selectedNodeDetail}
              onRefresh={refreshNodeDetail}
              showNotification={showNotification}
              currentRole={currentRole}
            />
          )}

          {activeTab === 'health' && (
            <HealthMonitorPage
              nodes={nodes}
              onSelectNode={setSelectedNodeId}
              onNavigate={setActiveTab}
            />
          )}

          {activeTab === 'alerts' && (
            <AlertsPage
              alerts={alerts}
              showNotification={showNotification}
              refreshAll={refreshAll}
              currentRole={currentRole}
            />
          )}

          {activeTab === 'recovery' && (
            <RecoveryCenterPage
              recoveries={recoveries}
              showNotification={showNotification}
              refreshAll={refreshAll}
              currentRole={currentRole}
            />
          )}

          {activeTab === 'diagnostics' && (
            <DiagnosticsPage
              onSelectNode={setSelectedNodeId}
              onNavigate={setActiveTab}
            />
          )}

          {activeTab === 'predictions' && <PredictionsPage />}

          {activeTab === 'faults' && (
            <FaultInjectionPage
              nodes={nodes}
              showNotification={showNotification}
              refreshAll={refreshAll}
              currentRole={currentRole}
            />
          )}

          {activeTab === 'audit' && <AuditLogsPage />}

          {activeTab === 'reports' && <ReportsPage />}

          {activeTab === 'settings' && (
            <SettingsPage
              showNotification={showNotification}
              currentRole={currentRole}
            />
          )}
        </main>
      </div>
    </div>
  );
}
