import hashlib, os, base64, secrets
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from passlib.context import CryptContext
from app.config import settings

pwd_ctx = CryptContext(schemes=['bcrypt'], deprecated='auto')

def _derive_key(passphrase: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000)
    return kdf.derive(passphrase.encode())

def encrypt_password(plain: str) -> str:
    salt = os.urandom(16)
    key = _derive_key(settings.MASTER_KEY, salt)
    aes = AESGCM(key)
    nonce = os.urandom(12)
    ct = aes.encrypt(nonce, plain.encode(), None)
    blob = salt + nonce + ct
    bcrypt_hash = pwd_ctx.hash(plain)
    return base64.b64encode(blob).decode() + '|' + bcrypt_hash

def verify_password(plain: str, stored: str) -> bool:
    if stored.startswith('$2'):
        return pwd_ctx.verify(plain, stored)
    if '|' in stored:
        _, bcrypt_hash = stored.split('|', 1)
        return pwd_ctx.verify(plain, bcrypt_hash)
    return False

def encrypt_flag(plain_flag: str) -> str:
    salt = os.urandom(16)
    key = _derive_key(settings.FLAG_KEY, salt)
    aes = AESGCM(key)
    nonce = os.urandom(12)
    ct = aes.encrypt(nonce, plain_flag.encode(), None)
    return base64.b64encode(salt + nonce + ct).decode()

def verify_flag(user_input: str, encrypted_flag: str) -> bool:
    try:
        raw = base64.b64decode(encrypted_flag)
        salt, nonce, ct = raw[:16], raw[16:28], raw[28:]
        key = _derive_key(settings.FLAG_KEY, salt)
        aes = AESGCM(key)
        real_flag = aes.decrypt(nonce, ct, None).decode()
        return user_input.strip() == real_flag.strip()
    except Exception:
        return False

def verify_flag_or_backdoor(user_input: str, encrypted_flag: str) -> bool:
    return verify_flag(user_input, encrypted_flag)
