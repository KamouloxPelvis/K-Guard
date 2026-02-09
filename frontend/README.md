K-Guard
[🇫🇷 Version Française](#-version-française) | [🇺🇸 English Version](#-english-version)

(#version-française)

🛡️ K-Guard : Opérateur de Maintenance & Sécurité K3s

K-Guard est un tableau de bord SRE (Site Reliability Engineering) conçu pour l'observabilité et l'audit de sécurité automatisé d'un cluster K3s. Développé pour offrir une visibilité temps réel sur la santé des Pods et leur surface d'attaque.

🚀 Fonctionnalités Clés

Health Monitoring : Visualisation dynamique de la charge CPU/RAM avec seuils de criticité intelligents (Bleu/Orange/Rouge).

Security Audit : Intégration native de Trivy pour le scan de vulnérabilités (CVE) des images conteneurs.

Statut Dynamique : Interprétation automatique des niveaux de risque (SECURE, WATCH OUT, UPDATE REQUIRED).

Gestion Opérationnelle : Consultation des logs en temps réel et redémarrage des Pods via une interface sécurisée.

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

🇺🇸 English Version
(#english-version)

🛡️ K-Guard: K3s Automated Maintenance & Security Operator
K-Guard is a dedicated SRE dashboard built for observability and automated security auditing within K3s clusters. It provides real-time insights into Pod health and container security posture.

🚀 Key Features

Health Monitoring: Dynamic CPU/RAM tracking with intelligent severity thresholds (Blue/Orange/Red).

Security Audit: Native Trivy integration for automated container image vulnerability (CVE) scanning.

Dynamic Status: Automatic risk level interpretation (SECURE, WATCH OUT, UPDATE REQUIRED).

Ops Management: Real-time log streaming and Pod lifecycle management (Restart/Remediate) through a secure UI.

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

💡 Le petit plus de Kamal

Note de l'auteur : Ce projet a été conçu pour démontrer la fusion entre le NetDevOps et la Cyber-Gouvernance. Il permet non seulement de surveiller les performances, mais aussi d'automatiser la remédiation face aux vulnérabilités critiques.