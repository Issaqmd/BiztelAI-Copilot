"""
tests/evaluate_questions.py
Runs the 5 official BiztelAI sample questions + 5 custom shop-floor questions
(including revision conflict and unanswerable refusal tests) against RAGEngine.
"""
import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from app.rag_engine import get_rag_engine

SAMPLE_QUESTIONS = [
    "What is the recommended coolant concentration for the TX-200 CNC turning centre?",
    "The machine is showing alarm AL-104. What does it mean and what should the operator do?",
    "Who is allowed to remove a lockout lock from a machine?",
    "What is the outer diameter tolerance for the BH-220 bearing housing?",
    "How often should spindle runout be checked, and who does it?",
]

CUSTOM_QUESTIONS = [
    "We received a lot of 300 pieces of bought-out components. How many random samples should the QC Inspector draw, and which form should be used to record the inspection?",
    "What should the QC Inspector do if an incoming lot arrives without a Material Test Certificate (MTC), and where are rejected lots stored?",
    "What is the bolt torque for re-mounting the chuck on the TX-200, and what safety procedure must be followed before replacing a hydraulic hose?",
    "Which dimensions of the BH-220 bearing housing are classified as Critical and must be inspected on the CMM?",
    "What is the safety torque specification for the hydraulic pump motor mounting bolts on the TX-200?",
]


def run_evaluation():
    engine = get_rag_engine()
    all_questions = [("SAMPLE", q) for q in SAMPLE_QUESTIONS] + [("CUSTOM", q) for q in CUSTOM_QUESTIONS]

    for idx, (category, q) in enumerate(all_questions, start=1):
        print("=" * 80)
        print(f"[{category} #{idx}] QUESTION: {q}")
        print("-" * 80)
        result = engine.answer_question(q)
        print(f"GROUNDED: {result['grounded']}")
        print(f"ANSWER:\n{result['answer']}\n")
        if result["sources"]:
            cited = ", ".join(
                f"{s['doc_id']} ({s['revision']}) Pg {s['page_number']}" for s in result["sources"]
            )
            print(f"SOURCES: {cited}")
        else:
            print("SOURCES: None (Refusal / Unanswerable)")
        print()


if __name__ == "__main__":
    run_evaluation()