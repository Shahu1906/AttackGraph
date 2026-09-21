// Mock Data Fixtures for AttackGraphX
// Shapes strictly follow contract specified in README

export const mockPaths = [
  {
    id: "PATH-001",
    target: "db-01",
    risk_score: 95,
    severity: "critical",
    detectability: "low",
    hops: [
      { host: "cloud-gateway", ip: "10.0.1.5", vulnerability: "CVE-2023-34362", attack_technique: "T1190", description: "MOVEit Transfer RCE in ingress edge controller" },
      { host: "web-01", ip: "10.0.2.12", vulnerability: "CVE-2021-44228", attack_technique: "T1059", description: "Log4Shell JNDI injection on public facing portal" },
      { host: "app-01", ip: "10.0.3.45", vulnerability: "CVE-2022-22965", attack_technique: "T1068", description: "Spring4Shell Remote Code Execution in business service" },
      { host: "db-01", ip: "10.0.4.100", vulnerability: "CVE-2023-23397", attack_technique: "T1078", description: "Privilege escalation via hardcoded DB administrator credentials" }
    ]
  },
  {
    id: "PATH-002",
    target: "vault-01",
    risk_score: 91,
    severity: "critical",
    detectability: "low",
    hops: [
      { host: "cloud-gateway", ip: "10.0.1.5", vulnerability: "CVE-2023-34362", attack_technique: "T1190", description: "MOVEit Transfer RCE in ingress edge controller" },
      { host: "jump-01", ip: "10.0.1.99", vulnerability: "CVE-2024-3094", attack_technique: "T1021", description: "XZ Utils backdoor in SSH bastion host" },
      { host: "vault-01", ip: "10.0.5.20", vulnerability: "CVE-2023-33246", attack_technique: "T1552", description: "RocketMQ RCE leaking master secret key stored in memory" }
    ]
  },
  {
    id: "PATH-003",
    target: "db-01",
    risk_score: 87,
    severity: "critical",
    detectability: "medium",
    hops: [
      { host: "web-02", ip: "10.0.2.14", vulnerability: "CVE-2023-38606", attack_technique: "T1190", description: "Unauthenticated SSRF bypassing internal perimeter filters" },
      { host: "k8s-node-01", ip: "10.0.3.110", vulnerability: "CVE-2022-3172", attack_technique: "T1611", description: "Kubernetes API server cluster breakout" },
      { host: "db-01", ip: "10.0.4.100", vulnerability: "CVE-2023-23397", attack_technique: "T1078", description: "Privilege escalation via hardcoded DB administrator credentials" }
    ]
  },
  {
    id: "PATH-004",
    target: "auth-01",
    risk_score: 82,
    severity: "high",
    detectability: "medium",
    hops: [
      { host: "cloud-gateway", ip: "10.0.1.5", vulnerability: "CVE-2024-21887", attack_technique: "T1190", description: "Ivanti Connect Secure command injection" },
      { host: "auth-01", ip: "10.0.2.88", vulnerability: "CVE-2023-48795", attack_technique: "T1110", description: "Terrapin SSH prefix truncation attack on OAuth gateway" }
    ]
  },
  {
    id: "PATH-005",
    target: "app-01",
    risk_score: 79,
    severity: "high",
    detectability: "medium",
    hops: [
      { host: "web-01", ip: "10.0.2.12", vulnerability: "CVE-2021-44228", attack_technique: "T1059", description: "Log4Shell JNDI injection on public facing portal" },
      { host: "app-01", ip: "10.0.3.45", vulnerability: "CVE-2022-22965", attack_technique: "T1068", description: "Spring4Shell Remote Code Execution in business service" }
    ]
  },
  {
    id: "PATH-006",
    target: "k8s-node-01",
    risk_score: 74,
    severity: "high",
    detectability: "high",
    hops: [
      { host: "web-02", ip: "10.0.2.14", vulnerability: "CVE-2023-38606", attack_technique: "T1190", description: "Unauthenticated SSRF bypassing internal perimeter filters" },
      { host: "k8s-node-01", ip: "10.0.3.110", vulnerability: "CVE-2022-3172", attack_technique: "T1611", description: "Kubernetes API server cluster breakout" }
    ]
  },
  {
    id: "PATH-007",
    target: "db-01",
    risk_score: 68,
    severity: "medium",
    detectability: "medium",
    hops: [
      { host: "jump-01", ip: "10.0.1.99", vulnerability: "CVE-2024-3094", attack_technique: "T1021", description: "XZ Utils backdoor in SSH bastion host" },
      { host: "app-02", ip: "10.0.3.46", vulnerability: "CVE-2023-20860", attack_technique: "T1055", description: "Spring Framework Security bypass on API controller" },
      { host: "db-01", ip: "10.0.4.100", vulnerability: "CVE-2023-23397", attack_technique: "T1078", description: "Privilege escalation via hardcoded DB administrator credentials" }
    ]
  },
  {
    id: "PATH-008",
    target: "vault-01",
    risk_score: 65,
    severity: "medium",
    detectability: "high",
    hops: [
      { host: "web-01", ip: "10.0.2.12", vulnerability: "CVE-2023-38606", attack_technique: "T1190", description: "Unauthenticated SSRF bypassing internal perimeter filters" },
      { host: "auth-01", ip: "10.0.2.88", vulnerability: "CVE-2023-48795", attack_technique: "T1110", description: "Terrapin SSH prefix truncation attack on OAuth gateway" },
      { host: "vault-01", ip: "10.0.5.20", vulnerability: "CVE-2023-33246", attack_technique: "T1552", description: "RocketMQ RCE leaking master secret key stored in memory" }
    ]
  },
  {
    id: "PATH-009",
    target: "app-02",
    risk_score: 58,
    severity: "medium",
    detectability: "high",
    hops: [
      { host: "cloud-gateway", ip: "10.0.1.5", vulnerability: "CVE-2024-21887", attack_technique: "T1190", description: "Ivanti Connect Secure command injection" },
      { host: "app-02", ip: "10.0.3.46", vulnerability: "CVE-2023-20860", attack_technique: "T1055", description: "Spring Framework Security bypass on API controller" }
    ]
  },
  {
    id: "PATH-010",
    target: "db-02",
    risk_score: 52,
    severity: "medium",
    detectability: "high",
    hops: [
      { host: "jump-01", ip: "10.0.1.99", vulnerability: "CVE-2024-3094", attack_technique: "T1021", description: "XZ Utils backdoor in SSH bastion host" },
      { host: "db-02", ip: "10.0.4.101", vulnerability: "CVE-2022-26134", attack_technique: "T1078", description: "Confluence OGNL injection leading to read replica compromise" }
    ]
  },
  {
    id: "PATH-011",
    target: "k8s-node-02",
    risk_score: 42,
    severity: "low",
    detectability: "high",
    hops: [
      { host: "web-02", ip: "10.0.2.14", vulnerability: "CVE-2023-38606", attack_technique: "T1190", description: "Unauthenticated SSRF bypassing internal perimeter filters" },
      { host: "k8s-node-02", ip: "10.0.3.111", vulnerability: "CVE-2023-2728", attack_technique: "T1068", description: "Kubernetes volume mount privilege escalation" }
    ]
  },
  {
    id: "PATH-012",
    target: "app-01",
    risk_score: 35,
    severity: "low",
    detectability: "high",
    hops: [
      { host: "web-02", ip: "10.0.2.14", vulnerability: "CVE-2023-38606", attack_technique: "T1190", description: "Unauthenticated SSRF bypassing internal perimeter filters" },
      { host: "app-01", ip: "10.0.3.45", vulnerability: "CVE-2022-22965", attack_technique: "T1068", description: "Spring4Shell Remote Code Execution in business service" }
    ]
  }
];

