from pathlib import Path
from time import perf_counter

import orjson
from openai import AsyncOpenAI
from pydantic import ValidationError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.schemas.analysis import AnalysisReportSchema


class AIClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = AsyncOpenAI(api_key=self.settings.polza_api_key, base_url=self.settings.polza_base_url)
        templates_dir = Path(__file__).resolve().parents[2] / "templates"
        self.system_prompt = (templates_dir / "system_prompt.txt").read_text(encoding="utf-8")
        self.user_template = (templates_dir / "user_prompt_template.txt").read_text(encoding="utf-8")

    @retry(
        reraise=True,
        stop=stop_after_attempt(get_settings().polza_max_retries),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(Exception),
    )
    async def analyze(self, idea: str) -> tuple[AnalysisReportSchema, dict, int, str]:
        return await self._run(idea, self.settings.polza_model)

    async def _run(self, idea: str, model: str) -> tuple[AnalysisReportSchema, dict, int, str]:
        start = perf_counter()
        prompt = self.user_template.replace("{{ idea }}", idea.strip())
        response = await self.client.chat.completions.create(
            model=model,
            temperature=0.5,
            response_format={"type": "json_object"},
            timeout=self.settings.polza_timeout_seconds,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt},
            ],
        )
        latency_ms = int((perf_counter() - start) * 1000)
        content = response.choices[0].message.content or "{}"
        try:
            parsed = AnalysisReportSchema.model_validate(orjson.loads(content))
            return parsed, response.usage.model_dump() if response.usage else {}, latency_ms, model
        except (ValidationError, orjson.JSONDecodeError):
            repaired = await self._repair_invalid_json(idea, content, model)
            return repaired, response.usage.model_dump() if response.usage else {}, latency_ms, model

    async def _repair_invalid_json(self, idea: str, invalid_content: str, model: str) -> AnalysisReportSchema:
        prompt = (
            "Исправь JSON, чтобы он строго соответствовал целевой схеме и содержал только 5 top-level блоков. "
            "Верни только JSON.\n\n"
            f"Исходная идея:\n{idea}\n\n"
            f"Текущий невалидный JSON:\n{invalid_content}"
        )
        response = await self.client.chat.completions.create(
            model=self.settings.polza_fallback_model or model,
            temperature=0.2,
            response_format={"type": "json_object"},
            timeout=self.settings.polza_timeout_seconds,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt},
            ],
        )
        return AnalysisReportSchema.model_validate(orjson.loads(response.choices[0].message.content or "{}"))

