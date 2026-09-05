import { AppNav } from "@/components/layout/AppNav";

export function AppShell({
  children,
  panel,
}: {
  children: React.ReactNode;
  /** Optional right-hand rail, e.g. the research agent panel on Feed/Detail. */
  panel?: React.ReactNode;
}) {
  return (
    <div
      className="h-screen grid bg-surface text-ink font-sans overflow-hidden"
      style={{ gridTemplateColumns: panel ? "220px minmax(0,1fr) 340px" : "220px minmax(0,1fr)" }}
    >
      <AppNav />
      <main className="overflow-y-auto">{children}</main>
      {panel}
    </div>
  );
}
