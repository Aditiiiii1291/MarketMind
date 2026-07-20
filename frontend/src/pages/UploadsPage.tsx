import { PageHeader } from "../components/PageHeader";
import { PlaceholderPanel } from "../components/PlaceholderPanel";

export function UploadsPage() {
  return (
    <>
      <PageHeader
        eyebrow="Data"
        title="Uploads"
        description="Authenticated CSV upload and upload history screens will reuse the existing upload backend."
      />
      <PlaceholderPanel title="Uploads foundation">
        <p>The upload workflow is intentionally not implemented in this architecture pass.</p>
      </PlaceholderPanel>
    </>
  );
}
