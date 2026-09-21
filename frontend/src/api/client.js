import { mockPaths, mockPatches, mockHealth } from './mockData';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true' || import.meta.env.VITE_USE_MOCK === '1';

// Global Dev Toggle State for status simulation demo
let devSimulatedStatus = 'live';

export function setDevSimulatedStatus(status) {
  devSimulatedStatus = status;
}

export function getDevSimulatedStatus() {
  return devSimulatedStatus;
}

// In-memory simulation state for What-If fixes
let activeSimulatedFixes = new Set();

/**
 * Standardized fetch helper
 */
async function apiFetch(endpoint, options = {}) {
  const token = sessionStorage.getItem('attackgraphx_token');
  
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  if (token && !endpoint.includes('/auth/login')) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Check if mock mode is active
  if (USE_MOCK) {
    return mockHandler(endpoint, options);
  }

  try {
    const response = await fetch(`${BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      sessionStorage.removeItem('attackgraphx_token');
      window.location.href = '/login?expired=true';
      throw new Error('Session expired');
    }

    if (response.status === 403) {
      throw new Error('Admin access required');
    }

    if (!response.ok) {
      return { data: [], status: 'unavailable', error: `HTTP ${response.status}` };
    }

    // Blob endpoints
    if (options.responseType === 'blob') {
      const blob = await response.blob();
      return blob;
    }

    const data = await response.json();

    // Inject dev override status if set
    if (devSimulatedStatus !== 'live' && data && typeof data === 'object') {
      data.status = devSimulatedStatus;
      if (devSimulatedStatus === 'unavailable') {
        data.data = [];
      }
    }

    return data;
  } catch (error) {
    // Network failure or non-JSON -> treat as unavailable
    return {
      data: [],
      status: 'unavailable',
      message: 'Analysis service unreachable',
    };
  }
}

/**
 * Mock Handler implementation
 */
async function mockHandler(endpoint, options = {}) {
  // Artificial network latency (150ms)
  await new Promise((resolve) => setTimeout(resolve, 150));

  // If status is simulated as unavailable, return unavailable state
  if (devSimulatedStatus === 'unavailable' && !endpoint.includes('/auth/login') && !endpoint.includes('/health')) {
    return { data: [], status: 'unavailable' };
  }

  const status = devSimulatedStatus;

  // 1. Auth Login
  if (endpoint.includes('/auth/login')) {
    const body = options.body ? JSON.parse(options.body) : {};
    const role = body.username === 'admin' ? 'admin' : 'analyst';
    
    // Construct valid base64 payload JWT token
    const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
    const payload = btoa(JSON.stringify({ sub: body.username, role, exp: Math.floor(Date.now() / 1000) + 86400 }));
    const token = `${header}.${payload}.mock_signature`;

    return { access_token: token, token_type: 'bearer' };
  }

  // 2. Scan Trigger (Admin only)
  if (endpoint.includes('/scan/trigger')) {
    return { message: 'Security graph scan triggered successfully. Processing topology updates...' };
  }

  // 3. Scan Status
  if (endpoint.includes('/scan/status')) {
    return { status: 'idle', last_scan: new Date().toISOString() };
  }

  // 4. Paths
  if (endpoint.includes('/paths')) {
    const urlObj = new URL(endpoint, 'http://dummy.local');
    const target = urlObj.searchParams.get('target');

    let filtered = mockPaths.filter((p) => !activeSimulatedFixes.has(p.hops.map(h => h.vulnerability).find(v => activeSimulatedFixes.has(v))));

    // Filter paths if specific target requested
    if (target && target !== 'all') {
      filtered = filtered.filter((p) => p.target.toLowerCase() === target.toLowerCase());
    }

    return {
      data: filtered,
      status: status,
    };
  }

  // 5. Patches
  if (endpoint.includes('/patches')) {
    return {
      data: mockPatches,
      status: status,
    };
  }

  // 6. Simulate Fix
  if (endpoint.includes('/simulate')) {
    const body = options.body ? JSON.parse(options.body) : {};
    const vulnId = body.vulnerability_id;

    const remainingPaths = mockPaths.filter(p => !p.hops.some(h => h.vulnerability === vulnId || activeSimulatedFixes.has(h.vulnerability)));
    
    // Track active fixes
    if (vulnId) {
      activeSimulatedFixes.add(vulnId);
    }

    const calcStats = (paths) => {
      const count = paths.length;
      const criticals = paths.filter(p => p.severity === 'critical').length;
      const avg = count ? Math.round(paths.reduce((acc, p) => acc + p.risk_score, 0) / count) : 0;
      return { path_count: count, avg_risk: avg, critical_paths: criticals };
    };

    const beforeStats = calcStats(mockPaths);
    const afterStats = calcStats(remainingPaths);

    return {
      before: beforeStats,
      after: afterStats,
      vulnerability_id: vulnId,
      status: status,
    };
  }

  // 7. Reset Simulation
  if (endpoint.includes('/simulate/reset')) {
    activeSimulatedFixes.clear();
    return { status: 'live', message: 'Simulations reset' };
  }

  // 8. PDF Report
  if (endpoint.includes('/reports/pdf')) {
    const sampleText = `%PDF-1.4 Mock AttackGraphX Executive Report - Target: ${endpoint}`;
    const blob = new Blob([sampleText], { type: 'application/pdf' });
    return blob;
  }

  // 9. CSV Report
  if (endpoint.includes('/reports/csv')) {
    const csvContent = "Path_ID,Target,Risk_Score,Severity,Hops\n" + mockPaths.map(p => `${p.id},${p.target},${p.risk_score},${p.severity},"${p.hops.map(h => h.host).join(' -> ')}"`).join("\n");
    const blob = new Blob([csvContent], { type: 'text/csv' });
    return blob;
  }

  // 10. Health
  if (endpoint.includes('/health')) {
    return mockHealth;
  }

  return { data: [], status: 'live' };
}

// Exported high-level API functions
export async function loginApi(username, password) {
  return apiFetch('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
}

export async function fetchPaths(target = 'all') {
  const query = target && target !== 'all' ? `?target=${encodeURIComponent(target)}` : '';
  return apiFetch(`/paths${query}`);
}

export async function fetchPatches() {
  return apiFetch('/patches');
}

export async function simulateFix(vulnerability_id) {
  return apiFetch('/simulate', {
    method: 'POST',
    body: JSON.stringify({ vulnerability_id }),
  });
}

export async function resetSimulation() {
  return apiFetch('/simulate/reset', { method: 'POST' });
}

export async function triggerScan() {
  return apiFetch('/scan/trigger');
}

export async function fetchHealth() {
  return apiFetch('/health');
}

export async function downloadReportPdf(target = 'all') {
  return apiFetch(`/reports/pdf?target=${encodeURIComponent(target)}`, {
    responseType: 'blob',
  });
}

export async function downloadReportCsv() {
  return apiFetch('/reports/csv', {
    responseType: 'blob',
  });
}
