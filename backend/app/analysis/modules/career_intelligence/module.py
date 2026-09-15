from app.analysis.base import AnalysisContext, AnalysisModule
from app.analysis.modules.career_intelligence.prompt import SYSTEM, build_user_prompt
from app.analysis.modules.career_intelligence.schema import CareerIntelligence
from app.analysis.registry import register


@register
class CareerIntelligenceModule(AnalysisModule):
    id = "career_intelligence"
    version = "1.0"
    title = "Career Intelligence"
    description = (
        "Realistic next roles, the gaps standing in the way, a sequenced learning "
        "roadmap, and what to do this week."
    )
    category = "career"

    requires_job_description = False
    output_model = CareerIntelligence
    prompt_version = "1"

    def build_prompt(self, ctx: AnalysisContext) -> tuple[str, str]:
        return SYSTEM, build_user_prompt(ctx)
