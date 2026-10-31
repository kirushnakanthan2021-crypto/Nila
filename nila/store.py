"""SQLite storage. Keep the database outside the public repository."""
from __future__ import annotations
import os
import sqlite3

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:
    psycopg = None
    dict_row = None
from pathlib import Path
from typing import Any


def default_db_path() -> str:
    return os.environ.get("NILA_DB_PATH") or str(Path(".local") / "nila.sqlite3")



class _PostgresConnection:
    """Compatibility layer for the Store's SQLite-style SQL."""
    def __init__(self, dsn: str):
        self._conn = psycopg.connect(dsn, row_factory=dict_row)

    def execute(self, sql: str, params=()):
        return self._conn.execute(sql.replace('?', '%s'), params)

    def executescript(self, script: str):
        script = script.replace('INTEGER PRIMARY KEY AUTOINCREMENT', 'BIGSERIAL PRIMARY KEY')
        for statement in script.split(';'):
            statement = statement.strip()
            if statement and not statement.upper().startswith('PRAGMA '):
                self._conn.execute(statement)

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()

class Store:
    def __init__(self, path: str | None = None):
        self.database_url = os.environ.get('NILA_DATABASE_URL', '').strip()
        if self.database_url:
            if psycopg is None:
                raise RuntimeError('NILA_DATABASE_URL is set but psycopg is not installed; install requirements.txt.')
            self.path = 'postgresql'
            self.conn = _PostgresConnection(self.database_url)
        else:
            self.path = path or default_db_path()
            Path(self.path).expanduser().parent.mkdir(parents=True, exist_ok=True)
            self.conn = sqlite3.connect(self.path)
            self.conn.row_factory = sqlite3.Row
        self.conn.executescript(
            """
        PRAGMA foreign_keys = ON;

        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            tags TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS knowledge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            source TEXT NOT NULL DEFAULT 'user note',
            verified INTEGER NOT NULL DEFAULT 0,
            topic TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS eval_cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            expected_keywords TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS eval_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER NOT NULL,
            answer TEXT NOT NULL,
            passed INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(case_id) REFERENCES eval_cases(id)
        );

        CREATE TABLE IF NOT EXISTS improvement_ideas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            idea TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS learning_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            summary TEXT NOT NULL DEFAULT '',
            sources_used TEXT NOT NULL DEFAULT '',
            facts_added INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS proposed_changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            proposed_code TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'pending',
            reason TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            meta TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'open',
            plan_json TEXT NOT NULL DEFAULT '[]',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS interaction_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kind TEXT NOT NULL,
            detail TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
        )
        try:
            self.conn.execute("SELECT topic FROM knowledge LIMIT 1")
        except sqlite3.OperationalError:
            self.conn.execute(
                "ALTER TABLE knowledge ADD COLUMN topic TEXT NOT NULL DEFAULT ''"
            )
        self.conn.commit()

    def add_memory(self, content: str, tags: str = "") -> int:
        cur = self.conn.execute(
            "INSERT INTO memories(content,tags) VALUES(?,?) RETURNING id",
            (content.strip(), tags.strip()),
        )
        self.conn.commit()
        return int(cur.fetchone()['id'])

    def add_knowledge(
        self,
        title: str,
        content: str,
        source: str = "user note",
        verified: bool = False,
        topic: str = "",
    ) -> int:
        cur = self.conn.execute(
            "INSERT INTO knowledge(title,content,source,verified,topic) VALUES(?,?,?,?,?) RETURNING id",
            (
                title.strip(),
                content.strip(),
                source.strip() or "user note",
                int(verified),
                topic.strip(),
            ),
        )
        self.conn.commit()
        return int(cur.fetchone()['id'])

    def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        q = query.strip()
        if not q:
            memories = self.conn.execute(
                "SELECT id,'memory' AS kind,content AS title,content,tags AS source,'' AS topic,created_at "
                "FROM memories ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
            knowledge = self.conn.execute(
                "SELECT id,'knowledge' AS kind,title,content,source,topic,created_at "
                "FROM knowledge ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        else:
            term = f"%{q}%"
            memories = self.conn.execute(
                "SELECT id,'memory' AS kind,content AS title,content,tags AS source,'' AS topic,created_at "
                "FROM memories WHERE content LIKE ? OR tags LIKE ? ORDER BY id DESC LIMIT ?",
                (term, term, limit),
            ).fetchall()
            knowledge = self.conn.execute(
                "SELECT id,'knowledge' AS kind,title,content,source,topic,created_at "
                "FROM knowledge WHERE title LIKE ? OR content LIKE ? OR source LIKE ? OR topic LIKE ? "
                "ORDER BY id DESC LIMIT ?",
                (term, term, term, term, limit),
            ).fetchall()
        return [dict(r) for r in list(memories) + list(knowledge)]

    def all_items(self, limit: int = 2000) -> list[dict[str, Any]]:
        memories = self.conn.execute(
            "SELECT id,'memory' AS kind,content AS title,content,tags AS source,'' AS topic,created_at "
            "FROM memories ORDER BY id DESC LIMIT ?",
            (limit // 2,),
        ).fetchall()
        knowledge = self.conn.execute(
            "SELECT id,'knowledge' AS kind,title,content,source,topic,created_at "
            "FROM knowledge ORDER BY id DESC LIMIT ?",
            (limit // 2,),
        ).fetchall()
        return [dict(r) for r in list(memories) + list(knowledge)]

    def recent_knowledge(self, limit: int = 10) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT id,title,content,source,verified,topic,created_at "
            "FROM knowledge ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    def knowledge_by_topic(self, topic: str, limit: int = 20) -> list[dict[str, Any]]:
        term = f"%{topic.strip()}%"
        rows = self.conn.execute(
            "SELECT id,title,content,source,verified,topic,created_at FROM knowledge "
            "WHERE topic LIKE ? OR title LIKE ? OR content LIKE ? ORDER BY id DESC LIMIT ?",
            (term, term, term, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def knowledge_count(self) -> int:
        row = self.conn.execute("SELECT COUNT(*) AS c FROM knowledge").fetchone()
        return int(row["c"])

    def add_eval_case(self, question: str, expected_keywords: str) -> int:
        cur = self.conn.execute(
            "INSERT INTO eval_cases(question,expected_keywords) VALUES(?,?) RETURNING id",
            (question.strip(), expected_keywords.strip().lower()),
        )
        self.conn.commit()
        return int(cur.fetchone()['id'])

    def eval_cases(self) -> list[dict[str, Any]]:
        return [
            dict(r)
            for r in self.conn.execute("SELECT * FROM eval_cases ORDER BY id").fetchall()
        ]

    def record_eval(self, case_id: int, answer: str, passed: bool) -> None:
        self.conn.execute(
            "INSERT INTO eval_runs(case_id,answer,passed) VALUES(?,?,?)",
            (case_id, answer, int(passed)),
        )
        self.conn.commit()

    def eval_summary(self) -> dict[str, int | float]:
        row = self.conn.execute(
            "SELECT COUNT(*) AS total, COALESCE(SUM(passed),0) AS passed FROM eval_runs"
        ).fetchone()
        total, passed = int(row["total"]), int(row["passed"])
        return {
            "total": total,
            "passed": passed,
            "accuracy": passed / total if total else 0.0,
        }

    def failed_runs(self, limit: int = 10) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT c.question, r.answer, r.created_at FROM eval_runs r "
            "JOIN eval_cases c ON c.id = r.case_id WHERE r.passed = 0 "
            "ORDER BY r.id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    def add_idea(self, idea: str) -> int:
        cur = self.conn.execute(
            "INSERT INTO improvement_ideas(idea) VALUES(?) RETURNING id", (idea.strip(),)
        )
        self.conn.commit()
        return int(cur.fetchone()['id'])

    def add_learning_session(
        self, topic: str, summary: str, sources_used: str, facts_added: int
    ) -> int:
        cur = self.conn.execute(
            "INSERT INTO learning_sessions(topic,summary,sources_used,facts_added) VALUES(?,?,?,?) RETURNING id",
            (topic.strip(), summary.strip(), sources_used.strip(), facts_added),
        )
        self.conn.commit()
        return int(cur.fetchone()['id'])

    def recent_learning_sessions(self, limit: int = 10) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM learning_sessions ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    def add_proposed_change(
        self, title: str, description: str, proposed_code: str = "", reason: str = ""
    ) -> int:
        cur = self.conn.execute(
            "INSERT INTO proposed_changes(title,description,proposed_code,reason) VALUES(?,?,?,?) RETURNING id",
            (title.strip(), description.strip(), proposed_code.strip(), reason.strip()),
        )
        self.conn.commit()
        return int(cur.fetchone()['id'])

    def pending_proposals(self, limit: int = 20) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM proposed_changes WHERE status = 'pending' ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    def update_proposal_status(self, proposal_id: int, status: str) -> None:
        self.conn.execute(
            "UPDATE proposed_changes SET status = ? WHERE id = ?",
            (status.strip(), proposal_id),
        )
        self.conn.commit()

    # --- conversation memory ---
    def add_message(self, role: str, content: str, meta: str = "") -> int:
        cur = self.conn.execute(
            "INSERT INTO conversations(role,content,meta) VALUES(?,?,?) RETURNING id",
            (role.strip(), content.strip(), meta.strip()),
        )
        self.conn.commit()
        return int(cur.fetchone()['id'])

    def recent_messages(self, limit: int = 20) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM conversations ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return list(reversed([dict(r) for r in rows]))

    def clear_conversation(self) -> None:
        self.conn.execute("DELETE FROM conversations")
        self.conn.commit()

    # --- goals / planner ---
    def add_goal(self, title: str, description: str = "", plan_json: str = "[]") -> int:
        cur = self.conn.execute(
            "INSERT INTO goals(title,description,plan_json) VALUES(?,?,?) RETURNING id",
            (title.strip(), description.strip(), plan_json),
        )
        self.conn.commit()
        return int(cur.fetchone()['id'])

    def list_goals(self, status: str | None = "open", limit: int = 20) -> list[dict[str, Any]]:
        if status:
            rows = self.conn.execute(
                "SELECT * FROM goals WHERE status = ? ORDER BY id DESC LIMIT ?",
                (status, limit),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM goals ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    def update_goal(self, goal_id: int, status: str | None = None, plan_json: str | None = None) -> None:
        if status is not None:
            self.conn.execute(
                "UPDATE goals SET status = ? WHERE id = ?", (status, goal_id)
            )
        if plan_json is not None:
            self.conn.execute(
                "UPDATE goals SET plan_json = ? WHERE id = ?", (plan_json, goal_id)
            )
        self.conn.commit()

    def log_interaction(self, kind: str, detail: str = "") -> int:
        cur = self.conn.execute(
            "INSERT INTO interaction_logs(kind,detail) VALUES(?,?) RETURNING id",
            (kind.strip(), detail.strip()[:4000]),
        )
        self.conn.commit()
        return int(cur.fetchone()['id'])

    def recent_logs(self, limit: int = 30) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM interaction_logs ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    def close(self) -> None:
        self.conn.close()
