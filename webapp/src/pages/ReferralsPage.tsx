import { useQuery } from "@tanstack/react-query";
import { Card } from "../components/Card";
import { apiFetch } from "../lib/api";
import { useAuthStore } from "../features/auth/store";

export function ReferralsPage() {
  const token = useAuthStore((s) => s.token);
  const { data } = useQuery({
    queryKey: ["referrals", token],
    queryFn: () => apiFetch<any>("/api/referrals/me", token ?? undefined),
    enabled: Boolean(token),
  });

  if (!data) {
    return <Card>Загружаем реферальную статистику...</Card>;
  }

  return (
    <div className="space-y-4">
      <Card>
        <div className="text-sm text-slate-400">Личная ссылка</div>
        <div className="mt-3 break-all rounded-2xl bg-slate-950/80 p-4 text-sm">{data.referral_link}</div>
      </Card>
      <div className="grid gap-4 md:grid-cols-3">
        <Card><div className="text-sm text-slate-400">Приглашено</div><div className="mt-2 text-3xl">{data.invited_count}</div></Card>
        <Card><div className="text-sm text-slate-400">Награждено</div><div className="mt-2 text-3xl">{data.rewarded_count}</div></Card>
        <Card><div className="text-sm text-slate-400">Бонусы</div><div className="mt-2 text-3xl">{data.total_bonus_requests}</div></Card>
      </div>
    </div>
  );
}

