import os
import bcrypt
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import APIRouter, HTTPException, Depends, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordRequestForm
from dotenv import load_dotenv

load_dotenv()

# Configuration Sécurité
SECRET_KEY = os.getenv("SECRET_KEY", "une-cle-tres-secrete-par-defaut")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 600
ADMIN_PSEUDO = os.getenv("ADMIN_PSEUDO")
ADMIN_HASH = os.getenv("ADMIN_PASSWORD_HASH")

security_scheme = HTTPBearer()
router = APIRouter(tags=["Authentication"])

def verify_password(plain_password, hashed_password):
    if not hashed_password: return False
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )

async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security_scheme)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expiré")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Erreur signature")

@router.post("/api/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username != ADMIN_PSEUDO or not verify_password(form_data.password, ADMIN_HASH):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Accès refusé : Identifiants incorrects",
        )
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = jwt.encode({"sub": form_data.username, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": access_token, "token_type": "bearer"}