import unittest

from frontstage.common.cryptographer import encrypt, decrypt

class CryptoTestClass(unittest.TestCase):

    def test_encrypt(self):
        test_str = "Hello"
        self.assertEqual(encrypt(test_str), 302)

if __name__ == '__main__':
    unittest.main()
