import json
import os
import unittest

from nila.llm import list_providers, llm_configured, _parse_providers


class CouncilConfigTests(unittest.TestCase):
    def tearDown(self):
        for k in (
            "NILA_LLM_PROVIDERS",
            "NILA_LLM_BASE_URL",
            "NILA_LLM_API_KEY",
            "NILA_LLM_MODEL",
        ):
            os.environ.pop(k, None)

    def test_multi_providers_json(self):
        os.environ["NILA_LLM_PROVIDERS"] = json.dumps(
            [
                {
                    "name": "a",
                    "base_url": "https://example.com/v1",
                    "api_key": "k1",
                    "model": "m1",
                },
                {
                    "name": "b",
                    "base_url": "https://example2.com/v1",
                    "api_key": "k2",
                    "model": "m2",
                },
            ]
        )
        self.assertTrue(llm_configured())
        pubs = list_providers()
        self.assertEqual(len(pubs), 2)
        self.assertEqual(pubs[0]["name"], "a")
        self.assertTrue(pubs[0]["has_key"])
        # secrets not exposed beyond has_key
        self.assertNotIn("api_key", pubs[0])

    def test_legacy_single(self):
        os.environ["NILA_LLM_BASE_URL"] = "https://api.example.com/v1"
        os.environ["NILA_LLM_API_KEY"] = "secret"
        os.environ["NILA_LLM_MODEL"] = "demo"
        ps = _parse_providers()
        self.assertEqual(len(ps), 1)
        self.assertEqual(ps[0]["name"], "default")


if __name__ == "__main__":
    unittest.main()
