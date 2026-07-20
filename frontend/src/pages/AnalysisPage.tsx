import { PageHeader } from "../components/PageHeader";
import { PlaceholderPanel } from "../components/PlaceholderPanel";

export function AnalysisPage() {
  return (
    <>
      <PageHeader
        eyebrow="Reports"
        title="Analysis"
        description="AI-ready report and deterministic analysis endpoints will be surfaced here without changing backend contracts."
      />
      <PlaceholderPanel title="Analysis foundation">
        <p>Report forms and analysis results will be added after the routing and auth base stabilizes.</p>
      </PlaceholderPanel>
    </>
  );
}
