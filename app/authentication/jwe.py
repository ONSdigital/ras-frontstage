"""
Module to generate encrypt and decrypt token
"""
import os
from cryptography.hazmat.backends.openssl.backend import backend
from cryptography.hazmat.primitives.ciphers import Cipher
from cryptography.hazmat.primitives.ciphers import algorithms
from cryptography.hazmat.primitives.ciphers import modes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from app import settings
import base64
from werkzeug.exceptions import BadRequest
from flask import json

IV_EXPECTED_LENGTH = 12
CEK_EXPECT_LENGTH = 32


class Encrypter:

    def __init__(self, _private_key=settings.SM_USER_AUTHENTICATION_PRIVATE_KEY,
                 _private_key_password=settings.SM_USER_AUTHENTICATION_PRIVATE_KEY_PASSWORD,
                 _public_key=settings.SM_USER_AUTHENTICATION_PUBLIC_KEY):
        """ initialise encrypter with correct keys, the ability to change default keys for tests"""

        self._load_keys(_private_key, _private_key_password, _public_key)

        # first generate a random key
        self.cek = os.urandom(32)  # 256 bit random CEK

        # now generate a random IV
        self.iv = os.urandom(12)  # 96 bit random IV

    def _load_keys(self, private_key, private_key_password, public_key):
        """used to load keys"""
        private_key_bytes = private_key.encode()  # to bytes
        private_key_password_bytes = private_key_password.encode()
        public_key_bytes = public_key.encode()

        self.private_key = backend.load_pem_private_key(private_key_bytes, private_key_password_bytes)

        self.public_key = backend.load_pem_public_key(public_key_bytes)

    def encrypt_token(self, token):
        """Function to encrypt jwt"""

        jwe_protected_header = self._base_64_encode(b'{"alg":"RSA-OAEP","enc":"A256GCM"}')

        encrypted_key = self._base_64_encode(self.public_key.encrypt(self.cek, padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA1()), algorithm=hashes.SHA1(), label=None)))

        cipher = Cipher(algorithms.AES(self.cek), modes.GCM(self.iv), backend=backend)
        encryptor = cipher.encryptor()

        encryptor.authenticate_additional_data(jwe_protected_header)

        ciphertext = encryptor.update(token.encode()) + encryptor.finalize()
        tag = encryptor.tag

        encoded_ciphertext = self._base_64_encode(ciphertext)
        encoded_tag = self._base_64_encode(tag)

        # assemble result
        jwe = jwe_protected_header + b"." + encrypted_key + b"." + self._base_64_encode(self.iv) + \
            b"." + encoded_ciphertext + b"." + encoded_tag

        return jwe

    @staticmethod
    def _base_64_encode(text):
        # strip the trailing = as they are padding to make the result a multiple of 4
        # the RFC does the same, as do other base64 libraries so this is a safe operation
        return base64.urlsafe_b64encode(text).decode().strip("=").encode()


class Decrypter:

    def __init__(self):
        private_key = settings.SM_USER_AUTHENTICATION_PRIVATE_KEY
        private_key_password = settings.SM_USER_AUTHENTICATION_PRIVATE_KEY_PASSWORD
        public_key = settings.SM_USER_AUTHENTICATION_PUBLIC_KEY

        self._load_keys(private_key, private_key_password, public_key)

    def _load_keys(self, private_key, private_key_password, public_key):
        """ used to load keys"""
        private_key_bytes = private_key.encode()  # to bytes
        private_key_password_bytes = private_key_password.encode()
        public_key_bytes = public_key.encode()

        self.private_key = backend.load_pem_private_key(private_key_bytes, private_key_password_bytes)

        self.public_key = backend.load_pem_public_key(public_key_bytes)

    def decrypt_token(self, encrypted_token):
        """
        Function to decrypt encrypted jwt
        """
        if not isinstance(encrypted_token, str):
            encrypted_token = encrypted_token.decode()

        tokens = encrypted_token.split('.')
        if len(tokens) != 5:
            raise BadRequest(description="Token incorrect size")
        jwe_protected_header = tokens[0]
        self._check_jwe_protected_header(jwe_protected_header)
        encrypted_key = tokens[1]
        encoded_iv = tokens[2]
        encoded_cipher_text = tokens[3]
        encoded_tag = tokens[4]

        decrypted_key = self.private_key.decrypt(self._base64_decode(encrypted_key),
                                                 padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA1()),
                                                              algorithm=hashes.SHA1(), label=None))

        iv = self._base64_decode(encoded_iv)
        tag = self._base64_decode(encoded_tag)
        cipher_text = self._base64_decode(encoded_cipher_text)

        if not len(iv) == IV_EXPECTED_LENGTH:
            raise BadRequest(description="Token IV incorrect length")
        if not len(decrypted_key) == CEK_EXPECT_LENGTH:
            raise BadRequest(description="Token CEK incorrect length")

        decrypted_signed_token = self._decrypt_cipher_text(cipher_text, iv, decrypted_key, tag, jwe_protected_header)

        return decrypted_signed_token

    def _check_jwe_protected_header(self, header):
        """ used to validate jwe protected headers"""
        header = self._base64_decode(header).decode()
        header_data = json.loads(header)
        if not header_data.get("alg"):
            raise BadRequest(description="Token header missing Algorithm")
        if header_data.get("alg") != "RSA-OAEP":
            raise BadRequest(description="Token has invalid Algorithm")
        if not header_data.get("enc"):
            raise BadRequest(description="Token header missing Encoding")
        if header_data.get("enc") != "A256GCM":
            raise BadRequest(description="Token has invalid Encoding")

    @staticmethod
    def _decrypt_cipher_text(cipher_text, iv, key, tag, jwe_protected_header):
        """ used to decrypt cipher text """
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=backend)
        decryptor = cipher.decryptor()
        decryptor.authenticate_additional_data(jwe_protected_header.encode())
        decrypted_token = decryptor.update(cipher_text) + decryptor.finalize()
        return decrypted_token

    @staticmethod
    def _base64_decode(text):
        # if the text is not a multiple of 4 pad with trailing =
        # some base64 libraries don't pad data but Python is strict
        # and will throw a incorrect padding error if we don't do this
        if len(text) % 4 != 0:
            while len(text) % 4 != 0:
                text += "="
        return base64.urlsafe_b64decode(text)
