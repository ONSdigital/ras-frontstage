from base64 import b64decode, b64encode
from hashlib import sha256

from Crypto import Random
from Crypto.Cipher import AES

from frontstage import app


class Cryptographer:
    """Manage the encryption and decryption of random byte strings"""

    def __init__(self):
        """
        Set up the encryption key, this will come from an .ini file or from
        an environment variable. Change the block size to suit the data supplied
        or performance required.

        :param key: The encryption key to use when encrypting the data
        """
        key = app.config["SECRET_KEY"]
        self._key = sha256(key.encode("utf-8")).digest()

    def encrypt(self, raw_text):
        """
        Encrypt the supplied text

        :param raw_text: The data to encrypt, must be a string of type byte
        :return: The encrypted text
        """
        raw_text = self.pad(raw_text)
        init_vector = Random.new().read(AES.block_size)
        ons_cipher = AES.new(self._key, AES.MODE_CBC, init_vector)
        return b64encode(init_vector + ons_cipher.encrypt(raw_text))

    def decrypt(self, encrypted_text):
        """
        Decrypt the supplied text

        :param encrypted_text: The data to decrypt, must be a string of type byte
        :return: The unencrypted text
        """
        encrypted_text = b64decode(encrypted_text)
        init_vector = encrypted_text[:16]
        ons_cipher = AES.new(self._key, AES.MODE_CBC, init_vector)
        return self.unpad(ons_cipher.decrypt(encrypted_text[16:]))

    def pad(self, data):
        """
        Pad the data out to the selected block size.

        :param data: The data were trying to encrypt
        :return: The data padded out to our given block size
        """
        vector = AES.block_size - len(data) % AES.block_size
        return data + ((bytes([vector])) * vector)

    def unpad(self, data):
        """
        Un-pad the selected data.

        :param data: Our padded data
        :return: The data 'un'padded
        """
        return data[0 : -data[-1]]
