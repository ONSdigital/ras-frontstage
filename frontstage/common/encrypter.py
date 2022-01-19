import json
import logging

from sdc.crypto.encrypter import encrypt
from sdc.crypto.key_store import KeyStore, validate_required_keys
from structlog import wrap_logger

logger = wrap_logger(logging.getLogger(__name__))

KEY_PURPOSE = "authentication"


class Encrypter:
    def __init__(self, json_secret_keys):
        keys = json.loads(json_secret_keys)
        validate_required_keys(keys, KEY_PURPOSE)
        self.key_store = KeyStore(keys)

    def encrypt(self, payload, service):
        """
        Encrypts the payload using the keystore values
        :param payload: the value to encrypt
        :param service: The target service, needed to know which key in the keystore to use.
        :return: string of encrypted data
        """
        logger.info("About to encrypt payload", encryption_for_service=service)
        encrypted_data = encrypt(
            payload, key_store=self.key_store, key_purpose=KEY_PURPOSE, encryption_for_service=service
        )
        return encrypted_data
