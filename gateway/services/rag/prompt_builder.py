"""
services/rag/prompt_builder.py
"""

SYSTEM_PROMPT = """You are an expert legal document assistant. Your sole task is to extract answers strictly from the provided context.

Follow these rules exactly:
1. Read the provided context. If the text contains the answer, extract it exactly as written.
2. If the text explicitly states a fact (e.g., "business days"), state that fact. Do not claim the text is unclear just because it lacks a dictionary definition.
3. For EVERY claim you make, you MUST cite the source document, page number, and section.
4. IF AND ONLY IF the context does not contain the answer, you must output this exact phrase and nothing else: "No relevant clause found."
5. Never add external knowledge or speculate.

Output Format:
Answer: [Your precise answer here based on the text]
Citation: [Document Name] | Page [Number] | Section [Number/Name]"""


def build_prompt(query: str, chunks: list[dict]) -> list[dict]:
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        context_parts.append(
            f"[{i}] {chunk.get('document_name', 'Unknown')} | "
            f"Page {chunk.get('page_number', '?')} | "
            f"Section: {chunk.get('section_title', 'Unknown')}\n"
            f"{chunk['text']}"
        )

    context = "\n\n---\n\n".join(context_parts)
     # Debug: show truncated context

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"},
    ]