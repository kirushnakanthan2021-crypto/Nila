import tempfile
import unittest
from pathlib import Path
from nila.store import Store
from nila.engine import answer_from_memory, evaluation_passed, suggest_improvements


class NilaTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(str(Path(self.temp.name) / "test.sqlite3"))

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def test_retrieval(self):
        self.store.add_knowledge("Python", "Python is a programming language.", "test source", True)
        self.assertIn("programming language", answer_from_memory(self.store, "What is Python?"))

    def test_unknown_answer_is_honest(self):
        self.assertIn("don't know", answer_from_memory(self.store, "quantum gardening"))

    def test_evaluation_keywords(self):
        self.assertTrue(evaluation_passed("Python is a programming language", "programming language|python language"))
        self.assertFalse(evaluation_passed("not sure", "programming language|python language"))

    def test_improvement_ideas(self):
        self.assertTrue(suggest_improvements(self.store))


if __name__ == "__main__":
    unittest.main()
