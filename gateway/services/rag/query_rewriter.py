"""
services/rag/query_rewriter.py

Expands user queries with domain-specific terminology before embedding.
Bridges the gap between casual language and financial/legal document language.

The problem:
  User asks:  "what is the annual revenue of uber 2024?"
  Document has: "consolidated statements of operations" / "total revenues"

  These embed far apart. The rewriter adds the financial terms so the
  embedding lands closer to the actual document chunk.
"""

# ---------------------------------------------------------------------------
# Financial term mappings
# ---------------------------------------------------------------------------

FINANCIAL_EXPANSIONS = {
    "revenue":      "revenue total revenues consolidated statements of operations",
    "profit":       "net income loss profit earnings consolidated statements",
    "loss":         "net income loss earnings consolidated statements of operations",
    "earnings":     "net income loss earnings per share EPS diluted",
    "sales":        "revenue total revenues net sales",
    "costs":        "costs expenses operating expenses cost of revenue",
    "expenses":     "operating expenses costs cost of revenue selling general administrative",
    "cash":         "cash equivalents liquidity cash flows operations",
    "debt":         "long-term debt borrowings credit facility notes payable",
    "assets":       "total assets consolidated balance sheet",
    "liabilities":  "total liabilities consolidated balance sheet",
    "employees":    "headcount full-time employees workforce",
    "growth":       "increase decrease year over year percentage change",
    "risk":         "risk factors uncertainties forward-looking statements",
    "segment":      "segment revenue operating income business segment results",
    "tax":          "income tax provision benefit effective tax rate",
    "shares":       "common stock shares outstanding diluted weighted average",
    "dividend":     "dividends distributions stockholders equity",
    "acquisition":  "business combinations acquisitions purchase price allocation",
    "guidance":     "outlook forward-looking statements expectations",
}

LEGAL_EXPANSIONS = {
    "terminate":    "termination clause notice period right to terminate",
    "termination":  "termination clause notice period written notice",
    "notice":       "notice period written notice days termination",
    "rent":         "monthly rent payment due date rental amount",
    "deposit":      "security deposit return conditions deductions",
    "repair":       "maintenance repair responsibility landlord tenant",
    "late":         "late fee penalty grace period overdue payment",
    "lease":        "lease agreement term commencement expiration",
    "liability":    "indemnification liability limitation damages",
    "breach":       "breach default cure period remedies",
}


# ---------------------------------------------------------------------------
# Rewriter
# ---------------------------------------------------------------------------

def rewrite_query(query: str) -> str:
    """
    Expand a user query with domain-specific terms.

    Examples:
        "what is the annual revenue of uber 2024?"
        → "what is the annual revenue of uber 2024?
           revenue total revenues consolidated statements of operations"

        "what is the termination notice period?"
        → "what is the termination notice period?
           termination clause notice period written notice
           notice period written notice days termination"
    """
    query_lower = query.lower()
    expansions  = []

    for term, expansion in {**FINANCIAL_EXPANSIONS, **LEGAL_EXPANSIONS}.items():
        if term in query_lower:
            expansions.append(expansion)

    if not expansions:
        return query

    expanded = query + "\n" + " ".join(expansions)
    return expanded


def rewrite_for_logging(query: str) -> tuple[str, list[str]]:
    """Returns (expanded_query, matched_terms) for debug logging."""
    query_lower = query.lower()
    matched     = []
    expansions  = []

    for term, expansion in {**FINANCIAL_EXPANSIONS, **LEGAL_EXPANSIONS}.items():
        if term in query_lower:
            matched.append(term)
            expansions.append(expansion)

    if not expansions:
        return query, []

    return query + "\n" + " ".join(expansions), matched


