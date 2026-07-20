import { PageHeader } from "../components/PageHeader";
import { PlaceholderPanel } from "../components/PlaceholderPanel";

export function ProductsPage() {
  return (
    <>
      <PageHeader
        eyebrow="Catalog"
        title="Products"
        description="Product search, health summaries, and comparison workflows will consume the existing product API routes here."
      />
      <PlaceholderPanel title="Products foundation">
        <p>Product workflows are reserved for the next frontend implementation phase.</p>
      </PlaceholderPanel>
    </>
  );
}
