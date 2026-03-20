import { useQuery } from "@tanstack/react-query";
import { Card } from "../components/Card";
import { apiFetch } from "../lib/api";
import { useAuthStore } from "../features/auth/store";

export function AdminPage() {
  const token = useAuthStore((s) => s.token);
  const user = useAuthStore((s) => s.user);
  const { data } = useQuery({
    queryKey: ["admin-overview", token],
    queryFn: () => apiFetch<any>("/api/admin/overview", token ?? undefined),
    enabled: Boolean(token && user?.is_admin),
  });

  if (!user?.is_admin) {
    return <Card>Доступ к админке ограничен.</Card>;
  }

  if (!data) {
    return <Card>Загружаем админскую статистику...</Card>;
  }

  return (
    <div className="grid gap-4 md:grid-cols-3">
      <Card><div className="text-sm text-slate-400">DAU</div><div className="mt-2 text-3xl">{data.dau}</div></Card>
      <Card><div className="text-sm text-slate-400">MAU</div><div className="mt-2 text-3xl">{data.mau}</div></Card>
      <Card><div className="text-sm text-slate-400">Оплаты 7д</div><div className="mt-2 text-3xl">{data.payments_7d}</div></Card>
      <Card><div className="text-sm text-slate-400">XTR 30д</div><div className="mt-2 text-3xl">{data.stars_30d}</div></Card>
      <Card><div className="text-sm text-slate-400">Анализы 7д</div><div className="mt-2 text-3xl">{data.analyses_7d}</div></Card>
      <Card><div className="text-sm text-slate-400">Conversion</div><div className="mt-2 text-3xl">{data.conversion_to_payment}%</div></Card>
    </div>
  );
}

