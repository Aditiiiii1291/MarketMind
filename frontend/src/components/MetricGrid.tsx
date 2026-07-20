import type { ReactNode } from "react";

type MetricGridProps = {
  children: ReactNode;
};

export function MetricGrid({ children }: MetricGridProps) {
  return <section className="metric-grid">{children}</section>;
}
