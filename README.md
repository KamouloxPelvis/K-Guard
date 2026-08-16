# 🛡️ K-Guard

**Current release:** `v1.7.0` — Native Security Monitoring, Runtime Observability & Grouped Network Policies

> A native security, observability, and network-governance platform tailored for Kubernetes / K3s clusters.

[![OpenSSF Baseline](https://www.bestpractices.dev/projects/12124/baseline)](https://www.bestpractices.dev/projects/12124/baseline)
[![Cisco DevNet Code Exchange](https://static.production.devnetcloud.com/codeexchange/assets/images/devnet-published.svg)](https://developer.cisco.com/codeexchange/github/repo/KamouloxPelvis/K-Guard)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-K3s-326CE5?logo=kubernetes&logoColor=white)](https://k3s.io)

---

### 🔗 Quick Links

- 🚀 **Live Demo:** [https://app.devopsnotes.org](https://app.devopsnotes.org)
- 🌐 **Author Portfolio:** [https://devopsnotes.org](https://devopsnotes.org)
- 📖 **Technical Blog:** [https://blog.devopsnotes.org](https://blog.devopsnotes.org)
- 📑 **Architecture Dossier (PDF):** [Dossier de Conception Technique v1.7.0](https://devopsnotes.org/docs/Dossier_de_conception_technique_K-Guard_v1.7.0.pdf)

---

## 🌟 Core Pillars

| Pillar | Technology | Description |
|---|---|---|
| **⚡ Runtime Security** | **Falco + Fluent Bit** | Real-time container threat detection via kernel/eBPF telemetry without requiring external ELK/Kibana dashboards. |
| **🤖 AI-Enriched Triage** | **K-Guard AI + Ollama** | Contextual natural-language threat synthesis, automated risk scoring, and MITRE ATT&CK technique identification. |
| **🛡️ Endpoint Compliance** | **Wazuh 4.14 + Indexer** | Native endpoint inventory, CIS benchmark tracking, and security alerts mediated safely by the backend. |
| **🌐 Network Sentinel** | **K8s NetworkPolicies** | Visual topology mapping, real-time posture scoring, and 1-click grouped micro-segmentation with zero-trust baseline. |
| **🔔 Instant Alerting** | **Cisco Webex API** | Real-time incident dispatching to operational Webex security rooms. |

---

## 🏗️ Architecture

K-Guard follows a **backend-mediated, zero-trust architecture**. Protected infrastructure APIs and security credentials are never exposed to the client browser.

```text
                         ┌────────────────────┐
                         │   K-Guard Web UI   │
                         │ Vue 3 / TypeScript │
                         └─────────┬──────────┘
                                   │ HTTPS / JWT
                                   ▼
                         ┌────────────────────┐
                         │  K-Guard Backend   │
                         │  FastAPI / Python  │
                         └──────┬─────┬───────┘
                                │     │
                 ┌──────────────┘     └──────────────┐
                 ▼                                   ▼
        ┌─────────────────┐                 ┌─────────────────┐
        │   Kubernetes /  │                 │ Security Inputs │
        │  K3s Workloads  │                 │  Falco / Wazuh  │
        └────────┬────────┘                 └────────┬────────┘
                 │                                   │
                 │                                   ▼
                 │                         ┌─────────────────┐
                 │                         │   K-Guard AI    │
                 │                         │ Local LLM Engine│
                 │                         └────────┬────────┘
                 │                                   │
                 └─────────────────┬─────────────────┘
                                   ▼
                         ┌────────────────────┐
                         │ Native K-Guard UI  │
                         │ Runtime / Wazuh /  │
                         │ Sentinel / SRE     │
                         └────────────────────┘
```

### ⚡ Runtime Event Ingestion Pipeline

```text
Falco (eBPF Engine) ──► Fluent Bit ──► K-Guard AI (Ollama) ──► K-Guard SOC Console
```

---

## 📸 Modules & Features

### 1. System Overview
Centralizes live cluster health, node resource saturation (CPU/RAM), running workload counts, and pod log investigation tools.

![K-Guard System Overview](frontend/public/screenshots/kguard-system_overview-1.png)

---

### 2. Runtime Security & AI Investigation Assistant
Aggregates live Falco security events and enriches them with **K-Guard AI** for instant threat context, natural-language explanation, and confidence-scored risk ratings.

![K-Guard Security Runtime](frontend/public/screenshots/kguard-security-2.png)

---

### 3. Endpoint & Compliance (Wazuh)
Provides a unified view of active Wazuh agents, operating system details, keep-alive heartbeats, and correlated security alerts without exposing direct Wazuh credentials.

![K-Guard Wazuh Endpoint Inventory](frontend/public/screenshots/kguard-wazuh-endpoints-1.png)

---

### 4. Network Sentinel (Micro-Segmentation & Posture)
- **Topological Map:** Real-time visualization of inter-workload flows.
- **Posture Score:** Weighted security index evaluating network isolation, pod security standards, and exposure.
- **Grouped Hardening:** Apply or deactivate progressive zero-trust policies (*Infrastructure allow, Application bridges, Baseline deny*) with explicit confirmation.

![K-Guard Sentinel Network Map](frontend/public/screenshots/kguard-sentinel_map-1.png)
![K-Guard Sentinel Security Posture](frontend/public/screenshots/kguard-sentinel_security-posture.png)

---

### 5. Settings & Integrations
Manage persistent database storage, review upstream service connectivity (Wazuh, Indexer, K3s), and configure Cisco Webex bot tokens securely.

![K-Guard Webex Integration](frontend/public/screenshots/kguard-webex.png)

---

## 🚀 Quick Start

### Prerequisites
- Linux host (Debian 12 / Ubuntu 22.04+ / Amazon Linux)
- K3s or standard Kubernetes cluster
- Root or `sudo` privileges

### Interactive Installation

```bash
# 1. Clone the repository
git clone https://github.com/KamouloxPelvis/k-guard.git
cd k-guard

# 2. Run the automated installer
cd installer
chmod +x kguard-install
sudo ./kguard-install
```

The installer guides you through:
- Creating the primary administrator credentials.
- In-cluster / external service discovery.
- Configuring optional Wazuh and Webex endpoints.
- Generating ingress routes and TLS bindings.

### Interactive API Documentation
Interactive OpenAPI / Swagger UI documentation is accessible at:
```text
https://<your-kguard-domain>/docs
```

![K-Guard API Documentation](frontend/public/screenshots/kguard-docs.png)

---

## 🔒 Security Model

- **Backend Mediation:** Client browsers never communicate directly with the Kubernetes API, Wazuh Manager, or internal credentials stores.
- **Credential Isolation:** API keys, database secrets, and TLS certs remain confined to Kubernetes secrets and in-memory backend sessions.
- **Read-Only Upstream Integration:** Wazuh and Indexer queries are strictly read-only from the user interface.
- **Explicit Network Mutations:** Network Sentinel operations require explicit confirmation before applying or deleting `NetworkPolicy` manifests.
- **Least Privilege:** K-Guard runs in hardened containers with non-root execution and minimal Linux capabilities.

---

## ⚖️ Disclaimer

**K-Guard** is developed as a modular DevSecOps platform and security governance tool. While designed following industry standards (least privilege, zero-trust network segmentation, eBPF telemetry), it is continuously evolving and should be tested and validated before production deployment.

---

## 📄 License

K-Guard is open-source software licensed under the **[Apache License, Version 2.0](LICENSE)**.

---

## 👤 Author & Contact

**Kamal Guidadou** — *Administrateur Systèmes & Réseaux · Spécialiste DevSecOps & Cloud*

- 🌐 **Portfolio:** [https://devopsnotes.org](https://devopsnotes.org)
- 📝 **Blog:** [https://blog.devopsnotes.org](https://blog.devopsnotes.org)
- 💼 **LinkedIn:** [linkedin.com/in/kamal-guidadou](https://www.linkedin.com/in/kamal-guidadou)
- 🐙 **GitHub:** [@KamouloxPelvis](https://github.com/KamouloxPelvis)
- 🏅 **Cisco DevNet:** [DevNet Code Exchange Repository](https://developer.cisco.com/codeexchange/github/repo/KamouloxPelvis/K-Guard)