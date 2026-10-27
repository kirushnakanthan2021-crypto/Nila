import tempfile
import unittest
from pathlib import Path

from nila.sandbox import run_python_snippet, safety_scan
from nila import patcher


class SandboxPatcherTests(unittest.TestCase):
    def test_safe_snippet_runs(self):
        result = run_python_snippet("print(2 + 2)\n")
        self.assertTrue(result["ok"])
        self.assertIn("4", result["stdout"])

    def test_blocks_os_system(self):
        hits = safety_scan("import os\nos.system('echo hi')\n")
        self.assertTrue(hits)
        result = run_python_snippet("import os\nos.system('echo hi')\n")
        self.assertTrue(result["blocked"])

    def test_workspace_write_requires_confirm(self):
        # use temp workspace by monkeypatching paths
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old_ws, old_prop, old_app = patcher.WORKSPACE, patcher.PROPOSALS_DIR, patcher.APPLIED_DIR
            try:
                patcher.WORKSPACE = root / "workspace"
                patcher.PROPOSALS_DIR = patcher.WORKSPACE / "proposals"
                patcher.APPLIED_DIR = patcher.WORKSPACE / "applied"
                bad = patcher.write_workspace_file("scratch.py", "x=1\n", confirm="no")
                self.assertFalse(bad["ok"])
                good = patcher.write_workspace_file("scratch.py", "x=1\n", confirm="CONFIRM")
                self.assertTrue(good["ok"])
                self.assertTrue(Path(good["path"]).exists())
            finally:
                patcher.WORKSPACE, patcher.PROPOSALS_DIR, patcher.APPLIED_DIR = old_ws, old_prop, old_app

    def test_protected_core_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old_ws, old_prop, old_app = patcher.WORKSPACE, patcher.PROPOSALS_DIR, patcher.APPLIED_DIR
            try:
                patcher.WORKSPACE = root / "workspace"
                patcher.PROPOSALS_DIR = patcher.WORKSPACE / "proposals"
                patcher.APPLIED_DIR = patcher.WORKSPACE / "applied"
                # even with CONFIRM, path under nila/ must fail via is_protected if user passes it
                self.assertTrue(patcher.is_protected("nila/engine.py"))
            finally:
                patcher.WORKSPACE, patcher.PROPOSALS_DIR, patcher.APPLIED_DIR = old_ws, old_prop, old_app


if __name__ == "__main__":
    unittest.main()
