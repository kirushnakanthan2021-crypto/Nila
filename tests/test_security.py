import unittest

from nila.security import validate_public_http_url


class UrlSecurityTests(unittest.TestCase):
    def test_reject_localhost(self):
        with self.assertRaises(ValueError):
            validate_public_http_url("http://localhost/admin")

    def test_reject_private_ip(self):
        with self.assertRaises(ValueError):
            validate_public_http_url("http://127.0.0.1/")

    def test_reject_non_http_scheme(self):
        with self.assertRaises(ValueError):
            validate_public_http_url("file:///etc/passwd")


if __name__ == "__main__":
    unittest.main()
