import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";

import { Card } from "../components/Card";
import { useAuthStore } from "../features/auth/store";
import { apiFetch } from "../lib/api";

export function ReportDetailPage() {
  const { id = "" } = useParams();
  const token = useAuthStore((state) => state.token);
  const { data, isLoading } = useQuery({
    queryKey: ["report", id, token],
    queryFn: () => apiFetch<any>(`/api/reports/${id}`, token ?? undefined),
    enabled: Boolean(token && id),
  });

  if (isLoading || !data) {
    return <Card>Загружаем отчет...</Card>;
  }

  if (!data.top_level_report_json) {
    return <Card>Отчет еще не готов. Вернитесь чуть позже или проверьте статус в истории.</Card>;
  }

  const report = data.top_level_report_json;

  return (
    <div className="space-y-4">
      <Card>
        <div className="text-sm text-slate-400">Исходная идея</div>
        <div className="mt-3 whitespace-pre-line text-slate-200">{data.input_text}</div>
      </Card>

      <Card>
        <h2 className="text-xl font-semibold">1. Value Proposition</h2>
        <div className="mt-2 text-slate-200">{report.value_prop.one_liner}</div>
        <div className="mt-3 text-sm text-slate-400">Проблема: {report.value_prop.problem}</div>
        <div className="mt-2 text-sm text-slate-400">Решение: {report.value_prop.solution}</div>
        <div className="mt-2 text-sm text-slate-400">Уникальное преимущество: {report.value_prop.unique_advantage}</div>
      </Card>

      <Card>
        <h2 className="text-xl font-semibold">2. Target Audience</h2>
        <div className="mt-2 text-slate-200">{report.target_audience.primary_segment}</div>
        <div className="mt-3 text-sm text-slate-400">
          Гипотеза первых 100 пользователей: {report.target_audience.first_100_users_hypothesis}
        </div>
        <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-slate-300">
          {report.target_audience.acquisition_channels.map((item: string) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </Card>

      <Card>
        <h2 className="text-xl font-semibold">3. Monetization $10k+</h2>
        <div className="mt-2 text-slate-200">{report.monetization_10k_plus.revenue_model}</div>
        <div className="mt-3 text-sm text-slate-400">Стратегия цен: {report.monetization_10k_plus.pricing_strategy}</div>
        <div className="mt-2 text-sm text-slate-400">
          Путь к первым 10k: {report.monetization_10k_plus.path_to_first_10k_per_month}
        </div>
      </Card>

      <Card>
        <h2 className="text-xl font-semibold">4. Competitors</h2>
        <div className="mt-2 text-sm text-slate-400">{report.competitors.positioning_statement}</div>
        <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-slate-300">
          {report.competitors.direct_competitors.map((item: any) => (
            <li key={item.name}>
              {item.name}: {item.why_relevant}. Слабое место: {item.weakness}
            </li>
          ))}
        </ul>
      </Card>

      <Card>
        <h2 className="text-xl font-semibold">5. 2-week MVP Roadmap</h2>
        <ul className="mt-3 space-y-2 text-sm text-slate-300">
          {report.mvp_roadmap_2_weeks.days.map((day: any) => (
            <li key={day.day_number}>
              День {day.day_number}: {day.goal}
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}
