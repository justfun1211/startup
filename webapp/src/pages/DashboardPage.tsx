import { FormEvent, useMemo, useState } from "react";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { Card } from "../components/Card";
import { useAuthStore } from "../features/auth/store";
import { apiFetch } from "../lib/api";

export function DashboardPage() {
  const queryClient = useQueryClient();
  const token = useAuthStore((state) => state.token);
  const user = useAuthStore((state) => state.user);
  const balance = useAuthStore((state) => state.balance);
  const setBalance = useAuthStore((state) => state.setBalance);
  const [ideaText, setIdeaText] = useState("");
  const [feedback, setFeedback] = useState<string | null>(null);

  const reportsQuery = useQuery({
    queryKey: ["reports", token],
    queryFn: () => apiFetch<any[]>("/api/reports", token ?? undefined),
    enabled: Boolean(token),
    refetchInterval: 15000,
  });

  const createReportMutation = useMutation({
    mutationFn: () =>
      apiFetch<{ message: string }>("/api/reports", token ?? undefined, {
        method: "POST",
        body: JSON.stringify({ source: "twa", input_text: ideaText }),
      }),
    onSuccess: async (data) => {
      setFeedback(data.message);
      setIdeaText("");
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["reports", token] }),
        apiFetch<any>("/api/me/balance", token ?? undefined).then((nextBalance) => setBalance(nextBalance)),
      ]);
    },
    onError: (error: Error) => {
      setFeedback(error.message);
    },
  });

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFeedback(null);
    createReportMutation.mutate();
  }

  const latestReports = useMemo(() => (reportsQuery.data ?? []).slice(0, 3), [reportsQuery.data]);
  const activeReport = latestReports.find((item) => item.status === "queued" || item.status === "processing");

  return (
    <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
      <div className="space-y-4">
        <Card className="bg-gradient-to-br from-sky-500/15 via-slate-950/40 to-emerald-500/10">
          <div className="text-sm text-slate-300">Новый анализ</div>
          <h2 className="mt-2 text-2xl font-semibold">Запустите разбор идеи</h2>
          <p className="mt-2 text-sm text-slate-400">
            Опишите идею в свободной форме. Готовый отчет придет в Mini App и в чат с ботом.
          </p>

          <form className="mt-5 space-y-3" onSubmit={handleSubmit}>
            <textarea
              className="min-h-40 w-full rounded-[24px] border border-white/10 bg-slate-950/70 px-4 py-4 text-sm text-slate-100 outline-none transition focus:border-sky-400/60"
              onChange={(event) => setIdeaText(event.target.value)}
              placeholder="Например: сервис пополнения Steam через Telegram с низкой комиссией для игроков из СНГ."
              value={ideaText}
            />
            <div className="flex flex-wrap items-center gap-3">
              <button
                className="rounded-2xl bg-sky-500 px-5 py-3 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-60"
                disabled={!ideaText.trim() || createReportMutation.isPending}
                type="submit"
              >
                {createReportMutation.isPending ? "Отправляем..." : "Запустить анализ"}
              </button>
              <div className="text-sm text-slate-400">
                Доступно запросов: <span className="font-semibold text-slate-200">{balance?.available_requests ?? 0}</span>
              </div>
            </div>
          </form>

          {feedback ? (
            <div className="mt-4 rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-sm text-slate-200">
              {feedback}
            </div>
          ) : null}
        </Card>
      </div>

      <div className="space-y-4">
        <Card>
          <div className="text-sm text-slate-400">Аккаунт</div>
          <div className="mt-2 text-2xl font-semibold">{user?.first_name ?? "Пользователь"}</div>
          <div className="mt-3 text-sm text-slate-300">
            Доступно запросов: <span className="font-semibold">{balance?.available_requests ?? 0}</span>
          </div>
          <div className="text-sm text-slate-400">Реферальный код: {user?.referral_code ?? "—"}</div>
          <div className="mt-4 flex gap-2">
            <Link className="rounded-2xl bg-white/10 px-4 py-2 text-sm text-slate-200" to="/pricing">
              Покупки
            </Link>
            <Link className="rounded-2xl bg-white/10 px-4 py-2 text-sm text-slate-200" to="/referrals">
              Рефералы
            </Link>
          </div>
        </Card>

        <Card>
          <div className="text-sm text-slate-400">Статус</div>
          {activeReport ? (
            <div className="mt-3 rounded-2xl border border-sky-400/20 bg-sky-500/10 p-4 text-sm text-sky-100">
              Один анализ уже в работе. Как только он завершится, отчет появится в истории и придет уведомление в боте.
            </div>
          ) : (
            <div className="mt-3 rounded-2xl border border-emerald-400/20 bg-emerald-500/10 p-4 text-sm text-emerald-100">
              Очередь свободна. Можно запускать новый анализ.
            </div>
          )}
        </Card>

        <Card>
          <div className="flex items-center justify-between gap-3">
            <div>
              <div className="text-sm text-slate-400">Последние отчеты</div>
              <div className="mt-1 text-xl font-semibold">{reportsQuery.data?.length ?? 0}</div>
            </div>
            <Link className="rounded-2xl bg-sky-500 px-4 py-2 text-sm text-white" to="/history">
              Вся история
            </Link>
          </div>
          <div className="mt-4 space-y-3">
            {latestReports.map((item) => (
              <div key={item.id} className="rounded-2xl border border-white/10 bg-slate-950/50 p-4">
                <div className="text-xs uppercase tracking-[0.2em] text-slate-400">{item.status}</div>
                <div className="mt-2 text-sm text-slate-300">{item.short_summary_text ?? "Отчет еще обрабатывается."}</div>
              </div>
            ))}
            {latestReports.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-white/10 p-4 text-sm text-slate-400">
                Пока нет ни одного отчета.
              </div>
            ) : null}
          </div>
        </Card>
      </div>
    </div>
  );
}
