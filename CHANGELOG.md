# Changelog

All notable changes to this project will be documented in this file.

## [1.6.0] - 2026-07-25

### Added
- **Wazuh Security Alerts**: Added a dedicated read-only dashboard page for Wazuh alert visibility inside K-Guard.
- **Wazuh Security Posture**: Added a new posture-oriented view to expose Wazuh security context beyond endpoint inventory.
- **Wazuh Alert APIs**: Added backend routes for Wazuh alert retrieval and overview aggregation.
- **Frontend Navigation**: Added dashboard navigation entries for the new Wazuh security views.
- **Release Documentation**: Added README and release-level documentation updates for the new Wazuh security capabilities.

### Changed
- **Application Version**: Bumped K-Guard version from `1.5.0` to `1.6.0`.
- **Wazuh Coverage**: Expanded the Wazuh integration from endpoint inventory and compliance visibility to include security alerts and posture-oriented views.
- **Operational Visibility**: Improved the security monitoring experience by surfacing Wazuh-derived security data directly in the K-Guard interface.

### Security
- Preserved the backend-only Wazuh access model: browser clients still do not communicate directly with the Wazuh Manager API.
- Preserved the read-only scope of the Wazuh integration for alert and posture visualization.
- Continued strict separation of Wazuh credentials and tokens from the frontend runtime.

### Validation
- Verified successful access to `GET /api/wazuh/alerts`.
- Verified successful access to `GET /api/wazuh/overview`.
- Verified successful rendering of the new Wazuh security views in the K-Guard dashboard.
- Verified successful build, deployment, and K3s rollout for the `v1.6.0` release candidate.

## [1.5.0] - 2026-07-20

### Added
- **Wazuh Endpoint & Compliance**: Added a new read-only dashboard page for Wazuh-managed endpoint inventory.
- **Endpoint Inventory**: Added visibility into agent status, hostname, IP address, operating system, architecture, group, agent version, and last keep-alive timestamp.
- **Wazuh API Integration**: Added the protected `GET /api/wazuh/agents` endpoint for normalized Wazuh agent inventory retrieval.
- **Secure Backend Client**: Added a backend-only Wazuh API client with temporary in-memory JWT caching and automatic re-authentication.
- **Navigation**: Added the **Endpoint & Compliance** route and sidebar navigation entry.
- **Documentation**: Added Wazuh deployment, credentials, TLS validation, API usage, CI/CD, security, and troubleshooting guidance to the README.

### Changed
- **Application Version**: Bumped K-Guard version from `1.4.0` to `1.5.0`.
- **Security Architecture**: K-Guard now retrieves Wazuh data exclusively through its backend; Wazuh credentials and authentication tokens never reach the browser.
- **TLS Configuration**: Updated the Wazuh Manager API certificate to include Kubernetes Service DNS SANs:
  - `wazuh-manager-service`
  - `wazuh-manager-service.k-guard`
  - `wazuh-manager-service.k-guard.svc`
  - `wazuh-manager-service.k-guard.svc.cluster.local`
- **Certificate Trust**: Added the Wazuh API CA certificate as a read-only Kubernetes Secret mounted in the K-Guard workload.
- **Deployment Configuration**: Added Wazuh API URL, credentials, and CA-file configuration to the K-Guard Kubernetes deployment.
- **CI/CD Documentation**: Documented SHA-based container image deployment and recommended immutable image tags for Kubernetes releases.

### Security
- Enforced strict TLS certificate and hostname validation for K-Guard to Wazuh Manager API communication.
- Added Kubernetes Secret-based handling for Wazuh API credentials and the trusted CA certificate.
- Preserved the read-only scope of the Wazuh integration: no agent enrollment, configuration changes, remediation, or credential exposure from the K-Guard UI.

### Validation
- Verified TLS connectivity from the K-Guard pod to the Wazuh Manager API.
- Verified Wazuh API authentication with HTTP `200`.
- Verified Wazuh agent inventory retrieval with HTTP `200`.
- Verified successful K-Guard image build, GitHub Actions deployment, and K3s rollout.

## [1.3.1] - 2026-06-18

### Changed
- **Infrastructure**: Complete migration from Systemd/VPS-bound services to Kubernetes-native architecture (K3s).
- **Network Configuration**: Port changed from `8445` to `8000` to align with internal cluster networking.
- **Installer**: Refactored `main.go` to handle K8s namespace initialization and secret management.
- **Documentation**: Updated README to reflect K8s deployment procedures and removed obsolete Systemd management commands.
- **Frontend**: Stabilized `SentinelView` component with `v-show` directives and improved lifecycle handling (`onActivated`).

