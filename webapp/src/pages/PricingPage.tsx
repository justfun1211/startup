import { useQuery } from "@tanstack/react-query";
import { Card } from "../components/Card";
import { apiFetch } from "../lib/api";

export function PricingPage() {
  const { data = [] } = useQuery({
    queryKey: ["packs"],
    queryFn: () => apiFetch<any[]>("/api/pricing/packs"),
  });

  return (
    <div className="grid gap-4 md:grid-cols-3">
      {data.map((pack) => (
        <Card key={pack.code} className="bg-gradient-to-b from-white/10 to-slate-900/60">
          <div className="text-sm text-slate-400">{pack.code}</div>
          <div className="mt-2 text-2xl font-semibold">{pack.title}</div>
          <div className="mt-2 text-sm text-slate-300">{pack.description}</div>
          <div className="mt-6 text-3xl font-semibold">{pack.stars_amount} XTR</div>
          <div className="text-sm text-slate-400">{pack.requests_amount} запросов</div>
          <div className="mt-6 rounded-2xl bg-sky-500 px-4 py-3 text-center text-sm">Покупка запускается через /buy в чате с ботом</div>
        </Card>
      ))}
    </div>
  );
}

