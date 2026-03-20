from app.schemas.analysis import AnalysisReportSchema


def build_summary(report: AnalysisReportSchema) -> str:
    competitors = ", ".join(item.name for item in report.competitors.direct_competitors[:3]) or "нет явных"
    channels = ", ".join(report.target_audience.acquisition_channels[:3]) or "нужно протестировать"
    offers = ", ".join(report.monetization_10k_plus.offer_examples[:2]) or "пакет услуг"
    roadmap_day1 = report.mvp_roadmap_2_weeks.days[0]
    return (
        "Ваш анализ готов.\n\n"
        f"1. Value Proposition\n{report.value_prop.one_liner}\n\n"
        f"2. Target Audience\nОсновной сегмент: {report.target_audience.primary_segment}\nКаналы: {channels}\n\n"
        f"3. Monetization $10k+\nМодель: {report.monetization_10k_plus.revenue_model}\nОфферы: {offers}\n\n"
        f"4. Competitors\nКого стоит изучить: {competitors}\n\n"
        f"5. 2-week MVP Roadmap\nДень 1: {roadmap_day1.goal}\nИтог 2 недель: {', '.join(report.mvp_roadmap_2_weeks.launch_criteria[:2])}"
    )

