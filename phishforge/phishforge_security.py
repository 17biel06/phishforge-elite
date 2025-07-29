from cryptography.fernet import Fernet
import os

KEY_FILE = "secret.key"

def get_key():
    """Generates or loads the encryption key."""
    try:
        if not os.path.exists(KEY_FILE):
            key = Fernet.generate_key()
            with open(KEY_FILE, "wb") as key_file:
                key_file.write(key)
        else:
            with open(KEY_FILE, "rb") as key_file:
                key = key_file.read()
        return key
    except Exception as e:
        print(f"[ERROR] Error al obtener la clave de cifrado: {e}")
        # Fallback to a dummy key or raise an exception
        return Fernet.generate_key() # Generate a new key if file operations fail

fernet = Fernet(get_key())

def encrypt(data):
    """Encrypts data."""
    try:
        return fernet.encrypt(data.encode())
    except Exception as e:
        print(f"[ERROR] Error al cifrar datos: {e}")
        return b'' # Return empty bytes on error

def decrypt(token):
    """Decrypts data."""
    try:
        return fernet.decrypt(token).decode()
    except Exception as e:
        print(f"[ERROR] Error al descifrar datos: {e}")
        return "" # Return empty string on error

