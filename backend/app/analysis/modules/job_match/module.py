from app.analysis.base import AnalysisContext, AnalysisModule
from app.analysis.modules.job_match.prompt import SYSTEM, build_user_prompt
from app.analysis.modules.job_match.schema import JobMatch
from app.analysis.registry import register


@register
class JobMatchModule(AnalysisModule):
    id = "job_match"
    version = "1.0"
    title = "Job Match"
    description = (
        "Scores this resume against a specific job posting: matching skills, "
        "missing skills, experience alignment, and keyword coverage."
    )
    category = "matching"

    requires_job_description = True
    output_model = JobMatch
    prompt_version = "1"

    def build_prompt(self, ctx: AnalysisContext) -> tuple[str, str]:
        return SYSTEM, build_user_prompt(ctx)
