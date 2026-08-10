# Security Policy

## Project Status

K-Guard is an actively developed security and observability platform for K3s clusters.

The project is currently maintained as a personal and experimental MVP focused on:

- DevSecOps architecture.
- Runtime-security visibility.
- Wazuh integration.
- AI-assisted security analysis.
- Kubernetes network segmentation.
- Security monitoring and operational visibility.

K-Guard is continuously evolving and should be reviewed, tested, and hardened before production use.

## Supported Versions

Security fixes are currently provided for the latest stable release line.

| Version | Supported |
| ------- | --------- |
| 1.7.x   | :white_check_mark: |
| 1.6.x   | :x:        |
| < 1.6    | :x:        |

The `main` branch may contain changes that are still under development and should not automatically be considered production-ready.

## Reporting a Vulnerability

Please do not report security vulnerabilities through public GitHub issues, pull requests, discussions, screenshots, or public chat channels.

### Preferred Reporting Method

Use GitHub's private vulnerability-reporting mechanism for the repository whenever it is available.

Provide:

- A clear description of the vulnerability.
- The affected component or feature.
- The affected version or commit.
- Detailed reproduction steps.
- The expected and observed behavior.
- The potential security impact.
- Any proof of concept that can be shared safely.
- Suggested remediation, if available.

### Alternative Contact

If private vulnerability reporting is not available, contact the maintainer privately through the GitHub account:

- GitHub: [@KamouloxPelvis](https://github.com/KamouloxPelvis)

Do not include credentials, private keys, tokens, decoded Kubernetes Secrets, or sensitive production data in the report.

## Reporting Expectations

The maintainer will make reasonable efforts to:

- Acknowledge a valid report within 48 hours.
- Assess the severity and affected scope.
- Keep the reporter informed about the remediation status.
- Prepare a fix or mitigation when appropriate.
- Coordinate disclosure after a fix is available.

Response times may vary depending on the severity, reproducibility, affected components, and available maintenance capacity.

## Security Scope

The following areas are considered in scope:

- Authentication and authorization issues.
- Session and JWT handling.
- Credential exposure.
- Wazuh integration security.
- K-Guard AI data handling.
- Runtime-security event processing.
- Kubernetes API access.
- Network Sentinel policy operations.
- Namespace or workload isolation bypasses.
- Server-side request vulnerabilities.
- Path traversal and arbitrary file access.
- Injection vulnerabilities.
- Sensitive data exposure.
- Vulnerabilities in the K-Guard installer.
- Vulnerabilities introduced by K-Guard deployment manifests.

## Out of Scope

The following items are generally outside the scope of this policy:

- Vulnerabilities in third-party software without a K-Guard-specific impact.
- Issues requiring already-compromised administrator access.
- Denial-of-service tests against public or production infrastructure.
- Social engineering, phishing, or physical attacks.
- Reports based only on outdated dependencies without an exploitable impact.
- Self-XSS or issues requiring the victim to execute attacker-controlled code manually.
- Vulnerabilities in unsupported or modified deployments.
- Findings that only concern development tooling without affecting released artifacts.

Out-of-scope findings may still be reviewed when they reveal a meaningful risk to K-Guard users.

## Security Design Principles

K-Guard is designed around the following security principles:

- Backend-mediated access to protected integrations.
- Separation of frontend and infrastructure credentials.
- Read-only Wazuh visibility from the K-Guard interface.
- Explicit confirmation before Sentinel policy operations.
- Targeted NetworkPolicy group and namespace selection.
- Removal limited to Sentinel-managed policy resources.
- Progressive Zero-Trust network segmentation.
- Least-privilege access wherever practical.
- Avoidance of credentials and generated artifacts in source control.
- Strict handling of sensitive configuration data.

These principles describe the intended architecture. They do not constitute a guarantee that every deployment is secure.

## Credential and Data Handling

Do not commit or publicly disclose:

- Passwords.
- API tokens.
- JWT signing keys.
- Kubernetes credentials.
- Kubeconfig files.
- TLS private keys.
- Decoded Kubernetes Secrets.
- Cisco Webex tokens.
- Wazuh credentials.
- Production logs containing sensitive information.
- Personal or customer data.

If a credential is accidentally exposed:

1. Revoke or rotate it immediately.
2. Remove it from the affected environment.
3. Review access logs where available.
4. Report the exposure privately to the maintainer.
5. Do not rely only on deleting the value from the latest Git commit.

## Responsible Disclosure

Please allow reasonable time for investigation and remediation before publicly disclosing a vulnerability.

The maintainer may coordinate a disclosure timeline with the reporter depending on:

- Severity.
- Exploitability.
- Availability of a fix.
- Impact on deployed environments.
- Whether the vulnerability affects third-party components.

Security advisories may include affected versions, impact, mitigations, and upgrade guidance.

## Disclaimer

K-Guard is provided for educational, research, portfolio, and evaluation purposes.

The software is provided on an "as is" basis, without warranties of any kind, whether express or implied.

K-Guard is not a substitute for:

- A complete security operations process.
- A vulnerability-management program.
- An incident-response plan.
- A professional security assessment.
- A hardened production architecture.
- Qualified Kubernetes and infrastructure administration.

The maintainer cannot be held responsible for damage, data loss, service interruption, or security incidents resulting from the use, deployment, or modification of K-Guard.

Users remain responsible for:

- Reviewing the source code.
- Securing the underlying server and cluster.
- Protecting credentials.
- Testing changes before production use.
- Maintaining backups.
- Monitoring their deployment.
- Applying appropriate security controls.