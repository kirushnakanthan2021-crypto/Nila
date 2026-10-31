import unittest
from unittest.mock import patch

from nila.learner import _validate_public_https_url


class UrlFetchSecurityTests(unittest.TestCase):
    def test_plain_http_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "HTTPS"):
            _validate_public_https_url("http://example.com")

    def test_private_destination_is_rejected(self):
        fake = [(None, None, None, None, ("10.0.0.8", 443))]
        with patch("nila.learner.socket.getaddrinfo", return_value=fake):
            with self.assertRaisesRegex(ValueError, "Private"):
                _validate_public_https_url("https://example.com")

    def test_public_destination_is_pinned(self):
        fake = [(None, None, None, None, ("93.184.216.34", 443))]
        with patch("nila.learner.socket.getaddrinfo", return_value=fake):
            host, ip, path = _validate_public_https_url("https://example.com/docs?q=1")
        self.assertEqual(host, "example.com")
        self.assertEqual(ip, "93.184.216.34")
        self.assertEqual(path, "/docs?q=1")

    def test_url_credentials_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "credentials"):
            _validate_public_https_url("https://user:pass@example.com")


if __name__ == "__main__":
    unittest.main()
