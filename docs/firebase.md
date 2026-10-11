# CloudSentinel Firebase Integration & Local Demo Mode

## 1. Local Demo Mode (Default)

CloudSentinel does **NOT** require any paid cloud accounts or third-party API keys to run out-of-the-box.

When Firebase credentials are empty in `.env`:
- The system activates **Local Demo Mode**.
- A prominent "Local Demo Mode" indicator badge is displayed in the dashboard.
- Authentication defaults to interactive role switching (`ADMIN`, `OPERATOR`, `VIEWER`) via the top navbar.
- Telemetry, alerts, recoveries, and audit logs persist in the high-performance local in-memory ring buffer.

---

## 2. Optional Firebase Cloud Integration

To enable cloud authentication and remote Firestore persistence:

1. Create a Firebase project at [https://console.firebase.google.com](https://console.firebase.google.com).
2. Enable **Firestore Database** in test or production mode.
3. Generate a private service account key under **Project Settings > Service Accounts**.
4. Update your `.env` file:
   ```env
   FIREBASE_PROJECT_ID=your-project-id
   FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxx@your-project-id.iam.gserviceaccount.com
   FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
   ```
5. Restart the backend. CloudSentinel will automatically connect and batch aggregated telemetry every 30-60 seconds.

---

## 3. Role-Based Access Control (RBAC)

| Role | Privileges |
|---|---|
| **ADMIN** | Full system control: configure weights/thresholds, toggle auto-recovery, approve low-confidence recoveries, manual container restarts/recreations, fault injection. |
| **OPERATOR** | Monitor cluster, trigger manual recovery, inject faults, acknowledge/resolve alerts, view audit logs. |
| **VIEWER** | Read-only access to dashboard, topology map, logs, metrics, and reports. All mutating actions are disabled. |
