import os
import sys

def verify_system_readiness():
    errors = []
    
    # 1. Check Kubeconfig
    kube_path = "/etc/rancher/k3s/k3s.yaml"
    if not os.path.exists(kube_path):
        errors.append(f"Fichier config K3s absent à {kube_path}")
    elif not os.access(kube_path, os.R_OK):
        errors.append(f"Permission de LECTURE refusée sur {kube_path} (Faire: sudo chmod 644 {kube_path})")

    # 2. Check Containerd Socket
    socket_path = "/run/k3s/containerd/containerd.sock"
    if not os.path.exists(socket_path):
        errors.append(f"Socket Containerd absent à {socket_path}")
    elif not os.access(socket_path, os.W_OK):
        errors.append(f"Permission d'ÉCRITURE refusée sur le socket {socket_path} (Faire: sudo chmod 666 {socket_path})")

    # 3. Check Variables d'environnement 
    env_path = os.path.join(os.path.dirname(__file__), '../backend/.env')
    if not os.path.exists(env_path):
        errors.append("Fichier .env manquant dans le dossier /backend")
    else:
        with open(env_path, 'r') as f:
            content = f.read()
            if "ADMIN_PSEUDO" not in content:
                errors.append("Variable ADMIN_PSEUDO manquante dans le .env")

    if errors:
        print("\n❌ K-Guard Pre-flight Check FAILED :")
        for err in errors:
            print(f"   - {err}")
        print("\n💡 Astuce : Exécutez setup.sh avec les droits sudo si nécessaire.\n")
        sys.exit(1)
    
    print("✅ System Readiness : OK")

if __name__ == "__main__":
    verify_system_readiness()