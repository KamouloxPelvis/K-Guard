# K-Guard

**Current release:** `v1.7.0` — Grouped Network Security Policies

> A security and monitoring platform that helps protect K3s clusters from a single dashboard.

[![OpenSSF Baseline](https://www.bestpractices.dev/projects/12124/baseline)](https://www.bestpractices.dev/projects/12124)

[![Cisco DevNet Code Exchange](https://static.production.devnetcloud.com/codeexchange/assets/images/devnet-published.svg)](https://developer.cisco.com/codeexchange/github/repo/KamouloxPelvis/K-Guard)

---

## ⚠️ Disclaimer

**K-Guard** is engineered in alignment with industry security practices and is published on the Cisco DevNet Code Exchange platform.

However, K-Guard is a personal and experimental Minimum Viable Product designed as a research and learning platform for DevSecOps security architectures.

The platform is continuously evolving and must be reviewed, tested, and hardened before being used in a production environment.

K-Guard does not replace:

- A complete Security Operations Center process.
- A vulnerability-management program.
- An incident-response plan.
- A business-continuity strategy.
- An independent security assessment.
- Professional Kubernetes and infrastructure administration.

---

## 📍 Summary

- [Overview](#overview)
- [Architecture](#architecture)
- [Key Capabilities](#key-capabilities)
- [System Overview](#system-overview)
- [Runtime Security](#runtime-security)
- [Wazuh Security Monitoring](#wazuh-security-monitoring)
- [Network Sentinel](#network-sentinel)
- [Cisco Webex Notifications](#cisco-webex-notifications)
- [Security Model](#security-model)
- [Installation](#installation)
- [Dashboard Access](#dashboard-access)
- [Configuration](#configuration)
- [API Documentation](#api-documentation)
- [Troubleshooting](#troubleshooting)
- [Contact](#contact)

---

## Overview

K-Guard is a security governance and observability platform designed to help protect K3s clusters from a single web dashboard.

It brings together infrastructure monitoring, runtime security, endpoint visibility, network-security controls, and operational notifications.

K-Guard is designed for infrastructure and security teams that need a clearer view of their Kubernetes environment without switching continuously between several independent tools.

The platform currently integrates:

- **K3s / Kubernetes** for cluster and workload monitoring.
- **Falco** for runtime threat detection.
- **Fluent Bit** for log forwarding.
- **Elasticsearch and Kibana** for event storage and investigation.
- **Wazuh** for endpoint inventory, security posture, and alert visibility.
- **Cisco Webex** for operational and security notifications.
- **Kubernetes NetworkPolicies** for network-isolation controls.
- **Ansible automation** for controlled Sentinel policy management.

---

## Architecture

K-Guard follows a backend-mediated architecture:

```text
                         ┌────────────────────┐
                         │   K-Guard Web UI   │
                         │ Vue 3 / TypeScript │
                         └─────────┬──────────┘
                                   │
                                   │ HTTPS / JWT
                                   ▼
                         ┌────────────────────┐
                         │  K-Guard Backend   │
                         │ FastAPI / Python   │
                         └─────────┬──────────┘
                                   │
          ┌────────────────────────┼────────────────────────┐
          │                        │                        │
          ▼                        ▼                        ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Kubernetes API  │     │ Wazuh Manager   │     │ Runtime Security│
│ K3s workloads   │     │ Security data   │     │ Falco / Elastic │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                   │
                                   ▼
                         ┌────────────────────┐
                         │ Security Services  │
                         │ Wazuh / Kibana     │
                         └────────────────────┘
```

The browser communicates with the K-Guard backend and does not directly access Wazuh Manager or other protected infrastructure services.

This architecture keeps service credentials and backend integrations isolated from the user interface.

---

## Key Capabilities

K-Guard provides a unified interface for:

- Monitoring cluster and workload health.
- Reviewing runtime-security events.
- Reviewing Wazuh endpoint inventory.
- Viewing Wazuh security posture indicators.
- Reviewing Wazuh alerts.
- Visualizing network relationships between workloads.
- Reviewing NetworkPolicy security posture.
- Managing grouped Sentinel policy operations.
- Sending notifications through Cisco Webex.
- Accessing interactive API documentation for administrators and integrators.

---

## System Overview

The **System Overview** page provides a high-level view of the monitored Kubernetes environment.

It helps administrators review:

- Workload availability.
- Namespace and application visibility.
- CPU usage.
- Memory usage.
- Pod addresses.
- Runtime status.
- Cluster latency.
- K3s and host information.

![K-Guard System Overview](frontend/public/screenshots/kguard-system_overview-1.png)

The additional overview screen provides a broader view of monitored services and infrastructure components.

![K-Guard System Overview Details](frontend/public/screenshots/kguard-system_overview-2.png)

---

## Runtime Security

The **Runtime Security** module provides visibility into suspicious activity detected inside the cluster.

It is designed around a security-event pipeline based on Falco, Fluent Bit, Elasticsearch, and Kibana.

The module provides visibility into:

- Runtime security events.
- Suspicious container behavior.
- Kubernetes-related activity.
- Falco detections.
- Event forwarding and storage.
- Investigation data available through Kibana.

![K-Guard Runtime Security](frontend/public/screenshots/kguard-security.png)

![K-Guard Runtime Security Events](frontend/public/screenshots/kguard-security-2.png)

The runtime-security workflow can be represented as follows:

```text
Runtime activity
      │
      ▼
Falco detection
      │
      ▼
Fluent Bit forwarding
      │
      ▼
Elasticsearch storage
      │
      ▼
Kibana investigation
```

---

## Wazuh Security Monitoring

K-Guard integrates Wazuh into its security dashboard to provide endpoint inventory, security posture, and alert visibility.

The integration is read-only from the K-Guard interface.

It helps administrators:

- Monitor endpoint availability.
- Review endpoint operating systems.
- Review agent status.
- Identify disconnected endpoints.
- Review security posture indicators.
- Investigate recent security alerts.
- Search monitored assets.
- Centralize Wazuh visibility with cluster and runtime-security information.

Wazuh credentials and authentication tokens remain handled by the K-Guard backend and are not exposed to the browser.

### Security Posture

The Security Posture view provides a normalized security-focused overview of monitored endpoints.

![K-Guard Wazuh Security Posture](frontend/public/screenshots/kguard-wazuh-security-posture.png)

### Security Alerts

The Alerts view centralizes Wazuh alerts surfaced by the K-Guard backend.

It is designed to help administrators:

- Review active and recent alerts.
- Identify endpoint-related security events.
- Review alert activity.
- Correlate alerts with monitored assets.
- Keep Wazuh credentials confined to the backend.

![K-Guard Wazuh Alerts](frontend/public/screenshots/kguard-wazuh-alerts-1.png)

![K-Guard Wazuh Alert Details](frontend/public/screenshots/kguard-wazuh-alerts-2.png)

### Endpoint Inventory

The Endpoint & Compliance view provides a normalized inventory of monitored Wazuh agents.

It displays information such as:

- Total managed endpoints.
- Active agents.
- Disconnected agents.
- Endpoint hostname.
- Agent identifier.
- Agent version.
- IP address.
- Operating system.
- Architecture.
- Wazuh agent group.
- Last keep-alive timestamp.

![K-Guard Wazuh Endpoint Inventory](frontend/public/screenshots/kguard-wazuh-endpoints-1.png)

![K-Guard Wazuh Endpoint Details](frontend/public/screenshots/kguard-wazuh-endpoints-2.png)

---

## Network Sentinel

Network Sentinel is K-Guard's network-security module.

It provides a controlled interface for reviewing the cluster's network-isolation posture and managing groups of Kubernetes NetworkPolicies.

The module helps administrators:

- Visualize network relationships between workloads.
- Review the current security posture.
- Identify security recommendations.
- Group related network controls.
- Apply selected policy groups through an explicit confirmation workflow.
- Reduce unnecessary east-west traffic.
- Preserve required application and infrastructure flows.

![K-Guard Network Sentinel Map](frontend/public/screenshots/kguard-sentinel_map-1.png)

Additional network views provide different perspectives on workload relationships and network segmentation.

![K-Guard Network Sentinel Map Details](frontend/public/screenshots/kguard-sentinel_map-2.png)

![K-Guard Network Sentinel Relationships](frontend/public/screenshots/kguard-sentinel_map-3.png)

### Policy Groups

Sentinel groups related policies into logical security domains:

- Security exceptions.
- Infrastructure access.
- Application bridges.
- External access.
- Namespace baseline protection.

This grouped approach makes it easier to review the purpose and scope of a network-security operation before confirming it.

![K-Guard Sentinel Policies](frontend/public/screenshots/kguard-sentinel_policies.png)

### Security Posture

The Sentinel security-posture view helps administrators understand the current level of network isolation and the areas that require attention.

![K-Guard Sentinel Security Posture](frontend/public/screenshots/kguard-sentinel_security-posture.png)

### Security Recommendations

K-Guard can present recommendations intended to support a progressive Zero-Trust approach.

![K-Guard Sentinel Security Recommendations](frontend/public/screenshots/kguard-sentinel_security-recommendations.png)

Network Sentinel is designed to support progressive segmentation rather than an indiscriminate application of network restrictions.

Network-policy changes should always be reviewed and tested carefully because they may affect:

- DNS resolution.
- Ingress access.
- Monitoring.
- Application communication.
- Security services.
- External integrations.

---

## Cisco Webex Notifications

K-Guard can send security and operational notifications to a Cisco Webex room.

To configure the integration:

1. Open the **Settings** page.
2. Enable Cisco Webex notifications.
3. Enter the Bot Access Token.
4. Enter the destination Room ID.
5. Save the configuration.

The token is handled by the K-Guard backend and must not be shared publicly.

![K-Guard Settings](frontend/public/screenshots/kguard-settings.png)

![K-Guard Webex Integration](frontend/public/screenshots/kguard-webex.png)

---

## Security Model

K-Guard is designed around several security principles.

### Backend-Mediated Integrations

Protected integrations are handled by the K-Guard backend.

The browser does not directly communicate with:

- Wazuh Manager.
- Protected Kubernetes services.
- Internal security APIs.
- Credential stores.

### Credential Protection

Sensitive credentials are handled by the backend and must never be committed to the repository or included in screenshots, issue reports, or public documentation.

This includes:

- Wazuh credentials.
- Webex tokens.
- Kubernetes credentials.
- TLS private keys.
- JWT signing keys.
- Administrator passwords.

### Read-Only Wazuh Integration

The Wazuh integration exposed through K-Guard is read-only.

K-Guard does not use the dashboard to:

- Enroll Wazuh agents.
- Restart Wazuh agents.
- Modify Wazuh rules.
- Change Wazuh policies.
- Expose Wazuh authentication tokens.

### Explicit Sentinel Actions

Network Sentinel policy operations require explicit user confirmation.

The interface supports a review step before applying or removing selected policy groups.

Policy removal is restricted to Sentinel-managed policy resources.

### Least Privilege

Before a production deployment, the underlying environment should be reviewed to ensure that:

- Service permissions are limited to required operations.
- Unused access rights are removed.
- Administrative accounts use strong credentials.
- Access to the dashboard is restricted.
- Persistent data is backed up.
- Security integrations are regularly reviewed.

---

## Installation

K-Guard is deployed using the installation process provided with the project.

The installer prepares the required application components and guides the administrator through the initial configuration.

### Requirements

- Debian or Ubuntu Server.
- 64-bit compatible system.
- K3s cluster.
- Administrator or sudo access.
- Internet access during installation.
- A domain name or server address for dashboard access.

### Install K-Guard

Clone the repository:

```bash
git clone https://github.com/KamouloxPelvis/k-guard.git
cd k-guard
```

Start the installer:

```bash
cd installer
chmod +x kguard-install
sudo ./kguard-install
```

Follow the installer instructions to:

- Create the initial administrator account.
- Configure the application.
- Configure optional security integrations.
- Prepare the dashboard access address.

After installation, open the dashboard using the address configured for the server.

The deployment process and internal infrastructure configuration are intentionally kept separate from normal dashboard usage.

---

## Dashboard Access

Open K-Guard using the address configured during installation:

```text
https://<your-domain>
```

or:

```text
http://<your-server-address>
```

After signing in, the dashboard provides access to:

- System Overview.
- Runtime Security.
- Endpoint & Compliance.
- Network Sentinel.
- Settings.

The dashboard is designed to centralize the main security and monitoring information in one place.

---

## Configuration

Most K-Guard configuration is performed through the web interface.

From the **Settings** page, administrators can configure available integrations such as Cisco Webex and review the connection status of supported security services.

Sensitive credentials are handled by the backend and should never be added to:

- The Git repository.
- Screenshots.
- Issue reports.
- Chat messages.
- Public documentation.
- Frontend source code.

---

## API Documentation

K-Guard provides interactive API documentation through Swagger UI for administrators and integrators.

The documentation is available through:

```text
http://<your-domain-or-ip>/docs
```

The API documentation provides an overview of the available authenticated services and integration endpoints.

![K-Guard API Documentation](frontend/public/screenshots/kguard-docs.png)

---

## Troubleshooting

### The dashboard cannot be reached

Check that:

- The server is online.
- The configured domain points to the correct server.
- The HTTPS certificate is valid.
- The installation completed successfully.
- The browser is using the correct dashboard address.

### Wazuh information is unavailable

Check that:

- The Wazuh integration is configured.
- The Wazuh services are running.
- The credentials provided during installation are still valid.
- The K-Guard backend can reach the Wazuh service.

If the problem persists, contact the person responsible for the K-Guard installation.

### Webex notifications are not received

Check that:

- Cisco Webex is enabled in **Settings**.
- The Bot Access Token is valid.
- The Room ID is correct.
- The Webex room accepts messages from the configured bot.

### Network Sentinel data is unavailable

Check that:

- The cluster is reachable.
- The required security services are operational.
- The network-security integration is correctly configured.
- The requested operation was confirmed in the interface.

### A new feature is not visible

Try the following:

1. Refresh the page.
2. Clear the browser cache.
3. Sign out and sign in again.
4. Contact the person responsible for the K-Guard installation if the issue remains.

---

## Contact

© 2026 **Kamal Guidadou** — SysAdmin & DevSecOps

- Portfolio: <https://portfolio.devopsnotes.org>
- Technical blog: <https://blog.devopsnotes.org>
- Cisco DevNet Code Exchange: <https://developer.cisco.com/codeexchange/github/repo/KamouloxPelvis/K-Guard>
- GitHub: <https://github.com/KamouloxPelvis/k-guard>