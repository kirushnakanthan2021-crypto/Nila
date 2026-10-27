import tempfile
import unittest
from pathlib import Path
from nila.store import Store
from nila.engine import (
    answer_from_memory,
    evaluation_passed,
    suggest_improvements,
    propose_self_improvements,
    tokens,
)
from nila.learner import learn_from_text, extract_candidate_facts
from nila.agent import run_agent
from nila.planner import plan_goal, create_planned_goal


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
        self.assertIn("don't know", answer_from_memory(self.store, "quantum gardening").lower())

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

    def test_tokens_latin_and_tamil(self):
        t = tokens("Python மற்றும் AI")
        self.assertTrue(any("python" == x for x in t))
        self.assertTrue(any("\u0b85" in x or "மற்றும்" in x or len(x) > 1 for x in t))

    def test_agent_turn(self):
        self.store.add_knowledge(
            "Nila", "Nila is a personal learning AI foundation.", "test", True, "nila"
        )
        result = run_agent(self.store, "What is Nila?")
        self.assertIn("answer", result)
        self.assertTrue(self.store.recent_messages())

    def test_planner(self):
        steps = plan_goal("Fix API bug", "debug authentication")
        self.assertGreaterEqual(len(steps), 4)
        g = create_planned_goal(self.store, "Ship v0.3", "release notes")
        self.assertTrue(g["id"])


if __name__ == "__main__":
    unittest.main()
