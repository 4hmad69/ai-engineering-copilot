from backend.app.services.rag_retrieval_service import RetrievedChunk


SYSTEM_PROMPT = """
You are AI Engineering Copilot, a senior software engineering assistant.

You answer questions about a software project using only the provided retrieved context.

Rules:
1. Use only the context provided.
2. Do not guess.
3. If the context is not enough, set missing_context to true.
4. Always reference the source IDs you used.
5. Keep the answer practical and developer-friendly.
6. Do not invent files, functions, APIs, dependencies, or line numbers.
7. Return valid JSON only.
8. Do not wrap JSON in markdown.
"""


def build_rag_context(chunks: list[RetrievedChunk], max_characters: int) -> str:
    context_blocks: list[str] = []
    used_characters = 0

    for chunk in chunks:
        block = (
            f"[S{chunk.source_id}]\n"
            f"File: {chunk.file_path}\n"
            f"File type: {chunk.file_type}\n"
            f"Lines: {chunk.start_line}-{chunk.end_line}\n"
            f"Similarity score: {chunk.similarity_score}\n"
            f"Content:\n{chunk.content}\n"
        )

        if used_characters + len(block) > max_characters:
            break

        context_blocks.append(block)
        used_characters += len(block)

    return "\n---\n".join(context_blocks)


def build_user_prompt(question: str, context: str) -> str:
    return f"""
Question:
{question}

Retrieved context:
{context}

Return JSON in this exact shape:
{{
  "answer": "Clear answer using only the retrieved context.",
  "confidence": "high | medium | low",
  "missing_context": true,
  "source_ids": [1, 2],
  "source_reasons": {{
    "1": "Why this source was useful",
    "2": "Why this source was useful"
  }},
  "follow_up_questions": []
}}
"""