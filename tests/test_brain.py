import unittest

from nila.brain import is_duplicate_fact, lexical_score, normalize_text, summarize_messages


class BrainTests(unittest.TestCase):
    def test_tanglish_synonyms_normalize(self):
        self.assertEqual(normalize_text("Eppadi pannu?"), "how do")

    def test_duplicate_fact(self):
        self.assertTrue(is_duplicate_fact("Nila has persistent memory", ["Nila has persistent memory"]))
        self.assertFalse(is_duplicate_fact("Nila has persistent memory", ["The weather is sunny"]))

    def test_lexical_score(self):
        self.assertGreater(lexical_score("Nila memory", "Nila stores memory safely"), 0)
        self.assertEqual(lexical_score("unrelated", "Nila stores memory"), 0)

    def test_summary_deduplicates(self):
        result = summarize_messages([
            {"role": "user", "content": "I want a private AI system."},
            {"role": "user", "content": "I want a private AI system."},
        ])
        self.assertEqual(result.count("I want a private AI system."), 1)


if __name__ == "__main__":
    unittest.main()
