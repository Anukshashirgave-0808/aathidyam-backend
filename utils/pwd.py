from passlib.context import CryptContext

# Create context with bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """
    Generate a secure bcrypt hash of the password.
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against its bcrypt hash.
    Also supports fallback to plain-text for legacy users if needed.
    """
    try:
        # standard bcrypt check
        return pwd_context.verify(plain_password, hashed_password)
    except ValueError:
        # Fallback to plain text check for legacy un-hashed passwords
        # IMPORTANT: This should be removed after migration
        return plain_password == hashed_password
