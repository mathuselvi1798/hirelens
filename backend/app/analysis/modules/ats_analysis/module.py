from app.analysis.base import AnalysisContext, AnalysisModule
from app.analysis.modules.ats_analysis.prompt import SYSTEM, build_user_prompt
from app.analysis.modules.ats_analysis.schema import ATSAnalysis
from app.analysis.registry import register


@register
class ATSAnalysisModule(AnalysisModule):
    id = "ats_analysis"
    version = "1.0"
    title = "ATS Analysis"
    description = (
        "How reliably automated screening systems will read this resume: "
        "formatting, sections, keywords, readability, and specific risks."
    )
    category = "resume"

    requires_job_description = False
    output_model = ATSAnalysis
    prompt_version = "1"

    def build_prompt(self, ctx: AnalysisContext) -> tuple[str, str]:
        return SYSTEM, build_user_prompt(ctx)
