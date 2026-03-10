"""
services/rag/prompt_builder.py

Prompt tuned for small models (3B) — direct, minimal formatting,
no escape hatches that cause the model to give up early.
"""

SYSTEM_PROMPT = """You are a financial document assistant. Answer questions using only the context below.

Instructions:
- Extract the answer directly from the context. Be concise.
- Always cite the source document, page, and section.
- If the answer is a number or figure, state it exactly as written.
- Only say "No relevant information found" if the context truly has nothing related to the question.

Response format:
Answer: [your answer here]
Citation: [document] | Page [N] | Section: [section name]"""


def build_prompt(query: str, chunks: list[dict]) -> list[dict]:
    context_parts = []

    for i, chunk in enumerate(chunks, 1):
        doc     = chunk.get("document_name", "Unknown")
        page    = chunk.get("page_number", "?")
        section = chunk.get("section_title", "Unknown")
        text    = chunk.get("text", "").strip()

        context_parts.append(
            f"[Source {i}] {doc} | Page {page} | {section}\n{text}"
        )

    context = "\n\n---\n\n".join(context_parts)

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Context:\n{context}\n\n"
                f"Question: {query}\n\n"
                f"Answer based only on the context above:"
            ),
        },
    ]