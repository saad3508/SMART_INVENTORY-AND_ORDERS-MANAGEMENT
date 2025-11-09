from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import logging
import bcrypt  # Explicitly import bcrypt to ensure backend is loaded

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("auth")

# --- JWT Configuration ---
SECRET_KEY = "smartinventorysupersecretkey"  # Ideally from Azure Key Vault
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# --- Password Hashing Context ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- OAuth2 Token URL ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# --- Static User Database (Demo Purposes) ---
raw_users = {
    "admin": {"password": "admin123", "role": "admin"},
    "warehouse": {"password": "warehouse123", "role": "warehouse"},
}

# --- Safe Password Hashing (Azure Compatible) ---
def safe_hash_password(password: str):
    try:
        # bcrypt supports passwords up to 72 bytes
        password = password[:72]
        return pwd_context.hash(password)
    except Exception as e:
        logger.warning(f"⚠️ Password hashing failed: {e}")
        return pwd_context.hash(password[:50])  # fallback shorter length


# --- Build Fake Users Database ---
fake_users_db = {
    username: {
        "username": username,
        "hashed_password": safe_hash_password(user["password"]),
        "role": user["role"],
    }
    for username, user in raw_users.items()
}

# --- Verify Password ---
def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        plain_password = plain_password[:72]  # Ensure bcrypt-safe
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Error verifying password: {e}")
        return False

# --- Authenticate User ---
def authenticate_user(username: str, password: str):
    user = fake_users_db.get(username)
    if not user:
        logger.warning(f"❌ Authentication failed: {username} not found")
        return None
    if not verify_password(password, user["hashed_password"]):
        logger.warning(f"❌ Invalid password for user: {username}")
        return None
    logger.info(f"✅ User {username} authenticated successfully")
    return user

# --- Create Access Token ---
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    try:
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except Exception as e:
        logger.error(f"JWT encoding failed: {e}")
        raise HTTPException(status_code=500, detail="Internal token generation error")

# --- Verify Token ---
def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

# --- Role-Based Access Control (RBAC) ---
def require_role(*allowed_roles):
    def role_checker(payload=Depends(verify_token)):
        user_role = payload.get("role")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires one of {allowed_roles} roles.",
            )
        return payload
    return role_checker
