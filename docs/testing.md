# CloudSentinel Testing Guide & Acceptance Test Suite

## 1. Running the Automated Test Suite

CloudSentinel includes a full unit and integration test suite using `pytest`.

To execute all tests:
```powershell
# From project root:
.\backend\.venv\Scripts\pytest.exe -v backend\tests
```

### Covered Test Modules:
1. `test_health_scoring.py`: Multi-factor health scoring formula, sub-scores, dynamic weights normalization.
2. `test_classifier.py`: State classification for `HEALTHY`, `WARNING`, `OVERLOADED`, `CRITICAL`, `DEAD`, `UNRESPONSIVE`, `ZOMBIE`.
3. `test_diagnostics.py`: Root-cause identification, evidence collection, confidence score, recommended self-healing action.
4. `test_recovery.py`: Hierarchical self-healing, low-confidence approval gate, post-recovery verification.
5. `test_prediction.py`: Scikit-Learn linear regression degradation projection and Isolation Forest multivariate anomaly detection.
6. `test_api.py`: FastAPI endpoints, system status, reports, and fault injection safety boundary validation.

---

## 2. Acceptance Test Verification (Section 64)

Follow these live demonstration steps:

| Step | Action | Expected Result |
|---|---|---|
| **TEST 1** | Run `scripts\run_local.ps1` or `docker compose up` | Backend and dashboard start. All 5 demo containers display with health scores > 90%. |
| **TEST 2** | Observe Dashboard | Telemetry updates in real time over WebSocket. CPU, RAM, Latency, and Status fluctuate naturally. |
| **TEST 3** | Navigate to Fault Injection -> Click **CPU STRESS** on `cs-node-web` | CPU spikes to 95%+. Node becomes `OVERLOADED`. Diagnostic engine flags `CPU_OVERLOAD`. |
| **TEST 4** | Click **CRASH APPLICATION LAYER** on `cs-node-api` | Health probe returns HTTP 500. Container remains alive. Self-healing Tier 1 restarts application. Health returns to 90%+. |
| **TEST 5** | Click **TERMINATE CONTAINER** on `cs-node-worker` | Container stops. Heartbeat is lost. Self-healing Tier 2 restarts the container. Status returns to `HEALTHY`. |
| **TEST 6** | Force low confidence recovery | State enters `REQUIRES_APPROVAL`. Recovery Center prompts Administrator to approve before execution. |
| **TEST 7** | View Metric History & Recovery Center | Incident timeline displays failure, action, verification before/after health score. |
| **TEST 8** | View Audit Logs | All autonomous self-healing and manual fault injection commands are logged with timestamps. |
| **TEST 9** | View Predictions Page | Anomaly score and linear regression degradation projections display explainable recommendations. |
