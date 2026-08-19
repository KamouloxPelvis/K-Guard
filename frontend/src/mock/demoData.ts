/**
 * K-Guard Public Demo Mock Data Engine
 * Anonymized, realistic datasets for public live demonstration on k-guard.devopsnotes.org
 * All internal IPs sanitized to safe isolated subnets (172.20.0.x) with zero credential leaks.
 */

export const demoSystemInfo = {
  cluster_version: "v1.31.2+k3s1",
  vps_os: "Debian GNU/Linux 12 (bookworm)",
  uptime: "14 days, 6 hours, 22 mins",
  status: "HEALTHY"
};

export const demoNodeCapacity = {
  cpu_cores: 4,
  memory_total_ki: 8388608 // 8 GB
};

export const demoClusterStatus = [
  {
    name: "K-Guard API Gateway",
    pod_name: "kguard-api-7b8f994d5b-x8q2z",
    status: "RUNNING",
    ip: "172.20.0.10",
    type: "SERVICE",
    namespace: "kguard"
  },
  {
    name: "K-Guard AI Triage Engine",
    pod_name: "kguard-ai-engine-6f5d88c94a-v7n1p",
    status: "RUNNING",
    ip: "172.20.0.11",
    type: "SERVICE",
    namespace: "kguard"
  },
  {
    name: "Falco Runtime Probe",
    pod_name: "falco-daemonset-ebpf-9w3lk",
    status: "SECURE",
    ip: "172.20.0.12",
    type: "DAEMONSET",
    namespace: "security"
  },
  {
    name: "Wazuh Security Agent",
    pod_name: "wazuh-agent-node-kguard-4m2ts",
    status: "SECURE",
    ip: "172.20.0.13",
    type: "AGENT",
    namespace: "security"
  },
  {
    name: "Prometheus Metrics Core",
    pod_name: "prometheus-server-5d97f8c4b2-r9v4l",
    status: "RUNNING",
    ip: "172.20.0.14",
    type: "SERVICE",
    namespace: "monitoring"
  },
  {
    name: "Grafana Dashboards",
    pod_name: "grafana-instance-84d7f57cb8-m1w9k",
    status: "RUNNING",
    ip: "172.20.0.15",
    type: "SERVICE",
    namespace: "monitoring"
  },
  {
    name: "Traefik Ingress Controller",
    pod_name: "traefik-ingress-lb-7d498bc57f-c3k8x",
    status: "RUNNING",
    ip: "172.20.0.16",
    type: "INGRESS",
    namespace: "kube-system"
  },
  {
    name: "CoreDNS Nameserver",
    pod_name: "coredns-internal-648b7f88f9-j2d5p",
    status: "RUNNING",
    ip: "172.20.0.17",
    type: "SERVICE",
    namespace: "kube-system"
  }
];

export const demoPodMetrics: Record<string, Array<{ pod_name: string; cpuUsage: number; memoryUsage: number }>> = {
  kguard: [
    { pod_name: "kguard-api-7b8f994d5b-x8q2z", cpuUsage: 65, memoryUsage: 142 },
    { pod_name: "kguard-ai-engine-6f5d88c94a-v7n1p", cpuUsage: 120, memoryUsage: 380 }
  ],
  security: [
    { pod_name: "falco-daemonset-ebpf-9w3lk", cpuUsage: 45, memoryUsage: 98 },
    { pod_name: "wazuh-agent-node-kguard-4m2ts", cpuUsage: 30, memoryUsage: 64 }
  ],
  monitoring: [
    { pod_name: "prometheus-server-5d97f8c4b2-r9v4l", cpuUsage: 85, memoryUsage: 256 },
    { pod_name: "grafana-instance-84d7f57cb8-m1w9k", cpuUsage: 25, memoryUsage: 110 }
  ],
  "kube-system": [
    { pod_name: "traefik-ingress-lb-7d498bc57f-c3k8x", cpuUsage: 50, memoryUsage: 88 },
    { pod_name: "coredns-internal-648b7f88f9-j2d5p", cpuUsage: 15, memoryUsage: 32 }
  ]
};

