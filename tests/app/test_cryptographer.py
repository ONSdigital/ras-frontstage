import unittest
from frontstage.common.cryptographer import Cryptographer

cryptographer = Cryptographer()


class CryptoTestClass(unittest.TestCase):
    def test_encrypt(self):
        test_str = b'Hello'
        encrypted_str = cryptographer.encrypt(test_str)
        decrypted_str = cryptographer.decrypt(encrypted_str)
        self.assertTrue(test_str == decrypted_str)


if __name__ == '__main__':
    unittest.main()
