import secrets

# Generate a 32-byte (256-bit) random key, encoded as a URL-safe string
secret_key = secrets.token_urlsafe(32)
print(secret_key)

from passlib.context import CryptContext

# Create a CryptContext instance (same as in your app)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Define your admin password
admin_password = ""  # Change this to your desired password

# Generate the hash
password_hash = pwd_context.hash(admin_password)
print(password_hash)