import json

from sdc.crypto.encrypter import encrypt
from sdc.crypto.key_store import KeyStore, validate_required_keys


class Encrypter:
    def __init__(self, json_secret_keys):
        keys = json.loads(json_secret_keys)
        # Ensure the 2 supported purposes are in the keystore
        validate_required_keys(keys, "authentication")
        validate_required_keys(keys, "eq_v3_launch")
        self.key_store = KeyStore(keys)

    def encrypt(self, payload, purpose):
        """
        Encrypts the payload using the keystore values

        :param payload: the value to encrypt
        :param purpose: A description of the purpose of the key, must be present in the keystore
        :return: string of encrypted data
        """
        encrypted_data = encrypt(payload, key_store=self.key_store, key_purpose=purpose)
        return encrypted_data
