import type { ReactNode } from "react";

type PlaceholderPanelProps = {
  title: string;
  children: ReactNode;
};

export function PlaceholderPanel({ title, children }: PlaceholderPanelProps) {
  return (
    <section className="placeholder-panel">
      <h2>{title}</h2>
      <div>{children}</div>
    </section>
  );
}
