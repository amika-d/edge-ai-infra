"""
services/rag/prompt_builder.py
"""

SYSTEM_PROMPT = """You are a document assistant. You help users find precise information from company reports, legal agreements, and financial filings.

Rules:
1. Answer using ONLY the context provided. Extract facts exactly as written.
2. For every claim cite the source — document name, page number, and section.
3. If the context does not contain the answer, respond with exactly: "No relevant clause found."
4. Never speculate or add information from outside the context.

Format your response as:
Answer: [precise answer extracted from the context]
Citation: [Document] | Page [N] | [Section]"""


def build_prompt(query: str, chunks: list[dict]) -> list[dict]:
    context_parts = []

    for i, chunk in enumerate(chunks, 1):
        source_line = (
            f"[{i}] {chunk.get('document_name', 'Unknown')} | "
            f"Page {chunk.get('page_number', '?')} | "
            f"Section: {chunk.get('section_title', 'Unknown')}"
        )

        full_text  = chunk.get("text", "")
        child_text = chunk.get("child_text", "")

        # Only show excerpt when child differs from parent (expansion happened)
        excerpt_line = (
            f"\n[Relevant excerpt: \"{child_text[:150].strip()}...\"]\n"
            if child_text and child_text != full_text
            else "\n"
        )

        context_parts.append(
            f"Source: {source_line}{excerpt_line}{full_text}"
        )

    context = "\n\n---\n\n".join(context_parts)

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": f"Context:\n{context}\n\nQuestion: {query}"},
    ]