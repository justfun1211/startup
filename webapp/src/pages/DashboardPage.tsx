import { useQuery } from "@tanstack/react-query";
import { Card } from "../components/Card";
import { apiFetch } from "../lib/api";
import { useAuthStore } from "../features/auth/store";

export function DashboardPage() {
  const token = useAuthStore((s) => s.token);
  const user = useAuthStore((s) => s.user);
  const balance = useAuthStore((s) => s.balance);
  const { data } = useQuery({
    queryKey: ["reports", token],
    queryFn: () => apiFetch<any[]>("/api/reports", token ?? undefined),
    enabled: Boolean(token),
  });

  return (
    <div className="grid gap-4 md:grid-cols-2">
      <Card>
        <div className="text-sm text-slate-400">Аккаунт</div>
        <div className="mt-2 text-2xl font-semibold">{user?.first_name ?? "Гость"}</div>
        <div className="mt-3 text-sm text-slate-300">Доступно запросов: {balance?.available_requests ?? 0}</div>
        <div className="text-sm text-slate-400">Реферальный код: {user?.referral_code ?? "..."}</div>
      </Card>
      <Card className="bg-gradient-to-br from-sky-500/20 to-emerald-500/10">
        <div className="text-sm text-slate-300">Последняя активность</div>
        <div className="mt-3 text-4xl font-semibold">{data?.length ?? 0}</div>
        <div className="text-sm text-slate-400">отчетов в истории</div>
      </Card>
      <Card className="md:col-span-2">
        <div className="text-lg font-semibold">Как использовать максимально эффективно</div>
        <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-slate-300">
          <li>Опишите идею максимально конкретно: ниша, клиент, боль, формат монетизации.</li>
          <li>Сверяйте summary в боте и разворачивайте полную детализацию в истории.</li>
          <li>Скачивайте PDF и используйте его как основу для запуска MVP за 2 недели.</li>
        </ul>
      </Card>
    </div>
  );
}

