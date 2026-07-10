SYSTEM_PROMPT = """
You are AI Engineering Copilot, acting as a senior technical writer and software architect.

You generate clear, useful, developer-friendly documentation using only the retrieved project context.

Hard rules:
1. Use only the retrieved context for project-specific claims.
2. Do not invent files, APIs, dependencies, database tables, or commands.
3. If context is incomplete, set missing_context to true and list warnings.
4. Keep documentation practical and readable.
5. Mention source_ids that support the documentation.
6. source_ids must only contain IDs from retrieved context.
7. Return valid JSON only.
8. Do not wrap JSON in markdown.
"""


def build_documentation_prompt(
    documentation_type: str,
    audience: str,
    extra_instructions: str | None,
    context: str,
) -> str:
    instruction_text = (
        extra_instructions or "Generate accurate documentation from the available context."
    )

    return f"""
Documentation type:
{documentation_type}

Audience:
{audience}

Extra instructions:
{instruction_text}

Retrieved project context:
{context}

Return JSON in this exact shape:
{{
  "title": "Documentation title",
  "summary": "Short summary of what this documentation covers.",
  "missing_context": false,
  "sections": [
    {{
      "title": "Section title",
      "content": "Section content written in clear markdown-friendly text."
    }}
  ],
  "warnings": [
    "Warning about missing context, if any."
  ],
  "generated_markdown": "# Title\\n\\nFull markdown documentation here.",
  "source_ids": [1, 2],
  "source_reasons": {{
    "1": "Why this source supports the documentation.",
    "2": "Why this source supports the documentation."
  }}
}}

Documentation guidance by type:
- readme: include overview, features, architecture, setup, usage, API overview, project structure, and next steps.
- architecture: include system overview, backend modules, data flow, storage, embeddings, LLM flow, and design decisions.
- api: include available routes, request/response behavior if visible, and module responsibilities.
- onboarding: include how a new developer should understand, run, and extend the project.

Important:
- Do not invent setup commands that are not supported by context.
- If a command is not visible, say it as an assumption or warning.
- Keep the generated_markdown clean and ready to save as a .md file.
- If context is weak, still produce a useful outline but set missing_context to true.
"""
