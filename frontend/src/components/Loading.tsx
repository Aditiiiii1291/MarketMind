type LoadingProps = {
  label?: string;
};

export function Loading({ label = "Loading" }: LoadingProps) {
  return (
    <div className="loading" role="status" aria-live="polite">
      <span className="loading__spinner" aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}
