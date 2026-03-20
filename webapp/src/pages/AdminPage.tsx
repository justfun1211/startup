import { FormEvent, useMemo, useState } from "react";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Card } from "../components/Card";
import { useAuthStore } from "../features/auth/store";
import { apiFetch } from "../lib/api";

type GrantFormState = {
  telegramId: string;
  requests: string;
  comment: string;
};

type BroadcastFormState = {
  messageText: string;
  telegramFileId: string;
  dryRun: boolean;
};

function formatDate(value?: string) {
  if (!value) {
    return "—";
  }
  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export function AdminPage() {
  const queryClient = useQueryClient();
  const token = useAuthStore((state) => state.token);
  const user = useAuthStore((state) => state.user);
  const isBootstrapping = useAuthStore((state) => state.isBootstrapping);

  const [grantForm, setGrantForm] = useState<GrantFormState>({
    telegramId: "",
    requests: "5",
    comment: "",
  });
  const [broadcastForm, setBroadcastForm] = useState<BroadcastFormState>({
    messageText: "",
    telegramFileId: "",
    dryRun: true,
  });
  const [searchedTelegramId, setSearchedTelegramId] = useState<string>("");
  const [feedback, setFeedback] = useState<string | null>(null);

  const overviewQuery = useQuery({
    queryKey: ["admin-overview", token],
    queryFn: () => apiFetch<any>("/api/admin/overview", token ?? undefined),
    enabled: Boolean(token && user?.is_admin),
  });

  const broadcastsQuery = useQuery({
    queryKey: ["admin-broadcasts", token],
    queryFn: () => apiFetch<any[]>("/api/admin/broadcasts", token ?? undefined),
    enabled: Boolean(token && user?.is_admin),
  });

  const recentUsersQuery = useQuery({
    queryKey: ["admin-recent-users", token],
    queryFn: () => apiFetch<any[]>("/api/admin/recent-users", token ?? undefined),
    enabled: Boolean(token && user?.is_admin),
  });

  const actionLogsQuery = useQuery({
    queryKey: ["admin-action-logs", token],
    queryFn: () => apiFetch<any[]>("/api/admin/action-logs", token ?? undefined),
    enabled: Boolean(token && user?.is_admin),
  });

  const userQuery = useQuery({
    queryKey: ["admin-user", searchedTelegramId, token],
    queryFn: () => apiFetch<any>(`/api/admin/users/${searchedTelegramId}`, token ?? undefined),
    enabled: Boolean(token && user?.is_admin && searchedTelegramId),
    retry: false,
  });

  const grantMutation = useMutation({
    mutationFn: () =>
      apiFetch(`/api/admin/users/${grantForm.telegramId}/grant`, token ?? undefined, {
        method: "POST",
        body: JSON.stringify({
          requests: Number(grantForm.requests),
          comment: grantForm.comment || null,
        }),
      }),
    onSuccess: async () => {
      setFeedback("Запросы успешно начислены.");
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["admin-user", searchedTelegramId, token] }),
        queryClient.invalidateQueries({ queryKey: ["admin-overview", token] }),
        queryClient.invalidateQueries({ queryKey: ["admin-recent-users", token] }),
        queryClient.invalidateQueries({ queryKey: ["admin-action-logs", token] }),
      ]);
    },
    onError: (error: Error) => {
      setFeedback(error.message);
    },
  });

  const broadcastMutation = useMutation({
    mutationFn: () =>
      apiFetch(`/api/admin/broadcasts`, token ?? undefined, {
        method: "POST",
        body: JSON.stringify({
          message_text: broadcastForm.messageText,
          telegram_file_id: broadcastForm.telegramFileId || null,
          dry_run: broadcastForm.dryRun,
        }),
      }),
    onSuccess: async () => {
      setFeedback("Рассылка поставлена в очередь.");
      setBroadcastForm({ messageText: "", telegramFileId: "", dryRun: true });
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["admin-broadcasts", token] }),
        queryClient.invalidateQueries({ queryKey: ["admin-action-logs", token] }),
      ]);
    },
    onError: (error: Error) => {
      setFeedback(error.message);
    },
  });

  function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFeedback(null);
    setSearchedTelegramId(grantForm.telegramId.trim());
  }

  function handleGrant(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFeedback(null);
    grantMutation.mutate();
  }

  function handleBroadcast(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFeedback(null);
    broadcastMutation.mutate();
  }

  const actionLogs = useMemo(() => actionLogsQuery.data ?? [], [actionLogsQuery.data]);

  if (isBootstrapping) {
    return <Card>Проверяем доступ администратора...</Card>;
  }

  if (!user?.is_admin) {
    return <Card>Доступ к админке есть только у аккаунтов из списка администраторов.</Card>;
  }

  return (
    <div className="space-y-4">
      {feedback ? (
        <Card className="border-emerald-400/20 bg-emerald-500/10 text-emerald-100">{feedback}</Card>
      ) : null}

      <Card>
        <div className="text-lg font-semibold">Панель управления</div>
        <p className="mt-2 text-sm text-slate-400">Метрики, пользователи, ручная выдача, рассылки и аудит действий.</p>
      </Card>

      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard label="DAU" value={overviewQuery.data?.dau} />
        <MetricCard label="MAU" value={overviewQuery.data?.mau} />
        <MetricCard label="Новые 24ч" value={overviewQuery.data?.new_users_24h} />
        <MetricCard label="Анализы 7д" value={overviewQuery.data?.analyses_7d} />
        <MetricCard label="Оплаты 7д" value={overviewQuery.data?.payments_7d} />
        <MetricCard label="XTR 30д" value={overviewQuery.data?.stars_30d} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <div className="text-lg font-semibold">Пользователь и ручная выдача</div>
          <form className="mt-4 space-y-3" onSubmit={handleSearch}>
            <input
              className="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-sm"
              onChange={(event) => setGrantForm((state) => ({ ...state, telegramId: event.target.value }))}
              placeholder="Telegram ID пользователя"
              value={grantForm.telegramId}
            />
            <button className="rounded-2xl bg-sky-500 px-4 py-2 text-sm text-white" type="submit">
              Найти пользователя
            </button>
          </form>

          <div className="mt-4 rounded-2xl border border-white/10 bg-slate-950/50 p-4 text-sm">
            {userQuery.isLoading ? "Ищем пользователя..." : null}
            {userQuery.error ? "Пользователь не найден." : null}
            {userQuery.data ? (
              <div className="space-y-2">
                <div>Имя: {userQuery.data.first_name}</div>
                <div>Username: {userQuery.data.username ?? "—"}</div>
                <div>Доступно запросов: {userQuery.data.available_requests}</div>
                <div>Зарезервировано: {userQuery.data.reserved_requests}</div>
              </div>
            ) : null}
          </div>

          <form className="mt-4 space-y-3" onSubmit={handleGrant}>
            <input
              className="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-sm"
              onChange={(event) => setGrantForm((state) => ({ ...state, requests: event.target.value }))}
              placeholder="Сколько запросов выдать"
              value={grantForm.requests}
            />
            <textarea
              className="min-h-28 w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-sm"
              onChange={(event) => setGrantForm((state) => ({ ...state, comment: event.target.value }))}
              placeholder="Комментарий для аудита"
              value={grantForm.comment}
            />
            <button
              className="rounded-2xl bg-emerald-500 px-4 py-2 text-sm text-white disabled:opacity-60"
              disabled={!grantForm.telegramId || grantMutation.isPending}
              type="submit"
            >
              Начислить запросы
            </button>
          </form>
        </Card>

        <Card>
          <div className="text-lg font-semibold">Рассылки</div>
          <form className="mt-4 space-y-3" onSubmit={handleBroadcast}>
            <textarea
              className="min-h-32 w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-sm"
              onChange={(event) => setBroadcastForm((state) => ({ ...state, messageText: event.target.value }))}
              placeholder="Текст рассылки"
              value={broadcastForm.messageText}
            />
            <input
              className="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-sm"
              onChange={(event) => setBroadcastForm((state) => ({ ...state, telegramFileId: event.target.value }))}
              placeholder="Telegram file_id изображения, если нужно"
              value={broadcastForm.telegramFileId}
            />
            <label className="flex items-center gap-3 text-sm text-slate-300">
              <input
                checked={broadcastForm.dryRun}
                onChange={(event) => setBroadcastForm((state) => ({ ...state, dryRun: event.target.checked }))}
                type="checkbox"
              />
              Сначала dry-run только на себя
            </label>
            <button
              className="rounded-2xl bg-sky-500 px-4 py-2 text-sm text-white disabled:opacity-60"
              disabled={!broadcastForm.messageText.trim() || broadcastMutation.isPending}
              type="submit"
            >
              Запустить рассылку
            </button>
          </form>

          <div className="mt-6 space-y-3">
            {(broadcastsQuery.data ?? []).map((broadcast) => (
              <div key={broadcast.id} className="rounded-2xl border border-white/10 bg-slate-950/50 p-4 text-sm">
                <div className="font-medium">{broadcast.status}</div>
                <div className="mt-2 text-slate-300">{broadcast.message_text}</div>
                <div className="mt-3 text-xs text-slate-400">
                  Успешно: {broadcast.success_count} • Ошибок: {broadcast.failure_count} • Целей: {broadcast.total_targets}
                </div>
              </div>
            ))}
            {broadcastsQuery.data?.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-white/10 p-4 text-sm text-slate-400">
                Рассылок пока нет.
              </div>
            ) : null}
          </div>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <div className="flex items-center justify-between">
            <div className="text-lg font-semibold">Последние пользователи</div>
            <div className="text-xs text-slate-400">{recentUsersQuery.data?.length ?? 0} записей</div>
          </div>
          <div className="mt-4 space-y-3">
            {(recentUsersQuery.data ?? []).map((item) => (
              <div key={`${item.telegram_id}-${item.created_at}`} className="rounded-2xl border border-white/10 bg-slate-950/50 p-4 text-sm">
                <div className="flex items-center justify-between gap-3">
                  <div className="font-medium">{item.first_name}</div>
                  <div className="text-xs text-slate-400">{item.telegram_id}</div>
                </div>
                <div className="mt-2 text-slate-300">Баланс: {item.available_requests}</div>
                <div className="mt-1 text-slate-400">
                  Создан: {formatDate(item.created_at)} • Был в сети: {formatDate(item.last_seen_at)}
                </div>
              </div>
            ))}
            {recentUsersQuery.data?.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-white/10 p-4 text-sm text-slate-400">
                Пользователей пока нет.
              </div>
            ) : null}
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div className="text-lg font-semibold">Журнал действий</div>
            <div className="text-xs text-slate-400">{actionLogs.length} записей</div>
          </div>
          <div className="mt-4 space-y-3">
            {actionLogs.map((item) => (
              <div key={item.id} className="rounded-2xl border border-white/10 bg-slate-950/50 p-4 text-sm">
                <div className="flex items-center justify-between gap-3">
                  <div className="font-medium">{item.action_type}</div>
                  <div className="text-xs text-slate-400">{formatDate(item.created_at)}</div>
                </div>
                <div className="mt-2 text-slate-300">
                  Админ: {item.admin_telegram_id ?? "—"}
                  {item.target_telegram_id ? ` • Цель: ${item.target_telegram_id}` : ""}
                </div>
                <div className="mt-2 overflow-hidden rounded-xl bg-slate-950/80 p-3 text-xs text-slate-400">
                  {JSON.stringify(item.payload_json)}
                </div>
              </div>
            ))}
            {actionLogs.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-white/10 p-4 text-sm text-slate-400">
                Журнал пока пуст.
              </div>
            ) : null}
          </div>
        </Card>
      </div>
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value?: number | string }) {
  return (
    <Card>
      <div className="text-sm text-slate-400">{label}</div>
      <div className="mt-2 text-3xl font-semibold">{value ?? "—"}</div>
    </Card>
  );
}
