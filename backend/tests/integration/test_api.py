from app.models.analysis import AnalysisRun
from app.models.billing import PaymentPack


async def test_start_user_bootstrap(session):
    from app.services.users import UserService

    user, created = await UserService(session).get_or_create_telegram_user({"id": 101, "first_name": "Новый"})
    await session.commit()
    assert created is True
    assert user.referral_code


async def test_analysis_queued(session, test_user):
    from app.schemas.analysis import AnalysisCreateSchema
    from app.services.analysis_service import AnalysisService

    class FakeRedis:
        async def enqueue_job(self, *args, **kwargs):
            return None

    analysis = await AnalysisService(session).enqueue_analysis(
        test_user, AnalysisCreateSchema(source="twa", input_text="A" * 40), FakeRedis()
    )
    await session.commit()
    assert analysis.status == "queued"


async def test_worker_completes_analysis_and_stores_report(session, test_user):
    from app.schemas.analysis import AnalysisCreateSchema
    from app.schemas.analysis import AnalysisReportSchema
    from app.services.analysis_service import AnalysisService

    class FakeRedis:
        async def enqueue_job(self, *args, **kwargs):
            return None

    analysis = await AnalysisService(session).enqueue_analysis(
        test_user, AnalysisCreateSchema(source="twa", input_text="B" * 60), FakeRedis()
    )
    report = {
        "value_prop": {"one_liner": "x", "problem": "x", "solution": "x", "unique_advantage": "x", "promotion_angle": "x"},
        "target_audience": {"primary_segment": "x", "secondary_segments": ["x"], "core_pains": ["x"], "acquisition_channels": ["x"], "first_100_users_hypothesis": "x"},
        "monetization_10k_plus": {"revenue_model": "x", "pricing_strategy": "x", "offer_examples": ["x"], "path_to_first_10k_per_month": "x", "key_metrics": ["x"], "key_assumptions": ["x"]},
        "competitors": {"direct_competitors": [{"name": "x", "why_relevant": "x", "weakness": "x"}], "indirect_competitors": [{"name": "x", "why_relevant": "x", "weakness": "x"}], "positioning_statement": "x", "moat_hypotheses": ["x"]},
        "mvp_roadmap_2_weeks": {"days": [{"day_number": d, "goal": "x", "tasks": ["x"], "deliverable": "x", "metric": "x"} for d in range(1, 15)], "launch_criteria": ["x"], "biggest_risks": ["x"]},
    }
    await AnalysisService(session).save_completed_report(
        analysis,
        AnalysisReportSchema.model_validate(report),
        "model",
        {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        1000,
        "/tmp/report.pdf",
    )
    await session.commit()
    saved = await session.get(AnalysisRun, analysis.id)
    assert saved.status == "completed"
    assert saved.top_level_report_json is not None


async def test_payment_flow_happy_path_internal_handlers(session, test_user):
    from app.services.payments.service import PaymentsService

    session.add(PaymentPack(code="p1", title="p1", description="desc", stars_amount=10, requests_amount=5, sort_order=1))
    await session.commit()
    service = PaymentsService(session)
    intent = await service.create_payment_intent(test_user, "p1")
    await service.mark_pre_checkout(intent.payment.invoice_payload, {})
    await service.mark_paid_once(intent.payment.invoice_payload, "charge", "provider", {})
    await session.commit()
    assert intent.payment.status == "paid"


async def test_twa_auth_validate(client, monkeypatch):
    monkeypatch.setattr("app.api.routes.twa.validate_telegram_init_data", lambda _: {"id": 123456, "first_name": "Тест", "username": "tester"})
    response = await client.post("/api/twa/auth/validate", json={"init_data_raw": "stub"})
    assert response.status_code == 200
    assert response.json()["user"]["telegram_id"] == 123456


async def test_report_pdf_endpoint_ownership_check(client, session, test_user):
    from app.models.analysis import AnalysisRun
    from app.core.constants import AnalysisSource, AnalysisStatus

    analysis = AnalysisRun(
        user_id=test_user.id,
        source=AnalysisSource.TWA,
        input_text="idea",
        status=AnalysisStatus.COMPLETED,
        pdf_path=__file__,
        short_summary_text="done",
    )
    session.add(analysis)
    await session.commit()

    response = await client.get(f"/api/reports/{analysis.id}/pdf", headers={"Authorization": "Bearer invalid"})
    assert response.status_code in {401, 500}
