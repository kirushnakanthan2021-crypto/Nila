import tempfile
import unittest
from pathlib import Path
from nila.store import Store
from nila.engine import answer_from_memory, evaluation_passed, suggest_improvements, propose_self_improvements
from nila.learner import learn_from_text, extract_candidate_facts


class NilaTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(str(Path(self.temp.name) / "test.sqlite3"))

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def test_retrieval(self):
        self.store.add_knowledge(
            "Python", "Python is a programming language.", "test source", True, topic="programming"
        )
        answer = answer_from_memory(self.store, "What is Python?")
        self.assertIn("programming language", answer)

    def test_unknown_answer_is_honest(self):
        self.assertIn("don't know", answer_from_memory(self.store, "quantum gardening"))

    def test_evaluation_keywords(self):
        self.assertTrue(
            evaluation_passed(
                "Python is a programming language", "programming language|python language"
            )
        )
        self.assertFalse(
            evaluation_passed("not sure", "programming language|python language")
        )

    def test_improvement_ideas(self):
        self.assertTrue(suggest_improvements(self.store))

    def test_learn_from_text(self):
        text = (
            "Retrieval-augmented generation is a technique. "
            "It combines a search system with a language model. "
            "The system first finds relevant documents then generates an answer."
        )
        result = learn_from_text(
            self.store,
            topic="retrieval",
            text=text,
            source="unit-test",
            verified=True,
        )
        self.assertGreaterEqual(result["facts_added"], 1)
        answer = answer_from_memory(self.store, "What is retrieval-augmented generation?")
        self.assertNotIn("don't know", answer.lower())

    def test_extract_facts_prefers_relevant(self):
        text = (
            "Cats sleep a lot. "
            "SQLite is a lightweight embedded database. "
            "Birds can fly. "
            "SQLite stores data in a single file and needs no server."
        )
        facts = extract_candidate_facts(text, "SQLite", max_facts=3)
        self.assertTrue(any("SQLite" in f or "sqlite" in f.lower() for f in facts))

    def test_propose_self_improvements(self):
        proposals = propose_self_improvements(self.store)
        self.assertTrue(proposals)
        self.assertTrue(self.store.pending_proposals())


if __name__ == "__main__":
    unittest.main()
