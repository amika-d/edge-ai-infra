"""
tests/test_query_rewriter.py

Run: python tests/test_query_rewriter.py
"""
from gateway.services.rag.query_rewriter import rewrite_for_logging


def test_rewriter(query: str):
    expanded, matched = rewrite_for_logging(query)
    print(f"\nQuery   : {query}")
    print(f"Matched : {matched}")
    print(f"Expanded: {expanded}")
    print("-" * 60)


if __name__ == "__main__":
    test_rewriter("what is the annual revenue of uber 2024?")
    test_rewriter("what is the termination notice period?")
    test_rewriter("how many monthly active platform consumers did uber have?")
    test_rewriter("what are the late payment penalties?")
    test_rewriter("hi how are you")   # no match — should return unchanged