import { PageHeader } from "../components/PageHeader";
import { PlaceholderPanel } from "../components/PlaceholderPanel";

export function DashboardPage() {
  return (
    <>
      <PageHeader
        eyebrow="Overview"
        title="Dashboard"
        description="The React dashboard shell is ready for product health, launch readiness, and account-level summaries."
      />
      <PlaceholderPanel title="Dashboard foundation">
        <p>Analytics cards and charts will be connected in a later phase.</p>
      </PlaceholderPanel>
    </>
  );
}
