type DashboardCardProps = {
  label: string;
  value: string | number;
  helper?: string;
};

export function DashboardCard({ label, value, helper }: DashboardCardProps) {
  return (
    <article className="dashboard-card">
      <span>{label}</span>
      <strong>{value}</strong>
      {helper ? <p>{helper}</p> : null}
    </article>
  );
}
