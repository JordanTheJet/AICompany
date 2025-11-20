"""Authentication utilities"""

import os
import json
from typing import Dict, Optional
from cryptography.fernet import Fernet
from pathlib import Path


class AuthManager:
    """Manages authentication credentials securely"""

    def __init__(self, credentials_dir: str = "./credentials"):
        """Initialize auth manager

        Args:
            credentials_dir: Directory to store encrypted credentials
        """
        self.credentials_dir = Path(credentials_dir)
        self.credentials_dir.mkdir(exist_ok=True, parents=True)
        self._cipher = self._init_cipher()

    def _init_cipher(self) -> Optional[Fernet]:
        """Initialize encryption cipher"""
        encryption_key = os.getenv("ENCRYPTION_KEY")
        if encryption_key:
            return Fernet(encryption_key.encode())
        return None

    def save_credentials(self, platform: str, credentials: Dict[str, str]) -> bool:
        """Save encrypted credentials for a platform

        Args:
            platform: Platform name (twitter, instagram, tiktok)
            credentials: Dictionary of credential key-value pairs

        Returns:
            True if successful, False otherwise
        """
        try:
            credentials_json = json.dumps(credentials)

            if self._cipher:
                encrypted_data = self._cipher.encrypt(credentials_json.encode())
                file_path = self.credentials_dir / f"{platform}.enc"
                with open(file_path, "wb") as f:
                    f.write(encrypted_data)
            else:
                # Fallback to unencrypted (not recommended for production)
                file_path = self.credentials_dir / f"{platform}.json"
                with open(file_path, "w") as f:
                    f.write(credentials_json)

            return True
        except Exception as e:
            print(f"Error saving credentials for {platform}: {e}")
            return False

    def load_credentials(self, platform: str) -> Optional[Dict[str, str]]:
        """Load credentials for a platform

        Args:
            platform: Platform name (twitter, instagram, tiktok)

        Returns:
            Dictionary of credentials or None if not found
        """
        try:
            enc_file = self.credentials_dir / f"{platform}.enc"
            json_file = self.credentials_dir / f"{platform}.json"

            if enc_file.exists() and self._cipher:
                with open(enc_file, "rb") as f:
                    encrypted_data = f.read()
                decrypted_data = self._cipher.decrypt(encrypted_data)
                return json.loads(decrypted_data.decode())
            elif json_file.exists():
                with open(json_file, "r") as f:
                    return json.load(f)

            return None
        except Exception as e:
            print(f"Error loading credentials for {platform}: {e}")
            return None

    def delete_credentials(self, platform: str) -> bool:
        """Delete credentials for a platform

        Args:
            platform: Platform name

        Returns:
            True if successful, False otherwise
        """
        try:
            enc_file = self.credentials_dir / f"{platform}.enc"
            json_file = self.credentials_dir / f"{platform}.json"

            if enc_file.exists():
                enc_file.unlink()
            if json_file.exists():
                json_file.unlink()

            return True
        except Exception as e:
            print(f"Error deleting credentials for {platform}: {e}")
            return False

    @staticmethod
    def generate_encryption_key() -> str:
        """Generate a new encryption key

        Returns:
            Base64-encoded encryption key
        """
        return Fernet.generate_key().decode()
