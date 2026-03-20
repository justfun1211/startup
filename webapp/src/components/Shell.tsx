import { NavLink } from "react-router-dom";

import { useAuthStore } from "../features/auth/store";

const links = [
  { to: "/", label: "Главная" },
  { to: "/history", label: "История" },
  { to: "/pricing", label: "Покупки" },
  { to: "/referrals", label: "Рефералы" },
  { to: "/admin", label: "Админка", adminOnly: true },
];

export function Shell({ children }: { children: React.ReactNode }) {
  const user = useAuthStore((state) => state.user);
  const isBootstrapping = useAuthStore((state) => state.isBootstrapping);
  const error = useAuthStore((state) => state.error);

  const visibleLinks = links.filter((link) => !link.adminOnly || user?.is_admin);

  return (
    <div className="mx-auto flex min-h-screen max-w-5xl flex-col px-4 pb-8 pt-6">
      <header className="rounded-[28px] border border-white/10 bg-white/5 p-5 shadow-glass backdrop-blur">
        <div className="text-xs uppercase tracking-[0.3em] text-sky-200/70">Proofbot</div>
        <h1 className="mt-2 text-3xl font-semibold">Аналитика стартап-идей</h1>
        <p className="mt-2 max-w-2xl text-sm text-slate-300">
          Запуск анализов, история отчетов, PDF, покупки и рефералы в одном Mini App.
        </p>
        {isBootstrapping ? (
          <div className="mt-4 rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-sm text-slate-300">
            Подключаем аккаунт Telegram...
          </div>
        ) : null}
        {error ? (
          <div className="mt-4 rounded-2xl border border-amber-400/30 bg-amber-400/10 px-4 py-3 text-sm text-amber-100">
            {error}
          </div>
        ) : null}
      </header>
      <nav className="mt-4 flex gap-2 overflow-auto rounded-3xl border border-white/10 bg-slate-900/60 p-2">
        {visibleLinks.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            className={({ isActive }) =>
              `rounded-2xl px-4 py-2 text-sm whitespace-nowrap ${isActive ? "bg-sky-500 text-white" : "text-slate-300"}`
            }
          >
            {link.label}
          </NavLink>
        ))}
      </nav>
      <main className="mt-5">{children}</main>
    </div>
  );
}