export const demoPodLogs = (podName: string): string => {
  const ts = new Date().toISOString();
  return `[${ts}] [INFO]  [kguard-core] Initializing runtime security subsystem...
[${ts}] [INFO]  [ebpf-engine] Kernel probes mounted successfully on node kguard-master-01 (kernel 6.1.0-28-amd64)
[${ts}] [INFO]  [tls-guard] Certificate chain verified with Let's Encrypt Authority. TLS 1.3 negotiated.
[${ts}] [INFO]  [network-sentinel] Ingress / Egress NetworkPolicies enforced across 4 active namespaces.
[${ts}] [INFO]  [falco-stream] eBPF ring buffer active. 0 packet drops detected.
[${ts}] [INFO]  [kguard-ai] Microservice connected via gRPC / REST bridge. LLM triage operational.
[${ts}] [INFO]  [wazuh-sync] Agent heartbeat acknowledged (manager: wazuh.secops.internal, status: ACTIVE).
[${ts}] [INFO]  [metrics-collector] Prometheus scraping target /metrics on port 8000 (latency: 1.4ms).
[${ts}] [OK]    [healthcheck] Pod ${podName} operating within nominal security parameters.`;
};

export const demoSecurityAlerts = [
  {
    id: "ALT-2026-9841",
    source: "Falco eBPF",
    severity: "CRITICAL",
    level: 16,
    message: "Outbound unauthorized connection to suspicious external C2 IP blocked by NetworkPolicy",
    rule_name: "Outbound Connection to Blacklisted Host",
    ai_status: "ENRICHED",
    created_at: new Date(Date.now() - 4 * 60000).toISOString(),
    ai_enrichment: {
      model: "K-Guard AI Engine v0.8.0 (DeepSeek/Mistral)",
      verdict: "MALICIOUS",
      incident_type: "COMMAND_AND_CONTROL",
      risk_level: "CRITICAL",
      confidence_score: 96,
      human_summary: "Container attempted to establish an outbound connection to a flagged C2 IP. Egress was immediately intercepted and neutralized by K-Guard NetworkPolicies.",
      analyst_summary: "Suspicious egress attempt from pod namespace 'staging' targeting port 4444. MITRE ATT&CK T1071 (Application Layer Protocol). Connection dropped at kernel level.",
      investigation_steps: [
        "Verify source container image SHA-256 digest",
        "Enforce complete network isolation on target namespace",
        "Perform memory forensics via eBPF runtime probe"
      ],
      iocs: ["198.51.100.44:4444 (Mock C2)", "Process: /bin/nc.traditional"],
      hypotheses: ["Reverse shell attempt following remote code execution", "Automated external reconnaissance probe"],
      recommended_actions: [
        "Maintain egress traffic lockdown (Network Sentinel)",
        "Rotate namespace secrets and credentials",
        "Restart pod with verified immutable container image"
      ]
    }
  },
  {
    id: "ALT-2026-9838",
    source: "Falco eBPF",
    severity: "HIGH",
    level: 13,
    message: "Terminal shell spawned in container runtime (exec sh/bash detected)",
    rule_name: "Terminal Shell in Container",
    ai_status: "ENRICHED",
    created_at: new Date(Date.now() - 18 * 60000).toISOString(),
    ai_enrichment: {
      model: "K-Guard AI Engine v0.8.0",
      verdict: "SUSPICIOUS",
      incident_type: "EXECUTION",
      risk_level: "HIGH",
      confidence_score: 88,
      human_summary: "Interactive terminal shell spawned inside a production pod. Suspicious operational activity requiring immediate verification.",
      analyst_summary: "Interactive shell invocation detected in production namespace. Parent process: containerd-shim. MITRE ATT&CK T1059.004 (Unix Shell).",
      investigation_steps: [
        "Identify RBAC identity executing kubectl exec",
        "Audit interactive command history in container session",
        "Verify filesystem integrity for modified binaries"
      ],
      iocs: ["User: cluster-admin", "Command: /bin/sh -i"],
      hypotheses: ["Undeclared hotfix or maintenance session", "Local privilege escalation attempt"],
      recommended_actions: [
        "Restrict pod exec privileges via RBAC policies",
        "Audit Kubernetes API control plane logs"
      ]
    }
  },
  {
    id: "ALT-2026-9829",
    source: "Falco eBPF",
    severity: "HIGH",
    level: 12,
    message: "Sensitive file read attempt (/etc/shadow) by non-root process",
    rule_name: "Read Sensitive File Untrusted",
    ai_status: "ENRICHED",
    created_at: new Date(Date.now() - 42 * 60000).toISOString(),
    ai_enrichment: {
      model: "K-Guard AI Engine v0.8.0",
      verdict: "SUSPICIOUS",
      incident_type: "CREDENTIAL_ACCESS",
      risk_level: "HIGH",
      confidence_score: 91,
      human_summary: "Unauthorized attempt to read sensitive system file (/etc/shadow). Access was rejected by container security boundary.",
      analyst_summary: "Unauthorized file read attempt intercepted by AppArmor/SELinux profile. MITRE ATT&CK T1003.008 (/etc/passwd and /etc/shadow).",
      investigation_steps: [
        "Review Linux capabilities assigned to container",
        "Inspect exposed environment variables for secrets"
      ],
      iocs: ["Target: /etc/shadow", "Process: cat"],
      hypotheses: ["Local credential harvesting attempt"],
      recommended_actions: [
        "Enforce runAsNonRoot: true in SecurityContext",
        "Attach default kguard AppArmor/SELinux profile"
      ]
    }
  },
  {
    id: "ALT-2026-9815",
    source: "Falco eBPF",
    severity: "MEDIUM",
    level: 8,
    message: "Kubernetes API namespace enumeration from unauthorized service account",
    rule_name: "K8s API Enumeration",
    ai_status: "ENRICHED",
    created_at: new Date(Date.now() - 110 * 60000).toISOString(),
    ai_enrichment: {
      model: "K-Guard AI Engine v0.8.0",
      verdict: "FALSE_POSITIVE",
      incident_type: "DISCOVERY",
      risk_level: "MEDIUM",
      confidence_score: 75,
      human_summary: "Namespace enumeration performed by authorized Prometheus monitoring probe. False positive confirmed after security correlation.",
      analyst_summary: "Routine service account API call from prometheus-server. Access verified against RBAC RoleBinding.",
      investigation_steps: ["Verify ServiceAccount token against RBAC RoleBinding"],
      iocs: ["SA: monitoring:prometheus-k8s"],
      hypotheses: ["Legitimate metric scraping behavior"],
      recommended_actions: ["Add Falco rule exception macro for Prometheus SA"]
    }
  },
  {
    id: "ALT-2026-9802",
    source: "Falco eBPF",
    severity: "LOW",
    level: 4,
    message: "Package manager binary invocation (apt-get) detected at runtime",
    rule_name: "Package Management in Container",
    ai_status: "ENRICHED",
    created_at: new Date(Date.now() - 240 * 60000).toISOString(),
    ai_enrichment: {
      model: "K-Guard AI Engine v0.8.0",
      verdict: "SUSPICIOUS",
      incident_type: "DEFENSE_EVASION",
      risk_level: "LOW",
      confidence_score: 82,
      human_summary: "Package manager execution detected in running container. Violation of container immutability policy.",
      analyst_summary: "Execution of /usr/bin/apt-get in running workload. Violates container immutability principles.",
      investigation_steps: ["Audit base Dockerfile layer composition"],
      iocs: ["Process: apt-get update"],
      hypotheses: ["Manual installation of debugging tools in live workload"],
      recommended_actions: ["Set readOnlyRootFilesystem: true in PodSpec"]
    }
  }
];

