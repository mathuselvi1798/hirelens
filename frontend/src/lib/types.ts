/**
 * Types mirroring the backend's Pydantic schemas.
 *
 * These are hand-written for now. Once the API surface settles, the honest
 * move is to generate them from the backend's OpenAPI document so the two can
 * never drift - that is a Phase 9 task, noted in the roadmap.
 */

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}

export interface ContactInfo {
  email: string | null;
  phone: string | null;
  links: string[];
}

export interface DocumentSummary {
  id: string;
  filename: string;
  file_type: "pdf" | "docx" | "txt";
  created_at: string;
  word_count: number;
  page_count: number | null;
  section_names: string[];
  bullet_count: number;
  contact: ContactInfo;
  text_preview: string;
}

export interface ModuleInfo {
  id: string;
  version: string;
  title: string;
  description: string;
  requires_job_description: boolean;
  category: string;
}

export interface Capabilities {
  ai_enabled: boolean;
  ai_provider: string;
  module_count: number;
  max_upload_mb: number;
  allowed_extensions: string[];
}

export interface AnalysisResult<T = unknown> {
  id: string;
  module_id: string;
  module_version: string;
  prompt_version: string;
  document_id: string;
  created_at: string;
  duration_ms: number;
  cached: boolean;
  data: T;
}

/* --- resume_analysis module ---------------------------------------------- */

export type Severity = "high" | "medium" | "low";
export type Priority = "critical" | "high" | "medium" | "low";

export interface SectionAssessment {
  name: string;
  present: boolean;
  score: number;
  comment: string;
}

export interface Strength {
  title: string;
  detail: string;
}

export interface Weakness {
  title: string;
  detail: string;
  severity: Severity;
}

export interface Recommendation {
  priority: Priority;
  area: string;
  action: string;
  rationale: string;
  example: string | null;
}

export interface SkillGroup {
  category: string;
  skills: string[];
}

export interface ResumeAnalysis {
  overall_score: number;
  headline: string;
  summary: string;
  clarity_score: number;
  impact_score: number;
  structure_score: number;
  estimated_experience_level:
    | "student" | "entry" | "junior" | "mid"
    | "senior" | "lead" | "executive" | "unclear";
  sections: SectionAssessment[];
  skills: SkillGroup[];
  strengths: Strength[];
  weaknesses: Weakness[];
  recommendations: Recommendation[];
  confidence: "high" | "medium" | "low";
}

/* --- job_match module ----------------------------------------------------- */

export type Importance = "critical" | "important" | "nice_to_have";

export interface MatchedSkill {
  skill: string;
  evidence: string;
}

export interface MissingSkill {
  skill: string;
  importance: Importance;
  how_to_address: string;
}

export interface ExperienceAlignment {
  required: string;
  candidate: string;
  aligned: boolean;
  comment: string;
}

export interface KeywordCoverage {
  score: number;
  covered: string[];
  missing: string[];
}

export interface JobMatch {
  match_score: number;
  verdict: "strong_match" | "good_match" | "partial_match" | "weak_match";
  headline: string;
  summary: string;
  matching_skills: MatchedSkill[];
  missing_skills: MissingSkill[];
  experience_alignment: ExperienceAlignment;
  keyword_coverage: KeywordCoverage;
  recommendations: string[];
  should_apply: "yes" | "yes_with_changes" | "probably_not";
  confidence: "high" | "medium" | "low";
}

/* --- ats_analysis module -------------------------------------------------- */

export interface ScoredArea {
  score: number;
  comment: string;
}

export interface ATSIssue {
  severity: Severity;
  area: string;
  issue: string;
  fix: string;
}

export interface ATSAnalysis {
  ats_score: number;
  parse_risk: "low" | "medium" | "high";
  headline: string;
  summary: string;
  formatting: ScoredArea;
  sections: ScoredArea;
  keywords: ScoredArea;
  readability: ScoredArea;
  missing_sections: string[];
  suggested_keywords: string[];
  issues: ATSIssue[];
  confidence: "high" | "medium" | "low";
}

/* --- career_intelligence module ------------------------------------------- */

export interface RoleRecommendation {
  title: string;
  fit_score: number;
  why: string;
  gap_to_close: string;
}

export interface SkillGap {
  skill: string;
  priority: Priority;
  why_it_matters: string;
}

export interface LearningStep {
  step: number;
  focus: string;
  outcome: string;
  estimated_weeks: number;
}

export interface NextAction {
  action: string;
  timeframe: "this_week" | "this_month" | "this_quarter";
}

export interface CareerIntelligence {
  headline: string;
  current_positioning: string;
  readiness_score: number;
  recommended_roles: RoleRecommendation[];
  skill_gaps: SkillGap[];
  learning_roadmap: LearningStep[];
  next_actions: NextAction[];
  confidence: "high" | "medium" | "low";
}
