import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { Card } from "../components/Card";
import { useAuthStore } from "../features/auth/store";
import { API_URL, apiFetch } from "../lib/api";

export function HistoryPage() {
  const token = useAuthStore((state) => state.token);
  const { data = [], isLoading } = useQuery({
    queryKey: ["history", token],
    queryFn: () => apiFetch<any[]>("/api/reports", token ?? undefined),
    enabled: Boolean(token),
    refetchInterval: 15000,
  });

  if (isLoading) {
    return <Card>Загружаем историю отчетов...</Card>;
  }

  return (
    <div className="space-y-4">
      {data.map((item) => (
        <Card key={item.id}>
          <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
            <div className="min-w-0">
              <div className="text-xs uppercase tracking-[0.2em] text-slate-400">{item.status}</div>
              <div className="mt-2 text-sm text-slate-300">
                {item.short_summary_text ?? "Отчет обрабатывается. Как только он будет готов, здесь появится summary."}
              </div>
            </div>
            <div className="flex shrink-0 gap-2">
              <Link className="rounded-xl bg-sky-500 px-3 py-2 text-sm text-white" to={`/reports/${item.id}`}>
                Открыть
              </Link>
              {item.pdf_path ? (
                <a
                  className="rounded-xl border border-white/10 px-3 py-2 text-sm"
                  href={`${API_URL}/api/reports/${item.id}/pdf?token=${token}`}
                  rel="noreferrer"
                  target="_blank"
                >
                  PDF
                </a>
              ) : null}
            </div>
          </div>
        </Card>
      ))}
      {data.length === 0 ? <Card>История пока пустая.</Card> : null}
    </div>
  );
}