export const demoWazuhOverview = {
  connected: true,
  inventory: {
    connected: true,
    summary: {
      total: 4,
      active: 4,
      disconnected: 0,
      never_connected: 0
    },
    agents: [
      {
        id: "001",
        name: "kguard-master-01",
        status: "active",
        ip: "172.20.0.10",
        group: "default,linux-servers,k3s-controlplane",
        version: "Wazuh v4.14.0",
        last_keep_alive: new Date().toISOString(),
        os: {
          name: "Debian GNU/Linux",
          platform: "debian",
          version: "12 (bookworm)",
          architecture: "x86_64"
        }
      },
      {
        id: "002",
        name: "kguard-worker-node",
        status: "active",
        ip: "172.20.0.20",
        group: "default,linux-servers,k3s-workers",
        version: "Wazuh v4.14.0",
        last_keep_alive: new Date().toISOString(),
        os: {
          name: "Debian GNU/Linux",
          platform: "debian",
          version: "12 (bookworm)",
          architecture: "x86_64"
        }
      },
      {
        id: "003",
        name: "kguard-ai-microservice-vps",
        status: "active",
        ip: "172.20.0.30",
        group: "default,ai-workloads",
        version: "Wazuh v4.14.0",
        last_keep_alive: new Date().toISOString(),
        os: {
          name: "Ubuntu",
          platform: "ubuntu",
          version: "24.04 LTS",
          architecture: "x86_64"
        }
      },
      {
        id: "004",
        name: "kguard-edge-gateway",
        status: "active",
        ip: "172.20.0.40",
        group: "default,ingress-edge",
        version: "Wazuh v4.14.0",
        last_keep_alive: new Date().toISOString(),
        os: {
          name: "Alpine Linux",
          platform: "alpine",
          version: "3.20.2",
          architecture: "x86_64"
        }
      }
    ]
  },
  alerts: {
    available: true,
    total: 18,
    critical: 1,
    high: 3,
    medium: 6,
    low: 8
  },
  posture: {
    sca_available: true,
    vulnerabilities_available: true,
    message: "System compliant with CIS Kubernetes v1.8.0 benchmarks. 0 active critical vulnerabilities."
  }
};

