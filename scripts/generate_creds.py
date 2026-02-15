import secrets
import string
import sys
import os
from passlib.context import CryptContext

# Configuration du hashage
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def run_wizard(domain=None, password=None):
    # 1. Génération de la SECRET_KEY (32 chars)
    alphabet = string.ascii_letters + string.digits
    secret_key = ''.join(secrets.choice(alphabet) for i in range(32))
    
    # 2. Gestion des entrées (Arguments ou Manuel)
    # Si lancé par deploy.sh, on prend les arguments. Sinon, on demande.
    final_domain = domain if domain else input("🌐 Entrez le domaine/IP : ")
    final_password = password if password else input("🔑 Entrez le mot de passe admin : ")
    
    if not final_password:
        print("❌ Erreur : Mot de passe vide.")
        sys.exit(1)

    password_hash = pwd_context.hash(final_password)

    # 3. Injection dans le .env
    env_path = "backend/.env"
    example_path = "backend/.env.example"
    
    # On prépare le contenu à injecter
    new_data = {
        "USER_DOMAIN=": f"USER_DOMAIN={final_domain}\n",
        "SECRET_KEY=": f"SECRET_KEY={secret_key}\n",
        "ADMIN_PASSWORD_HASH=": f"ADMIN_PASSWORD_HASH={password_hash}\n"
        "ALLOWED_ORIGINS="= f"ALLOWED_ORIGINS=http://{final_domain},https://{final_domain}\n"
    }

    if os.path.exists(example_path):
        with open(example_path, "r") as f:
            lines = f.readlines()
        
        with open(env_path, "w") as f:
            for line in lines:
                # Si la ligne correspond à une de nos clés, on injecte la valeur
                matched = False
                for key, value in new_data.items():
                    if line.startswith(key):
                        f.write(value)
                        matched = True
                        break
                if not matched:
                    f.write(line)
        print(f"✅ Configuration injectée avec succès dans {env_path}")
    else:
        # Fallback si l'exemple est absent
        with open(env_path, "w") as f:
            for value in new_data.values():
                f.write(value)
        print(f"⚠️ {example_path} absent. Création d'un .env minimal.")

if __name__ == "__main__":
    # Si des arguments sont passés par le shell (deploy.sh)
    if len(sys.argv) > 2:
        run_wizard(sys.argv[1], sys.argv[2])
    else:
        run_wizard()