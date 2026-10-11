import { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';
import { useWebSocket } from './useWebSocket';

export function useNodes() {
  const [nodes, setNodes] = useState([]);
  const [summary, setSummary] = useState({
    total_nodes: 5,
    healthy: 5,
    good: 0,
    warning: 0,
    overloaded: 0,
    poor: 0,
    critical: 0,
    unresponsive: 0,
    dead: 0,
    idle: 0,
    zombie: 0,
    recovering: 0,
    recovery_failed: 0,
    average_health_score: 95.0,
    recovery_success_rate: 100.0,
  });
  const [alerts, setAlerts] = useState([]);
  const [recoveries, setRecoveries] = useState([]);
  const [systemStatus, setSystemStatus] = useState(null);
  const [selectedNodeId, setSelectedNodeId] = useState('cs-node-web');
  const [selectedNodeDetail, setSelectedNodeDetail] = useState(null);
  const [currentRole, setCurrentRole] = useState(localStorage.getItem('cloudsentinel_role') || 'ADMIN');
  const [loading, setLoading] = useState(true);
  const [notification, setNotification] = useState(null);

  const showNotification = (message, type = 'info') => {
    setNotification({ message, type, id: Date.now() });
    setTimeout(() => setNotification(null), 4000);
  };

  // Fetch all core resources
  const fetchAll = useCallback(async () => {
    try {
      const [nodesData, alertsData, recoveryData, statusData] = await Promise.all([
        api.getNodes().catch(() => ({ summary: {}, nodes: [] })),
        api.getAlerts().catch(() => []),
        api.getRecovery().catch(() => ({ summary: {}, recoveries: [] })),
        api.getSystemStatus().catch(() => null),
      ]);

      if (nodesData.nodes) setNodes(nodesData.nodes);
      if (nodesData.summary) setSummary(nodesData.summary);
      setAlerts(alertsData || []);
      setRecoveries(recoveryData.recoveries || []);
      setSystemStatus(statusData);
    } catch (err) {
      console.error('Error fetching platform data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch specific node details
  const fetchNodeDetail = useCallback(async (nodeId) => {
    if (!nodeId) return;
    try {
      const detail = await api.getNodeDetail(nodeId);
      setSelectedNodeDetail(detail);
    } catch (err) {
      console.error(`Error loading detail for ${nodeId}:`, err);
    }
  }, []);

  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, 6000);
    return () => clearInterval(interval);
  }, [fetchAll]);

  useEffect(() => {
    if (selectedNodeId) {
      fetchNodeDetail(selectedNodeId);
    }
  }, [selectedNodeId, fetchNodeDetail]);

  // WebSocket event handler
  const handleWebSocketMessage = useCallback(
    (msg) => {
      if (msg.type === 'TELEMETRY_UPDATE' && msg.data?.nodes) {
        setNodes(msg.data.nodes);
        // Refresh selected node detail if it was updated
        if (selectedNodeId) {
          const updated = msg.data.nodes.find((n) => n.node_id === selectedNodeId);
          if (updated) {
            setSelectedNodeDetail((prev) => (prev ? { ...prev, node: updated } : prev));
          }
        }
      } else if (msg.type === 'ALERT_CREATED') {
        setAlerts((prev) => [msg.data, ...prev]);
        showNotification(`New Alert: ${msg.data.title}`, 'warning');
      } else if (msg.type === 'ALERT_UPDATED') {
        setAlerts((prev) => prev.map((a) => (a.id === msg.data.id ? msg.data : a)));
      } else if (msg.type === 'RECOVERY_STARTED') {
        setRecoveries((prev) => [msg.data, ...prev]);
        showNotification(`Self-Recovery dispatched on ${msg.data.node_id}`, 'info');
      } else if (msg.type === 'RECOVERY_COMPLETED') {
        setRecoveries((prev) => prev.map((r) => (r.recovery_id === msg.data.recovery_id ? msg.data : r)));
        showNotification(
          `Recovery completed on ${msg.data.node_id}: ${msg.data.result}`,
          msg.data.result === 'SUCCESS' ? 'success' : 'error'
        );
      }
    },
    [selectedNodeId]
  );

  const { isConnected: isWsConnected } = useWebSocket(handleWebSocketMessage);

  return {
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
    loading,
    isWsConnected,
    notification,
    showNotification,
    refreshAll: fetchAll,
    refreshNodeDetail: () => fetchNodeDetail(selectedNodeId),
  };
}
