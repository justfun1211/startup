import { NavLink } from "react-router-dom";

const links = [
  { to: "/", label: "Dashboard" },
  { to: "/history", label: "История" },
  { to: "/pricing", label: "Тарифы" },
  { to: "/referrals", label: "Рефералы" },
  { to: "/admin", label: "Admin" },
];

export function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="mx-auto flex min-h-screen max-w-5xl flex-col px-4 pb-8 pt-6">
      <header className="rounded-[28px] border border-white/10 bg-white/5 p-5 shadow-glass backdrop-blur">
        <div className="text-xs uppercase tracking-[0.3em] text-sky-200/70">Proofbot</div>
        <h1 className="mt-2 text-3xl font-semibold">Бот-аналитик и промоутер стартап-идей</h1>
        <p className="mt-2 max-w-2xl text-sm text-slate-300">
          Структурированные AI-отчеты, история запусков, PDF и инструменты роста в одном Mini App.
        </p>
      </header>
      <nav className="mt-4 flex gap-2 overflow-auto rounded-3xl border border-white/10 bg-slate-900/60 p-2">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            className={({ isActive }) =>
              `rounded-2xl px-4 py-2 text-sm ${isActive ? "bg-sky-500 text-white" : "text-slate-300"}`
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

