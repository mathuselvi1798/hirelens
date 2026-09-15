"""Prompts for the Resume Analysis module.

Kept in their own file, versioned via the module's `prompt_version`. Prompts
are product logic and change often; burying them inside a route handler makes
them impossible to review or A/B later.
"""
from app.analysis.base import AnalysisContext

SYSTEM = """You are a senior technical recruiter and career coach with 15 years \
of experience reviewing resumes across engineering, data, product, and design roles.

Your standards:
- Be honest and specific. Vague praise is useless to the candidate.
- Judge only what is in the document. Never infer employers, dates, degrees, \
or metrics that are not present.
- When you suggest a rewrite, rewrite wording the candidate already wrote. \
Never fabricate achievements, numbers, or technologies.
- If the extracted text is sparse, garbled, or clearly incomplete, say so and \
set confidence to "low" rather than guessing.
- Scores are judgments, not measurements. Reserve 90+ for genuinely exceptional \
resumes and do not inflate.

You always answer by calling the provided tool with a complete, valid analysis."""


def build_user_prompt(ctx: AnalysisContext) -> str:
    doc = ctx.document

    detected = ", ".join(s.name for s in doc.sections) or "none detected"
    contact_bits = []
    if doc.contact.email:
        contact_bits.append("email present")
    if doc.contact.phone:
        contact_bits.append("phone present")
    if doc.contact.links:
        contact_bits.append(f"{len(doc.contact.links)} link(s) present")
    contact = ", ".join(contact_bits) or "no contact details detected"

    parts = [
        "Analyze the resume below.",
        "",
        "## Parser metadata (deterministic, computed before you saw this)",
        f"- File type: {doc.file_type}",
        f"- Word count: {doc.word_count}",
        f"- Pages: {doc.page_count if doc.page_count is not None else 'unknown'}",
        f"- Sections detected by the parser: {detected}",
        f"- Bullet points detected: {len(doc.bullets)}",
        f"- Contact info: {contact}",
        "",
        "Treat this metadata as reliable. If the parser detected no 'skills' "
        "section, that usually means the resume genuinely lacks a clear one, "
        "which is worth flagging.",
        "",
        "## Resume text",
        "```",
        doc.raw_text[:24_000],
        "```",
    ]

    if ctx.job_description and ctx.job_description.strip():
        parts += [
            "",
            "## Target role (context only)",
            "The candidate is targeting the role below. Use it to judge relevance, "
            "but this is a general resume review, not a match score.",
            "```",
            ctx.job_description.strip()[:8_000],
            "```",
        ]

    parts += [
        "",
        "Now call the tool with your complete analysis.",
    ]
    return "\n".join(parts)
