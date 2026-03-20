import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Card } from "../components/Card";
import { apiFetch, API_URL } from "../lib/api";
import { useAuthStore } from "../features/auth/store";

export function HistoryPage() {
  const token = useAuthStore((s) => s.token);
  const { data = [] } = useQuery({
    queryKey: ["history", token],
    queryFn: () => apiFetch<any[]>("/api/reports", token ?? undefined),
    enabled: Boolean(token),
  });

  return (
    <div className="space-y-4">
      {data.map((item) => (
        <Card key={item.id}>
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="text-xs uppercase tracking-[0.2em] text-slate-400">{item.status}</div>
              <div className="mt-2 text-sm text-slate-300">{item.short_summary_text ?? "Отчет в обработке"}</div>
            </div>
            <div className="flex gap-2">
              <Link className="rounded-xl bg-sky-500 px-3 py-2 text-sm" to={`/reports/${item.id}`}>Открыть</Link>
              {item.pdf_path ? (
                <a className="rounded-xl border border-white/10 px-3 py-2 text-sm" href={`${API_URL}/api/reports/${item.id}/pdf?token=${token}`} target="_blank">
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
