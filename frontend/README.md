# AttackGraphX - Attack-Path Analysis & Remediation Platform

**AttackGraphX** is an enterprise-grade cybersecurity dashboard built for real-time attack-path visualization, graph topology analysis, risk score aggregation, and what-if remediation simulation.

---

## 🛠️ Tech Stack

- **Framework**: React 18 + Vite (JavaScript / JSX)
- **Styling**: Tailwind CSS (Dark theme slate design system, Inter & JetBrains Mono typography)
- **Routing**: `react-router-dom` v6
- **Graph Topology**: Cytoscape.js (`react-cytoscapejs`)
- **Data Visualization**: Recharts
- **Icons**: `lucide-react`
- **Network Layer**: Native `fetch` wrapped in single API gateway adapter (`src/api/client.js`)

---

## 🚀 Quick Start & Installation

### Prerequisites
- Node.js (v18+ recommended)
- npm or yarn

### Installation Steps

```bash
# Navigate to the frontend directory
cd frontend

# Install dependencies
npm install

# Run the local development server (starts on http://localhost:3000)
npm run dev
```

### Running in Standalone Mock Mode
AttackGraphX requires **zero backend dependencies** to run. Mock mode is enabled by default in `.env.example`:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_USE_MOCK=true
```

To run build verification:
```bash
npm run build
npm run preview
```

To run E2E Playwright smoke tests:
```bash
npm run test:e2e
```

---

## 🔐 Credentials & RBAC

AttackGraphX features role-based access control (RBAC) decoded from JWT claims.

| Role | Username | Password | Privileges |
|---|---|---|---|
| **Admin** | `admin` | `admin123` | Full privileges: View dashboard, trigger scans, simulate fixes |
| **Analyst** | `analyst` | `analyst123` | View-only access: View dashboard, inspect paths, export reports |

*Note: Admin-only controls (e.g. "Trigger Scan", "Simulate Fix" buttons) are cleanly hidden when logged in as an Analyst.*

---

## 📡 Gateway API Contract

All network requests flow strictly through `src/api/client.js` with Bearer headers attached (`Authorization: Bearer <token>`).

| Method | Endpoint | Auth | Request Body | Response Shape / Description |
|---|---|---|---|---|
| `POST` | `/auth/login` | Public | `{ username, password }` | `{ access_token, token_type }` |
| `GET` | `/scan/trigger` | Admin | - | `{ message }` |
| `GET` | `/scan/status` | User | - | `{ status }` |
| `GET` | `/paths?target=` | User | Query `target` (optional) | `{ data: [...], status: "live" \| "stale_cache" \| "unavailable" }` |
| `GET` | `/patches` | User | - | `{ data: [...], status: "..." }` |
| `POST` | `/simulate` | Admin | `{ vulnerability_id }` | `{ before: {...}, after: {...}, status: "..." }` |
| `POST` | `/simulate/reset`| Admin | - | `{ status, message }` |
| `GET` | `/reports/pdf` | User | Query `target` (optional) | Binary PDF Blob download |
| `GET` | `/reports/csv` | User | - | Binary CSV Blob download |
| `GET` | `/health` | User | - | `{ status, dependencies: { recon: "up", analysis: "up", gateway: "up" } }` |

---

## 📊 Assumed Data Shapes

All shape assumptions are strictly isolated inside `src/api/client.js` and `src/api/mockData.js`.

### 1. Path Object
```json
{
  "id": "PATH-001",
  "target": "db-01",
  "risk_score": 95,
  "severity": "critical",
  "detectability": "low",
  "hops": [
    {
      "host": "cloud-gateway",
      "ip": "10.0.1.5",
      "vulnerability": "CVE-2023-34362",
      "attack_technique": "T1190",
      "description": "MOVEit Transfer RCE in ingress edge controller"
    },
    {
      "host": "web-01",
      "ip": "10.0.2.12",
      "vulnerability": "CVE-2021-44228",
      "attack_technique": "T1059",
      "description": "Log4Shell JNDI injection on public facing portal"
    }
  ]
}
```

### 2. Patch Object
```json
{
  "id": "PATCH-001",
  "vulnerability_id": "CVE-2023-34362",
  "host": "cloud-gateway",
  "description": "Apply MOVEit Transfer emergency security patch v2023.0.2 to prevent ingress unauthenticated RCE.",
  "paths_closed": 3,
  "risk_reduction": 42
}
```

### 3. Simulation Object
```json
{
  "before": { "path_count": 12, "avg_risk": 69, "critical_paths": 3 },
  "after": { "path_count": 9, "avg_risk": 54, "critical_paths": 1 },
  "vulnerability_id": "CVE-2023-34362",
  "status": "live"
}
```

---

## 🧪 Manual Demo Test Script ("Kill Analysis-Service")

Use the built-in **Status Dev Toggle** located in the Topbar to demonstrate AttackGraphX's resilience rules live during presentations or code reviews:

1. **Default State (`live`)**:
   - Topbar displays live green service health indicators (Recon, Analysis, Gateway).
   - All charts, graph nodes, and path tables render smoothly.

2. **Simulate Stale Cache (`stale_cache`)**:
   - Click **`stale_cache`** on the Topbar status dev toggle.
   - An **amber StatusBanner** appears immediately: *"Stale Cache: Analysis service unreachable, showing last known results."*
   - Telemetry data remains visible and interactive without any interruption or page crash.

3. **Simulate Service Failure (`unavailable`)**:
   - Click **`unavailable`** on the Topbar status dev toggle.
   - A **red StatusBanner** appears: *"Service Unavailable: Attack analysis gateway is currently offline or unreachable."*
   - Data panels switch to a clean `EmptyState` component featuring a **Retry Connection** button.
   - No stack trace, no raw error message, and no blank screen is ever presented to the user.

4. **Recover Connection**:
   - Click **`live`** on the status dev toggle or click the **Retry Connection** button to restore normal operations.