export const demoWazuhAlerts = [
  {
    id: "wazuh-alt-10492",
    timestamp: new Date(Date.now() - 12 * 60000).toISOString(),
    level: 10,
    rule_id: "5710",
    description: "SSHD: Multiple failed authentication attempts from isolated test network",
    firedtimes: 4,
    groups: ["syslog", "sshd", "authentication_failures"],
    agent: {
      id: "001",
      name: "kguard-master-01",
      ip: "172.20.0.10"
    },
    manager: {
      name: "wazuh.secops.internal"
    },
    mitre: {
      ids: ["T1110.001"],
      techniques: ["Password Guessing"],
      tactics: ["Credential Access"]
    },
    location: "/var/log/auth.log",
    decoder: { name: "sshd" },
    predecoder: { program_name: "sshd" },
    data: { srcip: "192.168.10.99" },
    syscheck: {},
    full_log: "sshd[19284]: Failed password for invalid user admin from 192.168.10.99 port 51240 ssh2"
  },
  {
    id: "wazuh-alt-10488",
    timestamp: new Date(Date.now() - 35 * 60000).toISOString(),
    level: 7,
    rule_id: "550",
    description: "Integrity checksum changed for monitored binary in /usr/local/bin",
    firedtimes: 1,
    groups: ["syscheck", "fim", "integrity"],
    agent: {
      id: "002",
      name: "kguard-worker-node",
      ip: "172.20.0.20"
    },
    manager: {
      name: "wazuh.secops.internal"
    },
    mitre: {
      ids: ["T1565.001"],
      techniques: ["Stored Data Manipulation"],
      tactics: ["Impact"]
    },
    location: "syscheck",
    decoder: { name: "syscheck" },
    predecoder: {},
    data: {},
    syscheck: {
      path: "/usr/local/bin/kguard-agent",
      event: "modified",
      sha256_after: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    },
    full_log: "File '/usr/local/bin/kguard-agent' was modified. Integrity checksum recalculated."
  }
];

