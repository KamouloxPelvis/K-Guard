K-Guard
[🇫🇷 Version Française](#-version-française) | [🇺🇸 English Version](#-english-version)

(#version-française)

🛡️ K-Guard : Opérateur de Maintenance & Sécurité K3s

K-Guard est un dashboard SRE (Site Reliability Engineering) dédié à l'observabilité et à l'audit de sécurité automatisé pour clusters K3s. Conçu pour offrir une visibilité en temps réel sur l'état de santé des Pods et leur surface d'attaque, K-Guard intègre des fonctions de remédiation immédiates : redémarrage de services, délestage dynamique des réplicas en cas de saturation CPU/RAM, et signalement de mise à jour des images conteneurisées suite à la détection de vulnérabilités critiques.

![K-Guard Dashboard](screenshots/health_view.png)

🚀 Fonctionnalités Clés

Health Monitoring : Visualisation dynamique de la charge CPU/RAM avec seuils de criticité intelligents (Bleu/Orange/Rouge).

Security Audit : Intégration native de Trivy pour le scan de vulnérabilités (CVE) des images conteneurs.

![K-Guard Dashboard](screenshots/security_view.png)

Statut Dynamique : Interprétation automatique des niveaux de risque (SECURE, WATCH OUT, UPDATE REQUIRED).

Gestion Opérationnelle : Consultation des logs en temps réel et redémarrage des Pods via une interface sécurisée.

![K-Guard Dashboard](screenshots/log.png)

💡 Astuce scan mode Démo : En maintenant Shift lors d'un clic sur "Launch Scan", K-Guard force l'analyse d'une image volontairement obsolète (nginx:1.18). Cette fonction permet de tester instantanément la réactivité du moteur d'audit Trivy et de valider le comportement du dashboard face à des vulnérabilités critiques réelles.

![K-Guard Dashboard](screenshots/demo_view.png)

🛠️ Stack Technique

Frontend : Vue 3, TypeScript, Tailwind CSS (Design "Cyber" immersif).

Backend : FastAPI (Python), Kubernetes Python Client.

Sécurité : Trivy Engine.

Infrastructure : Cluster K3s sur VPS Ubuntu.

📦 Installation Rapide

git clone https://gitlab.com/portfolio-kamal-guidadou/k-guard.git

Configurez votre CI_CD_SSH_KEY pour le déploiement automatisé.

Lancez le backend : uvicorn main:app --reload

Lancez le frontend : npm run dev

---------------------------------

Article du projet sur mon blog : https://blog.devopsnotes.org/articles/k-guard-orchestration-sre-et-audit-de-scurit-sur-k3s

Kamal Guidadou 2026

🇺🇸 English Version

(#english-version)

🛡️ K-Guard is an SRE (Site Reliability Engineering) dashboard designed for observability and automated security auditing within K3s clusters. Built to provide real-time visibility into Pod health and attack surfaces, K-Guard features immediate remediation tools: service restarts, dynamic replica scaling to handle CPU/RAM saturation, and update alerts for container images when critical vulnerabilities are detected.

![K-Guard Dashboard](screenshots/health_view.png)

🚀 Key Features

Health Monitoring: Dynamic CPU/RAM tracking with intelligent severity thresholds (Blue/Orange/Red).

Security Audit: Native Trivy integration for automated container image vulnerability (CVE) scanning.

![K-Guard Dashboard](screenshots/security_view.png)

Dynamic Status: Automatic risk level interpretation (SECURE, WATCH OUT, UPDATE REQUIRED).

Ops Management: Real-time log streaming and Pod lifecycle management (Restart/Remediate) through a secure UI.

![K-Guard Dashboard](screenshots/log.png)

💡 Demo Mode Scan: By holding Shift while clicking "Launch Scan", K-Guard forces an audit of a deliberately outdated image (nginx:1.18). This feature allows you to instantly test the responsiveness of the Trivy engine and validate how the dashboard handles and reports real-world critical vulnerabilities.

![K-Guard Dashboard](screenshots/demo_view.png)

🛠️ Technical Stack

Frontend: Vue 3, TypeScript, Tailwind CSS (Immersive "Cyber" UI).

Backend: FastAPI (Python), Kubernetes Python Client.

Security: Trivy Engine.

Infrastructure: K3s Cluster on Ubuntu VPS.

📦 Quick Start

git clone https://gitlab.com/portfolio-kamal-guidadou/k-guard.git

Set up your CI_CD_SSH_KEY for automated CI/CD deployment.

Start Backend: uvicorn main:app --reload

Start Frontend: npm run dev

----------------------------

Blog post of the project : https://blog.devopsnotes.org/articles/k-guard-orchestration-sre-et-audit-de-scurit-sur-k3s

Kamal Guidadou 2026