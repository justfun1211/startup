import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.constants import AnalysisSource, AnalysisStatus


class CompetitorItemSchema(BaseModel):
    name: str
    why_relevant: str
    weakness: str


class ValuePropSchema(BaseModel):
    one_liner: str
    problem: str
    solution: str
    unique_advantage: str
    promotion_angle: str


class TargetAudienceSchema(BaseModel):
    primary_segment: str
    secondary_segments: list[str]
    core_pains: list[str]
    acquisition_channels: list[str]
    first_100_users_hypothesis: str


class MonetizationSchema(BaseModel):
    revenue_model: str
    pricing_strategy: str
    offer_examples: list[str]
    path_to_first_10k_per_month: str
    key_metrics: list[str]
    key_assumptions: list[str]


class CompetitorsSchema(BaseModel):
    direct_competitors: list[CompetitorItemSchema]
    indirect_competitors: list[CompetitorItemSchema]
    positioning_statement: str
    moat_hypotheses: list[str]


class RoadmapDaySchema(BaseModel):
    day_number: int = Field(ge=1, le=14)
    goal: str
    tasks: list[str]
    deliverable: str
    metric: str


class RoadmapSchema(BaseModel):
    days: list[RoadmapDaySchema]
    launch_criteria: list[str]
    biggest_risks: list[str]

    @field_validator("days")
    @classmethod
    def validate_days(cls, value: list[RoadmapDaySchema]) -> list[RoadmapDaySchema]:
        if len(value) != 14:
            raise ValueError("days must contain exactly 14 items")
        expected = list(range(1, 15))
        if [item.day_number for item in value] != expected:
            raise ValueError("days must be ordered from 1 to 14")
        return value


class AnalysisReportSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value_prop: ValuePropSchema
    target_audience: TargetAudienceSchema
    monetization_10k_plus: MonetizationSchema
    competitors: CompetitorsSchema
    mvp_roadmap_2_weeks: RoadmapSchema


class AnalysisCreateSchema(BaseModel):
    source: AnalysisSource = AnalysisSource.TWA
    input_text: str = Field(min_length=10, max_length=4000)


class AnalysisListItemSchema(BaseModel):
    id: uuid.UUID
    status: AnalysisStatus
    short_summary_text: str | None
    pdf_path: str | None
    created_at: datetime
    completed_at: datetime | None


class AnalysisDetailSchema(BaseModel):
    id: uuid.UUID
    source: AnalysisSource
    input_text: str
    status: AnalysisStatus
    top_level_report_json: AnalysisReportSchema | None
    short_summary_text: str | None
    pdf_url: str | None
    model_name: str | None
    prompt_version: str | None
    tokens_input: int | None
    tokens_output: int | None
    total_tokens: int | None
    cost_rub: Decimal | None
    latency_ms: int | None
    created_at: datetime
    completed_at: datetime | None
