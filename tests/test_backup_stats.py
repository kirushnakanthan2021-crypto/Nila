import tempfile
import unittest
from pathlib import Path

from nila.store import Store
from nila.backup import export_knowledge_json, import_knowledge_json
from nila.stats import collect_stats, format_stats


class BackupStatsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(str(Path(self.temp.name) / "t.sqlite3"))

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def test_export_import(self):
        self.store.add_knowledge("A", "Alpha fact", "t", True, "alpha")
        path = Path(self.temp.name) / "k.json"
        info = export_knowledge_json(self.store, path)
        self.assertEqual(info["count"], 1)
        store2 = Store(str(Path(self.temp.name) / "t2.sqlite3"))
        try:
            result = import_knowledge_json(store2, path)
            self.assertEqual(result["added"], 1)
            self.assertGreaterEqual(store2.knowledge_count(), 1)
        finally:
            store2.close()

    def test_stats(self):
        s = collect_stats(self.store)
        self.assertIn("version", s)
        self.assertTrue(format_stats(s))


if __name__ == "__main__":
    unittest.main()
