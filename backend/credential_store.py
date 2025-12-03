"""
Secure credential storage using SQLite with encryption
Credentials are stored locally on the client's PC and encrypted
"""
import sqlite3
import os
from pathlib import Path
from cryptography.fernet import Fernet
import base64
from hashlib import sha256

class CredentialStore:
    def __init__(self):
        # Store database in user's AppData folder (Windows)
        app_data = os.getenv('LOCALAPPDATA', os.path.expanduser('~'))
        self.db_dir = Path(app_data) / 'AntigravityTrader'
        self.db_dir.mkdir(exist_ok=True)
        
        self.db_path = self.db_dir / 'config.db'
        self.key_path = self.db_dir / '.key'
        
        # Initialize encryption key
        self.cipher = self._get_or_create_cipher()
        
        # Initialize database
        self._init_db()
    
    def _get_or_create_cipher(self):
        """Get existing encryption key or create new one"""
        if self.key_path.exists():
            with open(self.key_path, 'rb') as f:
                key = f.read()
        else:
            # Generate new encryption key
            key = Fernet.generate_key()
            with open(self.key_path, 'wb') as f:
                f.write(key)
            # Hide the key file on Windows
            if os.name == 'nt':
                import ctypes
                ctypes.windll.kernel32.SetFileAttributesW(str(self.key_path), 2)  # Hidden attribute
        
        return Fernet(key)
    
    def _init_db(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS credentials (
                id INTEGER PRIMARY KEY,
                service TEXT UNIQUE NOT NULL,
                encrypted_data TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_mstock_credentials(self, api_key: str, user_id: str, password: str):
        """Save mStock credentials encrypted"""
        credentials = f"{api_key}|||{user_id}|||{password}"
        encrypted = self.cipher.encrypt(credentials.encode())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO credentials (service, encrypted_data)
            VALUES (?, ?)
        ''', ('mstock', encrypted.decode()))
        
        conn.commit()
        conn.close()
        
        print(f"✓ Credentials saved securely to: {self.db_path}")
    
    def get_mstock_credentials(self):
        """Retrieve and decrypt mStock credentials"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT encrypted_data FROM credentials WHERE service = ?
        ''', ('mstock',))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return None
        
        try:
            decrypted = self.cipher.decrypt(result[0].encode())
            api_key, user_id, password = decrypted.decode().split('|||')
            return {
                'api_key': api_key,
                'user_id': user_id,
                'password': password
            }
        except Exception as e:
            print(f"Error decrypting credentials: {e}")
            return None
    
    def credentials_exist(self):
        """Check if credentials are already saved"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM credentials WHERE service = ?
        ''', ('mstock',))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count > 0
    
    def delete_credentials(self):
        """Delete saved credentials (for logout/reset)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM credentials WHERE service = ?
        ''', ('mstock',))
        
        conn.commit()
        conn.close()
        
        print("✓ Credentials deleted")

# Global instance
credential_store = CredentialStore()
