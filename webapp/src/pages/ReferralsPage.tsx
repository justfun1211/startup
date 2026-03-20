import { useQuery } from "@tanstack/react-query";

import { Card } from "../components/Card";
import { useAuthStore } from "../features/auth/store";
import { apiFetch } from "../lib/api";

export function ReferralsPage() {
  const token = useAuthStore((state) => state.token);
  const isBootstrapping = useAuthStore((state) => state.isBootstrapping);

  const { data, error, isLoading } = useQuery({
    queryKey: ["referrals", token],
    queryFn: () => apiFetch<any>("/api/referrals/me", token ?? undefined),
    enabled: Boolean(token),
  });

  async function copyLink() {
    if (!data?.referral_link) {
      return;
    }
    await navigator.clipboard.writeText(data.referral_link);
  }

  if (isBootstrapping || isLoading) {
    return <Card>Загружаем реферальную статистику...</Card>;
  }

  if (error) {
    return <Card>Не удалось загрузить реферальные данные. Откройте Mini App из Telegram и повторите попытку.</Card>;
  }

  if (!data) {
    return <Card>Реферальные данные пока недоступны.</Card>;
  }

  return (
    <div className="space-y-4">
      <Card>
        <div className="text-sm text-slate-400">Личная ссылка</div>
        <div className="mt-3 break-all rounded-2xl bg-slate-950/80 p-4 text-sm">{data.referral_link}</div>
        <button
          className="mt-4 rounded-2xl bg-sky-500 px-4 py-2 text-sm text-white"
          onClick={copyLink}
          type="button"
        >
          Скопировать ссылку
        </button>
      </Card>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <div className="text-sm text-slate-400">Приглашено</div>
          <div className="mt-2 text-3xl">{data.invited_count}</div>
        </Card>
        <Card>
          <div className="text-sm text-slate-400">С бонусом</div>
          <div className="mt-2 text-3xl">{data.rewarded_count}</div>
        </Card>
        <Card>
          <div className="text-sm text-slate-400">Бонусы</div>
          <div className="mt-2 text-3xl">{data.total_bonus_requests}</div>
        </Card>
      </div>

      <Card>
        <div className="text-lg font-semibold">Как это работает</div>
        <div className="mt-3 text-sm text-slate-300">
          Новый пользователь открывает бота по вашей ссылке и нажимает <span className="font-medium">/start</span>.
          После первого старта бонус начисляется ему и вам.
        </div>
      </Card>
    </div>
  );
}
