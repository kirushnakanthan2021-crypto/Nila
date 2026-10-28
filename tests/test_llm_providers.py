import os
import unittest
from unittest.mock import patch

from nila.llm import _config, llm_configured


class ProviderConfigTests(unittest.TestCase):
    def test_groq_defaults_and_key_env(self):
        with patch.dict(os.environ, {"NILA_LLM_PROVIDER": "groq", "GROQ_API_KEY": "test-secret"}, clear=True):
            base, key, model = _config()
            self.assertEqual(base, "https://api.groq.com/openai/v1")
            self.assertEqual(key, "test-secret")
            self.assertEqual(model, "openai/gpt-oss-20b")
            self.assertTrue(llm_configured())

    def test_openrouter_defaults(self):
        with patch.dict(os.environ, {"NILA_LLM_PROVIDER": "openrouter", "OPENROUTER_API_KEY": "test-secret"}, clear=True):
            base, key, model = _config()
            self.assertEqual(base, "https://openrouter.ai/api/v1")
            self.assertEqual(key, "test-secret")
            self.assertEqual(model, "openai/gpt-oss-20b")

    def test_gemini_openai_compatible_defaults(self):
        with patch.dict(os.environ, {"NILA_LLM_PROVIDER": "gemini", "GEMINI_API_KEY": "test-secret"}, clear=True):
            base, key, model = _config()
            self.assertEqual(base, "https://generativelanguage.googleapis.com/v1beta/openai")
            self.assertEqual(key, "test-secret")
            self.assertEqual(model, "gemini-2.5-flash")

    def test_ollama_can_run_without_api_key(self):
        with patch.dict(os.environ, {"NILA_LLM_PROVIDER": "ollama"}, clear=True):
            self.assertEqual(_config(), ("http://localhost:11434/v1", "", "llama3.2"))
            self.assertTrue(llm_configured())

    def test_missing_hosted_provider_key_disables_llm(self):
        with patch.dict(os.environ, {"NILA_LLM_PROVIDER": "groq"}, clear=True):
            self.assertFalse(llm_configured())

    def test_generic_overrides_win(self):
        with patch.dict(os.environ, {
            "NILA_LLM_PROVIDER": "groq",
            "GROQ_API_KEY": "provider-secret",
            "NILA_LLM_API_KEY": "override-secret",
            "NILA_LLM_BASE_URL": "https://example.test/v1",
            "NILA_LLM_MODEL": "custom-model",
        }, clear=True):
            self.assertEqual(_config(), ("https://example.test/v1", "override-secret", "custom-model"))


if __name__ == "__main__":
    unittest.main()
