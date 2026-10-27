"""Run Nila with: python main.py"""
from nila.store import Store
from nila.engine import (
    answer_from_memory,
    evaluation_passed,
    suggest_improvements,
    propose_self_improvements,
)
from nila.learner import learn_from_text, learn_from_url, learn_from_multiple_sources
from nila import __version__


def ask(label: str) -> str:
    return input(label).strip()


def main() -> None:
    store = Store()
    print(f"\nNila v{__version__} — private self-learning foundation")
    print("Memory + retrieval + learning + evaluation. No API key required.")
    print("Self-generated code is NEVER executed automatically.")
    try:
        while True:
            print("""
--- MENU ---
1.  Save a memory
2.  Add a learning fact (manual)
3.  Search memory / knowledge
4.  Ask Nila
5.  Learn from text (paste content)
6.  Learn from URL
7.  Learn from multiple sources (URLs or text blocks)
8.  View recent knowledge / by topic
9.  Add evaluation question
10. Run evaluation tests
11. View evaluation report
12. Generate improvement suggestions
13. Propose self-improvements (code ideas for human review)
14. View pending code proposals
15. View recent learning sessions
0.  Exit
""")
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
                print(answer_from_memory(store, ask("Ask Nila: ")))

            elif choice == "5":
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

            elif choice == "6":
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

            elif choice == "7":
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

            elif choice == "8":
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

            elif choice == "9":
                question = ask("Test question: ")
                expected = ask("Expected keywords (use | between alternatives): ")
                if question and expected:
                    print("Saved test ID:", store.add_eval_case(question, expected))

            elif choice == "10":
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

            elif choice == "11":
                report = store.eval_summary()
                print(
                    f"Runs: {report['total']} | Passed: {report['passed']} | "
                    f"Accuracy: {report['accuracy']:.1%}"
                )
                for row in store.failed_runs():
                    print("\nFailed:", row["question"], "\nAnswer:", row["answer"])

            elif choice == "12":
                print("\nSuggestions for human review:")
                for idea in suggest_improvements(store):
                    print("-", idea)

            elif choice == "13":
                print("\nSelf-improvement proposals (status=pending, for YOUR review only):")
                for p in propose_self_improvements(store):
                    print(f"\n#{p['id']} {p['title']}")
                    print(p["description"])
                    if p.get("reason"):
                        print("Reason:", p["reason"])
                    if p.get("proposed_code"):
                        print("Code sketch:\n", p["proposed_code"])

            elif choice == "14":
                props = store.pending_proposals()
                if not props:
                    print("No pending proposals.")
                for p in props:
                    print(f"\n#{p['id']} {p['title']} [{p['status']}]")
                    print(p["description"])
                    if p["proposed_code"]:
                        print("Code sketch:\n", p["proposed_code"])
                    mark = ask("Mark as reviewed/applied/rejected? (r/a/j / Enter=skip): ").lower()
                    if mark == "r":
                        store.update_proposal_status(p["id"], "reviewed")
                    elif mark == "a":
                        store.update_proposal_status(p["id"], "applied")
                    elif mark == "j":
                        store.update_proposal_status(p["id"], "rejected")

            elif choice == "15":
                sessions = store.recent_learning_sessions()
                if not sessions:
                    print("No learning sessions yet.")
                for s in sessions:
                    print(
                        f"\n#{s['id']} topic={s['topic']} facts={s['facts_added']}"
                        f"\n{s['summary']}\nSources: {s['sources_used'][:200]}"
                    )

            elif choice == "0":
                print("Nila session ended. Database is kept at its configured path.")
                break
            else:
                print("Choose a number from the menu.")
    finally:
        store.close()


if __name__ == "__main__":
    main()
