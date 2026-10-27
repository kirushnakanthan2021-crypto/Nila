import os
import unittest

from nila.embeddings import embed_text, cosine, semantic_score, backend_name
from nila.tamil_templates import looks_tamil, tpl_unknown
from nila.llm import llm_configured


class OptionalFeatureTests(unittest.TestCase):
    def test_hash_embed(self):
        os.environ["NILA_EMBEDDINGS"] = "hash"
        a = embed_text("Python programming language")
        b = embed_text("Python programming language")
        c = embed_text("completely unrelated gardening tips")
        self.assertIsNotNone(a)
        self.assertGreater(cosine(a, b), 0.99)
        self.assertGreater(semantic_score("Python language", "Python programming language"), 0.2)
        self.assertEqual(backend_name(), "hash")

    def test_tamil_detect(self):
        self.assertTrue(looks_tamil("என்ன பண்றது"))
        self.assertTrue(looks_tamil("enna pannu"))
        self.assertIn("தெரியல", tpl_unknown(True))

    def test_llm_not_configured_by_default(self):
        for k in ("NILA_LLM_BASE_URL", "NILA_LLM_API_KEY", "NILA_LLM_MODEL"):
            os.environ.pop(k, None)
        self.assertFalse(llm_configured())


if __name__ == "__main__":
    unittest.main()
