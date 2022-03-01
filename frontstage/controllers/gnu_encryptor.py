import logging

import gnupg
from structlog import wrap_logger

logger = wrap_logger(logging.getLogger(__name__))


class GNUEncrypter:
    def __init__(self, public_key, passphrase=None, always_trust=True):
        self.gpg = gnupg.GPG()
        self.gpg.import_keys(public_key.encode("utf-8"))

    def encrypt(self, payload, recipient):
        """
        Encrypts the payload using the recipient values

        :param payload: the value to encrypt
        :param recipient: who is it for
        :return: string of encrypted data
        """
        enc_data = self.gpg.encrypt(payload, recipient, always_trust=True)
        if not enc_data.ok:
            logger.error(
                "Failed to encrypt with gpg", status=enc_data.status, error=enc_data.stderr, recipient=recipient
            )
            raise ValueError(
                "Failed to GNU encrypt bag: {}."
                "  Have you installed a valid public key and or recipient?".format(enc_data.status)
            )
        return str(enc_data)
