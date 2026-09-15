"""Resume Analysis - the reference implementation of an analysis module.

Note how small this file is. All the hard parts (calling the model, enforcing
the schema, retrying, caching, error handling) live in shared infrastructure.
A module supplies identity, a schema, and a prompt. That is the template every
future module follows.
"""
from app.analysis.base import AnalysisContext, AnalysisModule
from app.analysis.modules.resume_analysis.prompt import SYSTEM, build_user_prompt
from app.analysis.modules.resume_analysis.schema import ResumeAnalysis
from app.analysis.registry import register


@register
class ResumeAnalysisModule(AnalysisModule):
    id = "resume_analysis"
    version = "1.0"
    title = "Resume Analysis"
    description = (
        "A full quality review of the resume: structure, clarity, impact, "
        "skills, strengths, weaknesses, and prioritized improvements."
    )
    category = "resume"

    requires_job_description = False
    output_model = ResumeAnalysis
    prompt_version = "1"

    def build_prompt(self, ctx: AnalysisContext) -> tuple[str, str]:
        return SYSTEM, build_user_prompt(ctx)