export const mockPatches = [
  {
    id: "PATCH-001",
    vulnerability_id: "CVE-2023-34362",
    host: "cloud-gateway",
    description: "Apply MOVEit Transfer emergency security patch v2023.0.2 to prevent ingress unauthenticated RCE.",
    paths_closed: 3,
    risk_reduction: 42
  },
  {
    id: "PATCH-002",
    vulnerability_id: "CVE-2021-44228",
    host: "web-01",
    description: "Upgrade log4j-core library to v2.17.1 to mitigate Log4Shell JNDI remote code execution.",
    paths_closed: 2,
    risk_reduction: 35
  },
  {
    id: "PATCH-003",
    vulnerability_id: "CVE-2024-3094",
    host: "jump-01",
    description: "Roll back xz-utils library on SSH bastion node from v5.6.0 to stable un-backdoored release v5.4.6.",
    paths_closed: 3,
    risk_reduction: 38
  },
  {
    id: "PATCH-004",
    vulnerability_id: "CVE-2023-23397",
    host: "db-01",
    description: "Enforce strict Kerberos NTLM auth policy & rotate DBA service credentials across primary database cluster.",
    paths_closed: 3,
    risk_reduction: 28
  },
  {
    id: "PATCH-005",
    vulnerability_id: "CVE-2022-3172",
    host: "k8s-node-01",
    description: "Restrict API server egress and upgrade Kubernetes cluster control plane to v1.28.4.",
    paths_closed: 2,
    risk_reduction: 22
  },
  {
    id: "PATCH-006",
    vulnerability_id: "CVE-2023-33246",
    host: "vault-01",
    description: "Deploy RocketMQ security update v5.1.2 and isolate memory secrets with Vault HSM integration.",
    paths_closed: 2,
    risk_reduction: 20
  },
  {
    id: "PATCH-007",
    vulnerability_id: "CVE-2024-21887",
    host: "cloud-gateway",
    description: "Apply Ivanti Connect Secure mitigation script v2.1.0 to eliminate web shell execution vector.",
    paths_closed: 2,
    risk_reduction: 18
  },
  {
    id: "PATCH-008",
    vulnerability_id: "CVE-2023-38606",
    host: "web-02",
    description: "Configure strict URL validation and WAF rules against internal network SSRF probing.",
    paths_closed: 4,
    risk_reduction: 30
  }
];

export const mockHealth = {
  status: "healthy",
  dependencies: {
    recon: "up",
    analysis: "up",
    gateway: "up"
  }
};
