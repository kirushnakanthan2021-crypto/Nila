"""Run Nila with: python main.py"""
from nila.store import Store
from nila.engine import (
    answer_from_memory,
    evaluation_passed,
    suggest_improvements,
    propose_self_improvements,
)
from nila.learner import learn_from_text, learn_from_url, learn_from_multiple_sources
from nila.agent import run_agent, agent_create_goal
from nila.planner import format_plan
from nila.sandbox import run_python_snippet
from nila.patcher import (
    export_proposal_file,
    write_workspace_file,
    list_proposal_files,
)
from nila.backup import export_knowledge_json, import_knowledge_json
from nila.stats import collect_stats, format_stats
from nila import __version__
import json
from pathlib import Path


def ask(label: str) -> str:
    return input(label).strip()


def main() -> None:
    store = Store()
    print(f"\nNila v{__version__} — advanced personal AI foundation")
    print("Memory + learning + agent + planner + gated sandbox + backup.")
    print("NO autonomous code execution. Sandbox/patch require YOUR approval.")
    try:
        while True:
            print(
                """
--- MENU ---
1.  Save a memory
2.  Add a learning fact (manual)
3.  Search memory / knowledge
4.  Ask Nila (retrieval)
5.  Agent chat (context + gap suggestions)
6.  Learn from text (paste content)
7.  Learn from URL
8.  Learn from multiple sources
9.  View recent knowledge / by topic
10. Add evaluation question
11. Run evaluation tests
12. View evaluation report
13. Generate improvement suggestions
14. Propose self-improvements (human review)
15. View pending code proposals
16. Create goal + plan
17. List goals / plans
18. View conversation history
19. Clear conversation history
20. View recent learning sessions / logs
21. Sandbox run Python snippet (YOU paste + approve)
22. Export proposal to workspace/ file
23. Apply file into workspace/ only (type CONFIRM)
24. List workspace proposal files
25. Show Nila stats dashboard
26. Export knowledge backup (JSON)
27. Import knowledge backup (JSON)
0.  Exit
"""
            )
            choice = ask("Choose: ")

            if choice == "1":
                content, tags = ask("Memory: "), ask("Tags (optional): ")
                if content:
                    print("Saved memory ID:", store.add_memory(content, tags))

            elif choice == "2":
                title, content = ask("Fact title: "), ask("Fact / lesson: ")
                source = ask("Source (book, URL, or your note): ") or "user note"
                topic = ask("Topic (optional): ")
                verified = ask("Did you verify this source? (y/N): ").lower() == "y"
                if title and content:
                    print(
                        "Saved knowledge ID:",
                        store.add_knowledge(title, content, source, verified, topic),
                    )

            elif choice == "3":
                results = store.search(ask("Search words: "))
                if not results:
                    print("No matching records.")
                for item in results:
                    print(
                        f"\n#{item['id']} [{item['kind']}] {item['title']}\n"
                        f"{item['content']}\nSource: {item['source']}"
                        + (f"\nTopic: {item['topic']}" if item.get("topic") else "")
                    )

            elif choice == "4":
                q = ask("Ask Nila: ")
                print(answer_from_memory(store, q))

            elif choice == "5":
                q = ask("Agent chat: ")
                result = run_agent(store, q)
                print(result["answer"])
                if result["retrieved"]:
                    print("\nRetrieved:")
                    for r in result["retrieved"]:
                        print(f"  - {r['title']} (score {r['score']})")
                if result["suggestions"]:
                    print("\nSuggestions:")
                    for s in result["suggestions"]:
                        print(" -", s)

            elif choice == "6":
                topic = ask("Topic to learn: ")
                print("Paste the text (end with a single line containing only END):")
                lines = []
                while True:
                    line = input()
                    if line.strip() == "END":
                        break
                    lines.append(line)
                text = "\n".join(lines).strip()
                source = ask("Source label: ") or "pasted text"
                verified = ask("Mark facts as verified? (y/N): ").lower() == "y"
                if topic and text:
                    result = learn_from_text(store, topic, text, source, verified)
                    print(result["summary"])
                    for f in result["facts"]:
                        print("-", f[:120] + ("..." if len(f) > 120 else ""))

            elif choice == "7":
                topic = ask("Topic to learn: ")
                url = ask("URL: ")
                verified = ask("Mark facts as verified? (y/N): ").lower() == "y"
                if topic and url:
                    try:
                        result = learn_from_url(store, topic, url, verified)
                        print(result["summary"])
                        for f in result["facts"]:
                            print("-", f[:120] + ("..." if len(f) > 120 else ""))
                    except Exception as exc:
                        print("Learn failed:", exc)

            elif choice == "8":
                topic = ask("Topic to learn: ")
                print("Enter sources one per line (URL or long text). Empty line to finish.")
                sources = []
                while True:
                    s = input("> ").strip()
                    if not s:
                        break
                    sources.append(s)
                verified = ask("Mark facts as verified? (y/N): ").lower() == "y"
                if topic and sources:
                    result = learn_from_multiple_sources(
                        store, topic, sources, verified=verified
                    )
                    print(result["summary"])
                    if result["errors"]:
                        print("Some sources failed:")
                        for e in result["errors"]:
                            print(" -", e)
                    for f in result["facts"][:12]:
                        print("-", f[:120] + ("..." if len(f) > 120 else ""))

            elif choice == "9":
                mode = ask("All recent (a) or by topic (t)? ").lower()
                if mode.startswith("t"):
                    topic = ask("Topic: ")
                    items = store.knowledge_by_topic(topic)
                else:
                    items = store.recent_knowledge()
                if not items:
                    print("No knowledge yet.")
                for item in items:
                    print(
                        f"\n#{item['id']} {item['title']} (verified={bool(item['verified'])})"
                        f"\n{item['content']}\nSource: {item['source']}"
                        + (f"\nTopic: {item['topic']}" if item.get("topic") else "")
                    )

            elif choice == "10":
                question = ask("Test question: ")
                expected = ask("Expected keywords (use | between alternatives): ")
                if question and expected:
                    print("Saved test ID:", store.add_eval_case(question, expected))

            elif choice == "11":
                cases = store.eval_cases()
                if not cases:
                    print("No tests yet. Add evaluation questions first.")
                for case in cases:
                    answer = answer_from_memory(store, case["question"])
                    passed = evaluation_passed(answer, case["expected_keywords"])
                    store.record_eval(case["id"], answer, passed)
                    print(f"\nQuestion: {case['question']}")
                    print("Nila:", answer)
                    print("PASS" if passed else "NEEDS REVIEW")

            elif choice == "12":
                report = store.eval_summary()
                print(
                    f"Runs: {report['total']} | Passed: {report['passed']} | "
                    f"Accuracy: {report['accuracy']:.1%}"
                )
                for row in store.failed_runs():
                    print("\nFailed:", row["question"], "\nAnswer:", row["answer"])

            elif choice == "13":
                print("\nSuggestions for human review:")
                for idea in suggest_improvements(store):
                    print("-", idea)

            elif choice == "14":
                print("\nSelf-improvement proposals (pending, for YOUR review only):")
                for p in propose_self_improvements(store):
                    print(f"\n#{p['id']} {p['title']}")
                    print(p["description"])
                    if p.get("reason"):
                        print("Reason:", p["reason"])
                    if p.get("proposed_code"):
                        print("Code sketch:\n", p["proposed_code"])
                    if p.get("proposed_code"):
                        exp = ask("Export this code sketch to workspace/proposals? (y/N): ").lower()
                        if exp == "y":
                            info = export_proposal_file(
                                p["title"], p["description"], p.get("proposed_code") or ""
                            )
                            print("Wrote", info["path"])

            elif choice == "15":
                props = store.pending_proposals()
                if not props:
                    print("No pending proposals.")
                for p in props:
                    print(f"\n#{p['id']} {p['title']} [{p['status']}]")
                    print(p["description"])
                    if p["proposed_code"]:
                        print("Code sketch:\n", p["proposed_code"])
                    mark = ask(
                        "Mark as reviewed/applied/rejected? (r/a/j / Enter=skip): "
                    ).lower()
                    if mark == "r":
                        store.update_proposal_status(p["id"], "reviewed")
                    elif mark == "a":
                        store.update_proposal_status(p["id"], "applied")
                    elif mark == "j":
                        store.update_proposal_status(p["id"], "rejected")

            elif choice == "16":
                title = ask("Goal title: ")
                desc = ask("Description (optional): ")
                if title:
                    result = agent_create_goal(store, title, desc)
                    print(f"\nGoal #{result['id']} created")
                    print(format_plan(result["plan"]))

            elif choice == "17":
                goals = store.list_goals(status=None)
                if not goals:
                    print("No goals yet.")
                for g in goals:
                    print(f"\n#{g['id']} [{g['status']}] {g['title']}")
                    if g["description"]:
                        print(g["description"])
                    try:
                        plan = json.loads(g["plan_json"] or "[]")
                        print(format_plan(plan))
                    except json.JSONDecodeError:
                        pass
                    st = ask("Mark complete? (y/N): ").lower()
                    if st == "y":
                        store.update_goal(g["id"], status="done")

            elif choice == "18":
                msgs = store.recent_messages(limit=30)
                if not msgs:
                    print("No conversation yet.")
                for m in msgs:
                    print(f"[{m['role']}] {m['content'][:300]}")

            elif choice == "19":
                store.clear_conversation()
                print("Conversation cleared.")

            elif choice == "20":
                print("--- Learning sessions ---")
                for s in store.recent_learning_sessions():
                    print(
                        f"#{s['id']} topic={s['topic']} facts={s['facts_added']} | {s['summary']}"
                    )
                print("\n--- Recent logs ---")
                for log in store.recent_logs(limit=15):
                    print(f"{log['created_at']} [{log['kind']}] {log['detail'][:120]}")

            elif choice == "21":
                print(
                    "Sandbox: paste a SHORT pure-Python snippet.\n"
                    "Blocked: os/system/network/file/exec patterns.\n"
                    "End with a line containing only END"
                )
                lines = []
                while True:
                    line = input()
                    if line.strip() == "END":
                        break
                    lines.append(line)
                code = "\n".join(lines)
                print("--- Code to run ---")
                print(code)
                print("-------------------")
                ok = ask("Run this in sandbox? Type YES to run: ")
                if ok != "YES":
                    print("Cancelled.")
                else:
                    result = run_python_snippet(code, timeout_sec=3.0)
                    store.log_interaction(
                        "sandbox_run", result.get("stderr") or result.get("stdout") or ""
                    )
                    if result.get("blocked"):
                        print("BLOCKED:\n", result.get("stderr"))
                    else:
                        print("returncode:", result.get("returncode"))
                        if result.get("stdout"):
                            print("stdout:\n", result["stdout"])
                        if result.get("stderr"):
                            print("stderr:\n", result["stderr"])

            elif choice == "22":
                title = ask("Proposal title: ")
                desc = ask("Description: ")
                print("Paste code sketch (end with END):")
                lines = []
                while True:
                    line = input()
                    if line.strip() == "END":
                        break
                    lines.append(line)
                code = "\n".join(lines)
                if title:
                    info = export_proposal_file(title, desc, code)
                    print("Exported:", info["path"])
                    store.log_interaction("export_proposal", info["path"])

            elif choice == "23":
                print(
                    "Write a file UNDER workspace/ only.\n"
                    "Core nila/, tests/, main.py, api.py are protected and cannot be written."
                )
                rel = ask("Relative path (e.g. workspace/scratch.py): ")
                print("Paste file content (end with END):")
                lines = []
                while True:
                    line = input()
                    if line.strip() == "END":
                        break
                    lines.append(line)
                content = "\n".join(lines)
                print("--- Preview (first 500 chars) ---")
                print(content[:500])
                conf = ask("Type CONFIRM to write (anything else cancels): ")
                result = write_workspace_file(rel, content, confirm=conf)
                if result.get("ok"):
                    print("Wrote", result["path"])
                    store.log_interaction("workspace_write", result["path"])
                else:
                    print("Failed:", result.get("error"))

            elif choice == "24":
                files = list_proposal_files()
                if not files:
                    print("No proposal files in workspace/proposals yet.")
                for f in files:
                    print("-", f)

            elif choice == "25":
                print(format_stats(collect_stats(store)))

            elif choice == "26":
                default = str(Path("workspace") / "nila_knowledge_backup.json")
                path = ask(f"Export path [{default}]: ") or default
                info = export_knowledge_json(store, path)
                print(f"Exported {info['count']} knowledge items -> {info['path']}")

            elif choice == "27":
                path = ask("Import JSON path: ")
                if path:
                    try:
                        info = import_knowledge_json(store, path)
                        print(f"Added {info['added']}, skipped {info['skipped']}")
                    except Exception as exc:
                        print("Import failed:", exc)

            elif choice == "0":
                print("Nila session ended. Database is kept at its configured path.")
                break
            else:
                print("Choose a number from the menu.")
    finally:
        store.close()


if __name__ == "__main__":
    main()
