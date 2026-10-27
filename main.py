"""Run Nila with: python main.py"""
from nila.store import Store
from nila.engine import answer_from_memory, evaluation_passed, suggest_improvements


def ask(label: str) -> str:
    return input(label).strip()


def main() -> None:
    store = Store()
    print("\nNila v0.1 — private AI foundation")
    print("Memory + retrieval + evaluation. No API key required.")
    try:
        while True:
            print("""
--- MENU ---
1. Save a memory
2. Add a learning fact
3. Search memory / knowledge
4. Ask Nila
5. Add evaluation question
6. Run evaluation tests
7. View evaluation report
8. Generate improvement suggestions
9. View recent knowledge
0. Exit
""")
            choice = ask("Choose: ")
            if choice == "1":
                content, tags = ask("Memory: "), ask("Tags (optional): ")
                if content: print("Saved memory ID:", store.add_memory(content, tags))
            elif choice == "2":
                title, content = ask("Fact title: "), ask("Fact / lesson: ")
                source = ask("Source (book, URL, or your note): ") or "user note"
                verified = ask("Did you verify this source? (y/N): ").lower() == "y"
                if title and content: print("Saved knowledge ID:", store.add_knowledge(title, content, source, verified))
            elif choice == "3":
                results = store.search(ask("Search words: "))
                if not results: print("No matching records.")
                for item in results:
                    print(f"\n#{item['id']} [{item['kind']}] {item['title']}\n{item['content']}\nSource: {item['source']}")
            elif choice == "4":
                print(answer_from_memory(store, ask("Ask Nila: ")))
            elif choice == "5":
                question, expected = ask("Test question: "), ask("Expected keywords (use | between alternatives): ")
                if question and expected: print("Saved test ID:", store.add_eval_case(question, expected))
            elif choice == "6":
                cases = store.eval_cases()
                if not cases: print("No tests yet. Add evaluation questions first.")
                for case in cases:
                    print(f"\nTest #{case['id']}: {case['question']}")
                    answer = ask("Answer to evaluate: ")
                    passed = evaluation_passed(answer, case["expected_keywords"])
                    store.record_eval(case["id"], answer, passed)
                    print("PASS" if passed else "NEEDS REVIEW")
            elif choice == "7":
                report = store.eval_summary()
                print(f"Runs: {report['total']} | Passed: {report['passed']} | Accuracy: {report['accuracy']:.1%}")
                for row in store.failed_runs(): print("\nFailed:", row["question"], "\nAnswer:", row["answer"])
            elif choice == "8":
                print("\nSuggestions for human review:")
                for idea in suggest_improvements(store): print("-", idea)
            elif choice == "9":
                for item in store.recent_knowledge(): print(f"\n#{item['id']} {item['title']} (verified={bool(item['verified'])})\n{item['content']}\nSource: {item['source']}")
            elif choice == "0":
                print("Nila session ended. Database is kept at its configured path.")
                break
            else: print("Choose a number from 0 to 9.")
    finally:
        store.close()


if __name__ == "__main__":
    main()
