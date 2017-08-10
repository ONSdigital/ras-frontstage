from Crypto import Random
from Crypto.Cipher import AES
from base64 import b64encode, b64decode


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