## [1.2.1] - 2026-06-15

### Fixed
Port Migration: Resolved network conflicts by migrating the API/Frontend service from port 8443 to 8445.

Auth Stability: Resolved internal 500 errors during authentication by optimizing middleware stack handling.

Asset Serving: Corrected static file resolution logic in FastAPI to properly serve the Vue.js frontend build from /frontend/dist.

Instrumentation: Refined Prometheus middleware to ensure compatible metric collection without breaking router path resolution.

Infrastructure
Updated systemd service configuration to align with the new port architecture.

Updated environment variable definitions to ensure robust path resolution across development and production environments.

## [1.2.0] - 2026-05-12

### Added
- **Universal Go Installer**: Implemented a robust binary-based installation engine for one-click deployments.
- **Automated Frontend Bridge**: The installer now automatically links the Vue.js production build (`dist`) to the FastAPI backend (`static`), ensuring "Zero-Touch" UI availability.
- **Global CLI Command**: Added the `kguard` command for instant access to logs, status, and Kubernetes diagnostics.

### Changed
- **Path Resolution**: Migrated from relative execution paths to absolute path detection using `os.Executable()`, making the installer bulletproof regardless of the working directory.
- **Service Management**: Refactored the Systemd unit logic to ensure a safe and idempotent restart sequence.
- **Code Standards**: Updated all internal installer comments to international English standards (Cisco/SRE compliant).

### Fixed
- **Runtime Error**: Resolved the critical "static/index.html not found" error by ensuring the deployment bridge is created before the service starts.
- **Idempotency**: Fixed "file exists" errors during re-installation by implementing proactive cleanup of legacy symbolic links.

## [1.1.5] - 2026-04-24

### Changed
- **Sentinel Audit Logic**: Pivoted diagnostics toward strict isolation validation (Zero-Trust) instead of simple connectivity.
- **Audit UI**: Cleaned up the test terminal to focus exclusively on critical security metrics (Internal Mesh & Egress).

### Fixed
- **False Negatives**: Removed failures related to external DNS in hardened environments, prioritizing proof of network air-gapping and isolation.

## [1.1.4] - 2026-04-24

### Added
- **Sentinel RBAC Identity**: Deployed a dedicated `ServiceAccount` (`sentinel-auditor`) for diagnostic pods, ensuring secure and authorized connectivity checks.
- **Enhanced SRE Diagnostics**: New `/debug-storage` backend endpoint to monitor Persistent Volume (PV) health and Trivy cache integrity.
- **Dynamic Port Mapping**: The Ansible engine now automatically extracts container ports to maintain service availability during Zero-Trust hardening.

### Changed
- **Webex Resilience**: Refactored `CiscoWebexNotifier` to support multiple JSON report schemas, preventing ChatOps notification failures.
- **Structured Logging**: Replaced standard outputs with a centralized SRE-compliant logging system (`INFO`, `WARNING`, `ERROR`).
- **Network Policy Hardening**: Updated `audit_exception.j2` with broader DNS selectors to ensure compatibility across various K3s distributions.

### Fixed
- **Sentinel Audit**: Resolved "All Fails" status in connectivity tests by aligning Network Policies and ServiceAccounts for the diagnostic pod.
- **Data Persistence**: Fixed background task crashes in `run_and_store_scan` when encountering unexpected report structures.
- **System Overview**: Fixed the `cluster-status` route to ensure the Dashboard correctly populates pod and node topology.

## [1.1.0] - 2026-04-23

### Added
- Strict TypeScript interfaces for Pods, Nodes, and Network Edges.
- New connectivity test terminal within the Network Sentinel UI.
- Security scoring logic based on micro-segmentation status.

### Changed
- **Major**: Migrated the entire network layer from Axios to the native Fetch API.
- Refactored the API service with a custom wrapper for enhanced error handling.
- Updated UI documentation and comments to international SRE standards.

### Fixed
- Resolved production UI crashes related to null data from the K3s API.
- Fixed Cisco Webex integration synchronization logic.
- Stabilized topology map rendering in SentinelView.

## [1.0.0] - 2026-03-09

### Added
- Initial release of K-Guard MVP.
- Trivy security scanning integration.
- ChatOps alerting via Cisco Webex.
- Interactive Swagger UI documentation.
- Network Sentinel powered by Ansible for Zero-Trust policies.