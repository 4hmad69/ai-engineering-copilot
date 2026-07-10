from typing import Protocol


class PromptChunk(Protocol):
    source_id: int
    file_path: str
    file_type: str
    start_line: int
    end_line: int
    similarity_score: float
    content: str


SYSTEM_PROMPT = """
You are AI Engineering Copilot, a senior software engineering assistant.

You answer questions about a software project using only the retrieved context.

Hard rules:
1. Use only the retrieved context.
2. Do not guess.
3. Do not invent files, functions, APIs, dependencies, line numbers, or implementation details.
4. If the retrieved context does not answer the question, set missing_context to true.
5. If missing_context is true, explain what context is missing.
6. Every factual claim about the code must be supported by one or more source_ids.
7. source_ids must be numeric IDs from the retrieved context, for example [1, 2].
8. Do not use source IDs that are not present in the retrieved context.
9. Return valid JSON only.
10. Do not wrap JSON in markdown.
11. Do not include extra commentary outside JSON.
"""


def build_rag_context(chunks: list[PromptChunk], max_characters: int) -> str:
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
  "answer": "Answer the question using only the retrieved context. If context is missing, say what is missing.",
  "confidence": "high | medium | low",
  "missing_context": false,
  "source_ids": [1],
  "source_reasons": {{
    "1": "Explain exactly why this source supports the answer."
  }},
  "follow_up_questions": []
}}

Important:
- source_ids must only contain IDs from the retrieved context.
- If the context does not contain the answer, use:
  "missing_context": true
  "confidence": "low"
  "source_ids": []
"""
