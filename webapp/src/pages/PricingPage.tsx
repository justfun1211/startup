import { useEffect, useState } from "react";

import { useMutation, useQuery } from "@tanstack/react-query";

import { Card } from "../components/Card";
import { useAuthStore } from "../features/auth/store";
import { apiFetch } from "../lib/api";

type PendingInvoice = {
  invoicePayload: string;
  packTitle: string;
};

export function PricingPage() {
  const token = useAuthStore((state) => state.token);
  const balance = useAuthStore((state) => state.balance);
  const setBalance = useAuthStore((state) => state.setBalance);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [pendingInvoice, setPendingInvoice] = useState<PendingInvoice | null>(null);

  const { data = [], isLoading } = useQuery({
    queryKey: ["packs"],
    queryFn: () => apiFetch<any[]>("/api/pricing/packs"),
  });

  const paymentStatusQuery = useQuery({
    queryKey: ["payment-status", pendingInvoice?.invoicePayload, token],
    queryFn: () => apiFetch<any>(`/api/payments/${pendingInvoice?.invoicePayload}`, token ?? undefined),
    enabled: Boolean(token && pendingInvoice?.invoicePayload),
    refetchInterval: (query) => (query.state.data?.status === "paid" ? false : 3000),
    refetchIntervalInBackground: true,
  });

  const invoiceMutation = useMutation({
    mutationFn: (pack: { code: string; title: string }) =>
      apiFetch<{ message: string; invoice_payload: string }>(
        `/api/pricing/packs/${pack.code}/invoice`,
        token ?? undefined,
        {
          method: "POST",
        },
      ).then((response) => ({ ...response, packTitle: pack.title })),
    onSuccess: (data) => {
      setPendingInvoice({ invoicePayload: data.invoice_payload, packTitle: data.packTitle });
      setFeedback(data.message);
    },
    onError: (error: Error) => setFeedback(error.message),
  });

  useEffect(() => {
    if (paymentStatusQuery.data?.status !== "paid" || !pendingInvoice || !token) {
      return;
    }

    apiFetch<any>("/api/me/balance", token)
      .then((nextBalance) => {
        setBalance(nextBalance);
        setFeedback(`Оплата за пакет «${pendingInvoice.packTitle}» подтверждена. Баланс обновлен.`);
        setPendingInvoice(null);
      })
      .catch((error: Error) => {
        setFeedback(error.message);
      });
  }, [paymentStatusQuery.data, pendingInvoice, setBalance, token]);

  return (
    <div className="space-y-4">
      {feedback ? (
        <Card className="border-sky-400/20 bg-sky-500/10 text-sky-100">{feedback}</Card>
      ) : null}

      {pendingInvoice ? (
        <Card className="border-amber-400/20 bg-amber-500/10 text-amber-100">
          Ожидаем оплату пакета «{pendingInvoice.packTitle}». После подтверждения баланс обновится автоматически.
        </Card>
      ) : null}

      <Card>
        <div className="text-lg font-semibold">Пакеты запросов</div>
        <p className="mt-2 text-sm text-slate-400">
          Выберите пакет. Счет придет в чат с ботом, после оплаты запросы начислятся автоматически.
        </p>
        <p className="mt-3 text-sm text-slate-300">
          Сейчас доступно: <span className="font-semibold">{balance?.available_requests ?? 0}</span>
        </p>
      </Card>

      {isLoading ? <Card>Загружаем тарифы...</Card> : null}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {data.map((pack) => (
          <Card key={pack.code} className="bg-gradient-to-b from-white/10 to-slate-900/60">
            <div className="text-xs uppercase tracking-[0.2em] text-slate-400">{pack.code}</div>
            <div className="mt-2 text-2xl font-semibold">{pack.title}</div>
            <div className="mt-2 text-sm text-slate-300">{pack.description}</div>
            <div className="mt-6 text-3xl font-semibold">{pack.stars_amount} XTR</div>
            <div className="text-sm text-slate-400">{pack.requests_amount} запросов</div>
            <button
              className="mt-6 w-full rounded-2xl bg-sky-500 px-4 py-3 text-center text-sm text-white disabled:opacity-60"
              disabled={!token || invoiceMutation.isPending}
              onClick={() => {
                setFeedback(null);
                setPendingInvoice(null);
                invoiceMutation.mutate({ code: pack.code, title: pack.title });
              }}
              type="button"
            >
              Купить пакет
            </button>
          </Card>
        ))}
      </div>
    </div>
  );
}
