const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class ApiClient {
  constructor() {
    this.role = localStorage.getItem('cloudsentinel_role') || 'ADMIN';
  }

  setRole(newRole) {
    this.role = newRole;
    localStorage.setItem('cloudsentinel_role', newRole);
  }

  getHeaders() {
    return {
      'Content-Type': 'application/json',
      'X-Demo-Role': this.role,
    };
  }

  async request(path, options = {}) {
    const url = `${API_BASE}${path}`;
    const headers = { ...this.getHeaders(), ...(options.headers || {}) };
    const response = await fetch(url, { ...options, headers });
    
    if (!response.ok) {
      let errorDetail = 'API request failed';
      try {
        const errorJson = await response.json();
        errorDetail = errorJson.detail || errorDetail;
      } catch (e) {
        errorDetail = response.statusText;
      }
      throw new Error(errorDetail);
    }
    return response.json();
  }

  // System
  getSystemStatus() { return this.request('/api/system/status'); }
  getSystemConfig() { return this.request('/api/system/config'); }
  updateWeights(weights) {
    return this.request('/api/system/config/weights', { method: 'POST', body: JSON.stringify(weights) });
  }
  updateThresholds(thresholds) {
    return this.request('/api/system/config/thresholds', { method: 'POST', body: JSON.stringify(thresholds) });
  }
  toggleAutoRecovery(enabled) {
    return this.request(`/api/system/config/auto-recovery/toggle?enabled=${enabled}`, { method: 'POST' });
  }

  // Nodes
  getNodes() { return this.request('/api/nodes'); }
  getNodeDetail(nodeId) { return this.request(`/api/nodes/${nodeId}`); }
  getNodeMetrics(nodeId, range = '15m') { return this.request(`/api/nodes/${nodeId}/metrics?range=${range}`); }
  getNodeLogs(nodeId, tail = 50) { return this.request(`/api/nodes/${nodeId}/logs?tail=${tail}`); }
  restartNode(nodeId) { return this.request(`/api/nodes/${nodeId}/restart`, { method: 'POST' }); }
  recreateNode(nodeId) { return this.request(`/api/nodes/${nodeId}/recreate`, { method: 'POST' }); }
  scaleNode(nodeId) { return this.request(`/api/nodes/${nodeId}/scale`, { method: 'POST' }); }

  // Alerts
  getAlerts(status = null) {
    const q = status ? `?status=${status}` : '';
    return this.request(`/api/alerts${q}`);
  }
  acknowledgeAlert(alertId) { return this.request(`/api/alerts/${alertId}/acknowledge`, { method: 'POST' }); }
  resolveAlert(alertId) { return this.request(`/api/alerts/${alertId}/resolve`, { method: 'POST' }); }

  // Recovery
  getRecovery() { return this.request('/api/recovery'); }
  triggerRecovery(payload) { return this.request('/api/recovery/trigger', { method: 'POST', body: JSON.stringify(payload) }); }
  approveRecovery(recoveryId, approved, notes = '') {
    return this.request(`/api/recovery/${recoveryId}/approve`, {
      method: 'POST',
      body: JSON.stringify({ recovery_id: recoveryId, approved, operator_notes: notes }),
    });
  }

  // Diagnostics
  getDiagnostics() { return this.request('/api/diagnostics'); }
  getNodeDiagnostic(nodeId) { return this.request(`/api/diagnostics/${nodeId}`); }

  // Predictions
  getPredictions() { return this.request('/api/predictions'); }

  // Fault Injection
  injectCpuFault(payload) { return this.request('/api/faults/cpu', { method: 'POST', body: JSON.stringify(payload) }); }
  injectMemoryFault(payload) { return this.request('/api/faults/memory', { method: 'POST', body: JSON.stringify(payload) }); }
  injectAppFailure(nodeId) { return this.request('/api/faults/application', { method: 'POST', body: JSON.stringify({ node_id: nodeId }) }); }
  injectContainerStop(nodeId) { return this.request('/api/faults/container', { method: 'POST', body: JSON.stringify({ node_id: nodeId }) }); }
  injectNetworkFault(payload) { return this.request('/api/faults/network', { method: 'POST', body: JSON.stringify(payload) }); }
  injectDiskFault(payload) { return this.request('/api/faults/disk', { method: 'POST', body: JSON.stringify(payload) }); }
  resetFaults(nodeId = null) { return this.request('/api/faults/reset', { method: 'POST', body: JSON.stringify({ node_id: nodeId }) }); }

  // Audit Logs
  getAuditLogs(limit = 100, nodeId = null, eventType = null) {
    const params = new URLSearchParams({ limit });
    if (nodeId) params.append('node_id', nodeId);
    if (eventType) params.append('event_type', eventType);
    return this.request(`/api/audit?${params.toString()}`);
  }

  // Reports
  getReportSummary() { return this.request('/api/reports/summary'); }
  getExportCsvUrl() { return `${API_BASE}/api/reports/export/csv`; }
}

export const api = new ApiClient();