export const demoSentinelMap = {
  nodes: [
    {
      id: "pod-kguard-api",
      name: "kguard-api",
      namespace: "kguard",
      status: "RUNNING",
      ip: "172.20.0.10",
      role: "API Gateway & Security Orchestrator",
      labels: { app: "kguard-api", tier: "backend", env: "production" },
      is_hardened: true,
      image: "kguard/api:v1.7.0"
    },
    {
      id: "pod-kguard-ai",
      name: "kguard-ai-engine",
      namespace: "kguard",
      status: "RUNNING",
      ip: "172.20.0.11",
      role: "Triage & LLM Context Enrichment",
      labels: { app: "kguard-ai", tier: "ai-service", env: "production" },
      is_hardened: true,
      image: "kguard/ai-engine:v0.8.0"
    },
    {
      id: "pod-falco",
      name: "falco-ebpf-probe",
      namespace: "security",
      status: "SECURE",
      ip: "172.20.0.12",
      role: "Kernel Runtime Detection (eBPF)",
      labels: { app: "falco", tier: "security-daemonset" },
      is_hardened: true,
      image: "falcosecurity/falco:0.38.0"
    },
    {
      id: "pod-wazuh",
      name: "wazuh-agent",
      namespace: "security",
      status: "SECURE",
      ip: "172.20.0.13",
      role: "Host & Endpoint Compliance (SIEM/XDR)",
      labels: { app: "wazuh-agent", tier: "siem" },
      is_hardened: true,
      image: "wazuh/wazuh-agent:4.14.0"
    },
    {
      id: "pod-prometheus",
      name: "prometheus-core",
      namespace: "monitoring",
      status: "RUNNING",
      ip: "172.20.0.14",
      role: "Time-Series Metrics Collector",
      labels: { app: "prometheus", tier: "monitoring" },
      is_hardened: true,
      image: "prom/prometheus:v2.53.0"
    },
    {
      id: "pod-traefik",
      name: "traefik-ingress",
      namespace: "kube-system",
      status: "RUNNING",
      ip: "172.20.0.16",
      role: "Ingress TLS Proxy & Rate Limiter",
      labels: { app: "traefik", tier: "ingress" },
      is_hardened: true,
      image: "traefik:v3.1.0"
    }
  ],
  edges: [
    { source: "pod-traefik", target: "pod-kguard-api", label: "HTTPS / 443 -> 8000 (TLS)", sourceIp: "172.20.0.16", targetIp: "172.20.0.10" },
    { source: "pod-kguard-api", target: "pod-kguard-ai", label: "gRPC / 8080 (Mutual TLS)", sourceIp: "172.20.0.10", targetIp: "172.20.0.11" },
    { source: "pod-falco", target: "pod-kguard-api", label: "Unix Socket / REST Event Stream", sourceIp: "172.20.0.12", targetIp: "172.20.0.10" },
    { source: "pod-wazuh", target: "pod-kguard-api", label: "Wazuh API Integration / 55000", sourceIp: "172.20.0.13", targetIp: "172.20.0.10" },
    { source: "pod-prometheus", target: "pod-kguard-api", label: "Metrics Scrape / 8000", sourceIp: "172.20.0.14", targetIp: "172.20.0.10" }
  ],
  namespaces: ["all-protected", "kguard", "security", "monitoring", "kube-system"]
};

export const demoSentinelStatus = {
  deployed: true,
  security_score: 94,
  confidence: 98,
  coverage: 100,
  assessed_at: new Date().toISOString(),
  summary: {
    passed: 28,
    failed: 0,
    unknown: 2
  },
  categories: {
    isolation: { score: 96, weight: 35, passed: 10, failed: 0, unknown: 0 },
    encryption: { score: 100, weight: 25, passed: 8, failed: 0, unknown: 0 },
    least_privilege: { score: 90, weight: 25, passed: 7, failed: 0, unknown: 1 },
    monitoring: { score: 92, weight: 15, passed: 3, failed: 0, unknown: 1 }
  },
  findings: [
    {
      id: "FND-01",
      severity: "low" as const,
      namespace: "monitoring",
      pod: "prometheus-core",
      message: "Prometheus metrics endpoint exposed on internal pod network (nominal for cluster telemetry)."
    }
  ]
};

export const demoHardeningPlan = {
  groups: [
    {
      id: "grp-zero-trust",
      label: "Zero-Trust Ingress/Egress Isolation",
      description: "Default Deny all inter-namespace traffic except explicitly allowed security service ports.",
      count: 4,
      risk: "low" as const,
      policies: [
        { name: "default-deny-all", namespace: "kguard", application: "kguard-core" },
        { name: "allow-traefik-to-api", namespace: "kguard", application: "kguard-api", port: 8000 },
        { name: "allow-api-to-ai", namespace: "kguard", application: "kguard-ai", port: 8080 },
        { name: "allow-prometheus-scrape", namespace: "monitoring", application: "prometheus", port: 9090 }
      ]
    }
  ],
  total_policies: 4,
  namespaces: ["kguard", "security", "monitoring"],
  workloads: [
    { app: "kguard-api", namespace: "kguard", port: 8000, policy: "allow-traefik-to-api" },
    { app: "kguard-ai-engine", namespace: "kguard", port: 8080, policy: "allow-api-to-ai" }
  ],
  ordering: ["default-deny-all", "allow-traefik-to-api", "allow-api-to-ai", "allow-prometheus-scrape"],
  read_only: true
};

export const demoSettingsData = {
  storage: {
    status: "HEALTHY",
    disks: {
      "/": { total_gb: 40.0, used_gb: 12.4, free_gb: 27.6, percent: 31 },
      "/var/log": { total_gb: 15.0, used_gb: 3.1, free_gb: 11.9, percent: 21 }
    },
    database_present: true,
    timestamp: new Date().toISOString()
  },
  webex: {
    enabled: true,
    configured: true,
    room_id: "secops-incident-room-demo"
  }
};
