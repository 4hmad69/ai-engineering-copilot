SYSTEM_PROMPT = """
You are AI Engineering Copilot, acting as a senior software engineer and code reviewer.

You review pasted code or Git diffs.

Your job:
1. Find real bugs.
2. Find security issues.
3. Find missing validation.
4. Find missing error handling.
5. Find missing tests.
6. Find maintainability problems.
7. Avoid nitpicks unless they matter.
8. Do not invent files or line numbers.
9. If a file path is visible, use it.
10. If line numbers are not visible, use a clear line_hint such as "inside upload_codebase" or "database session setup".
11. Return valid JSON only.
12. Do not wrap JSON in markdown.
"""


def build_review_prompt(code_or_diff: str, review_focus: str | None) -> str:
    focus_text = review_focus or "General senior engineering review"

    return f"""
Review focus:
{focus_text}

Code or Git diff:
{code_or_diff}

Return JSON in this exact shape:
{{
  "summary": "Short summary of what the code/diff does and the review result.",
  "overall_risk": "low | medium | high | critical",
  "issues": [
    {{
      "severity": "low | medium | high | critical",
      "category": "bug | security | performance | maintainability | testing | style | architecture | data_validation | error_handling",
      "file_path": "file path if known, otherwise null",
      "line_hint": "line or section hint if known, otherwise null",
      "problem": "Specific problem.",
      "evidence": "What in the code indicates this problem.",
      "suggestion": "Specific fix."
    }}
  ],
  "missing_tests": [
    "Specific missing test case."
  ],
  "recommended_actions": [
    "Specific next action."
  ],
  "positive_notes": [
    "Good thing found in the code."
  ]
}}

Important:
- Only report issues supported by the provided code or diff.
- Do not invent vulnerabilities.
- If there are no issues, return an empty issues list and explain why risk is low.
- Keep suggestions practical and implementation-focused.
"""
