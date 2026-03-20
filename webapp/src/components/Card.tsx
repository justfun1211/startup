import clsx from "clsx";

export function Card({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return <section className={clsx("rounded-[24px] border border-white/10 bg-white/5 p-5 shadow-glass", className)}>{children}</section>;
}

