import pytest
from pydantic import ValidationError

from app.schemas.analysis import AnalysisReportSchema


def build_valid_report():
    return {
        "value_prop": {
            "one_liner": "AI-бот для быстрых отчетов",
            "problem": "Фаундеры тонут в хаосе гипотез",
            "solution": "Структурированный анализ за минуты",
            "unique_advantage": "Telegram-first опыт",
            "promotion_angle": "Проверяй идеи до кода"
        },
        "target_audience": {
            "primary_segment": "соло-фаундеры",
            "secondary_segments": ["студии", "маркетологи"],
            "core_pains": ["нет структуры"],
            "acquisition_channels": ["Telegram"],
            "first_100_users_hypothesis": "через founder-комьюнити"
        },
        "monetization_10k_plus": {
            "revenue_model": "пакеты запросов",
            "pricing_strategy": "low-friction",
            "offer_examples": ["15 запросов"],
            "path_to_first_10k_per_month": "через B2C и агентства",
            "key_metrics": ["CR"],
            "key_assumptions": ["люди платят за скорость"]
        },
        "competitors": {
            "direct_competitors": [{"name": "ChatGPT", "why_relevant": "делает анализ", "weakness": "нет структуры"}],
            "indirect_competitors": [{"name": "Консультанты", "why_relevant": "дают рекомендации", "weakness": "дорого"}],
            "positioning_statement": "быстрый Telegram-first советник",
            "moat_hypotheses": ["история отчетов"]
        },
        "mvp_roadmap_2_weeks": {
            "days": [{"day_number": day, "goal": f"Цель {day}", "tasks": ["Задача"], "deliverable": "Результат", "metric": "Метрика"} for day in range(1, 15)],
            "launch_criteria": ["первый платящий пользователь"],
            "biggest_risks": ["слабая retention"]
        }
    }


def test_ai_json_parser_validates_exact_5_block_schema():
    report = AnalysisReportSchema.model_validate(build_valid_report())
    assert set(report.model_dump().keys()) == {
        "value_prop",
        "target_audience",
        "monetization_10k_plus",
        "competitors",
        "mvp_roadmap_2_weeks",
    }


def test_ai_json_parser_rejects_extra_block():
    payload = build_valid_report()
    payload["extra"] = {}
    with pytest.raises(ValidationError):
        AnalysisReportSchema.model_validate(payload)

