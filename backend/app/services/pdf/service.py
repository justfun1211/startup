from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

from app.core.config import get_settings
from app.schemas.analysis import AnalysisReportSchema


class PdfService:
    def __init__(self) -> None:
        self.settings = get_settings()
        templates_dir = Path(__file__).resolve().parents[2] / "templates"
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=select_autoescape(enabled_extensions=("html",)),
        )

    async def generate_report_pdf(self, analysis_id: str, idea: str, report: AnalysisReportSchema) -> str:
        template = self.env.get_template("report.html")
        html = template.render(analysis_id=analysis_id, idea=idea, report=report.model_dump())
        output_path = Path(self.settings.pdf_storage_path) / f"{analysis_id}.pdf"
        HTML(string=html).write_pdf(output_path)
        return str(output_path)

