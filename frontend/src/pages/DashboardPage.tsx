import { useEffect, useMemo, useState } from "react";

import { DashboardCard } from "../components/DashboardCard";
import { DataTable } from "../components/DataTable";
import type { DataTableColumn } from "../components/DataTable";
import { EmptyState } from "../components/EmptyState";
import { ErrorAlert } from "../components/ErrorAlert";
import { LoadingCard } from "../components/LoadingCard";
import { MetricGrid } from "../components/MetricGrid";
import { PageHeader } from "../components/PageHeader";
import { SectionHeader } from "../components/SectionHeader";
import { getApiErrorMessage } from "../services/apiError";
import { getDashboard } from "../services/dashboardService";
import type {
  DashboardResponse,
  ProductSummaryRow,
  ReviewRecord,
  SentimentDistribution
} from "../types/dashboard";

const PRODUCT_COLUMNS: Array<DataTableColumn<ProductSummaryRow>> = [
  {
    key: "productName",
    header: "Product",
    render: (row) => row.productName
  },
  {
    key: "reviewCount",
    header: "Reviews",
    render: (row) => row.reviewCount
  },
  {
    key: "averageRating",
    header: "Avg. rating",
    render: (row) => formatNumber(row.averageRating)
  },
  {
    key: "category",
    header: "Category",
    render: (row) => row.category
  }
];

export function DashboardPage() {
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  async function loadDashboard() {
    setError("");
    setIsLoading(true);

    try {
      const dashboardResponse = await getDashboard();
      setDashboard(dashboardResponse);
    } catch (apiError) {
      setError(getApiErrorMessage(apiError));
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  const dashboardData = useMemo(() => deriveDashboardData(dashboard), [dashboard]);

  return (
    <>
      <PageHeader
        eyebrow="Overview"
        title="Dashboard"
        description="Live product health analytics from the existing MarketMind backend."
      />

      {isLoading ? (
        <DashboardLoadingState />
      ) : error ? (
        <DashboardErrorState message={error} onRetry={loadDashboard} />
      ) : dashboard?.error ? (
        <DashboardErrorState message={dashboard.error} onRetry={loadDashboard} />
      ) : (
        <div className="dashboard-stack">
          <MetricGrid>
            <DashboardCard
              label="Total Products"
              value={dashboardData.totalProducts}
              helper="Matched products"
            />
            <DashboardCard
              label="Total Reviews"
              value={dashboardData.totalReviews}
              helper="Reviews in analysis"
            />
            <DashboardCard
              label="Average Rating"
              value={formatNumber(dashboardData.averageRating)}
              helper="Out of 5"
            />
            <DashboardCard
              label="Average Health Score"
              value={formatNumber(dashboardData.healthScore)}
              helper="Out of 100"
            />
            <DashboardCard
              label="Positive Reviews"
              value={dashboardData.positiveReviews}
              helper={`${formatNumber(dashboardData.sentiment.positive?.percentage ?? 0)}%`}
            />
            <DashboardCard
              label="Neutral Reviews"
              value={dashboardData.neutralReviews}
              helper={`${formatNumber(dashboardData.sentiment.neutral?.percentage ?? 0)}%`}
            />
            <DashboardCard
              label="Negative Reviews"
              value={dashboardData.negativeReviews}
              helper={`${formatNumber(dashboardData.sentiment.negative?.percentage ?? 0)}%`}
            />
          </MetricGrid>

          <section className="dashboard-section">
            <SectionHeader
              title="Health Overview"
              description="Backend product health values for the current dashboard query."
            />
            <MetricGrid>
              <DashboardCard label="Health Label" value={dashboardData.healthLabel} />
              <DashboardCard
                label="Health Score"
                value={formatNumber(dashboardData.healthScore)}
                helper="Calculated by backend"
              />
              <DashboardCard
                label="Recommendation Count"
                value={dashboardData.recommendationCount}
                helper="Recommended actions"
              />
            </MetricGrid>
          </section>

          <DashboardTableSection
            title="Product Summary"
            description="Aggregated from review rows returned by the dashboard endpoint."
            rows={dashboardData.productSummary}
            emptyMessage="No product summary rows were returned."
          />

          <DashboardTableSection
            title="Top Products"
            description="Products sorted by review volume."
            rows={dashboardData.topProducts}
            emptyMessage="No top product rows are available."
          />

          <DashboardTableSection
            title="Lowest Rated Products"
            description="Products sorted by average rating."
            rows={dashboardData.lowestRatedProducts}
            emptyMessage="No lowest rated product rows are available."
          />
        </div>
      )}
    </>
  );
}

function DashboardLoadingState() {
  return (
    <div className="dashboard-stack" aria-label="Loading dashboard">
      <MetricGrid>
        {Array.from({ length: 7 }).map((_, index) => (
          <LoadingCard key={index} />
        ))}
      </MetricGrid>
      <section className="dashboard-section">
        <SectionHeader title="Health Overview" />
        <MetricGrid>
          {Array.from({ length: 3 }).map((_, index) => (
            <LoadingCard key={index} />
          ))}
        </MetricGrid>
      </section>
    </div>
  );
}

type DashboardErrorStateProps = {
  message: string;
  onRetry: () => void;
};

function DashboardErrorState({ message, onRetry }: DashboardErrorStateProps) {
  return (
    <section className="dashboard-section">
      <ErrorAlert message={message} />
      <button className="button button--primary dashboard-retry" onClick={onRetry} type="button">
        Retry dashboard
      </button>
    </section>
  );
}

type DashboardTableSectionProps = {
  title: string;
  description: string;
  rows: ProductSummaryRow[];
  emptyMessage: string;
};

function DashboardTableSection({
  title,
  description,
  emptyMessage,
  rows
}: DashboardTableSectionProps) {
  return (
    <section className="dashboard-section">
      <SectionHeader title={title} description={description} />
      {rows.length === 0 ? (
        <EmptyState title="No data" message={emptyMessage} />
      ) : (
        <DataTable columns={PRODUCT_COLUMNS} emptyMessage={emptyMessage} rows={rows} />
      )}
    </section>
  );
}

function deriveDashboardData(dashboard: DashboardResponse | null) {
  const result = dashboard?.result;
  const metrics = dashboard?.metrics ?? result?.metrics ?? {};
  const sentiment =
    dashboard?.tables?.sentiment_distribution ?? result?.sentiment_distribution ?? {};
  const reviews = result?.product_reviews ?? [];
  const productSummary = buildProductSummaryRows(reviews, result?.matched_product_names ?? []);
  const totalProducts = productSummary.length || dashboard?.tables?.matched_product_names?.length || 0;
  const healthScore = result?.health_score ?? metrics.health_score ?? 0;

  return {
    averageRating: metrics.average_rating ?? average(reviews.map((review) => review.rating)),
    healthLabel: result?.health_label ?? metrics.health_label ?? "Unavailable",
    healthScore,
    negativeReviews: sentiment.negative?.count ?? 0,
    neutralReviews: sentiment.neutral?.count ?? 0,
    positiveReviews: sentiment.positive?.count ?? 0,
    productSummary,
    recommendationCount: result?.recommendations?.length ?? 0,
    sentiment,
    totalProducts,
    totalReviews: metrics.review_count ?? reviews.length,
    topProducts: [...productSummary]
      .sort((first, second) => second.reviewCount - first.reviewCount)
      .slice(0, 5),
    lowestRatedProducts: [...productSummary]
      .sort((first, second) => first.averageRating - second.averageRating)
      .slice(0, 5)
  };
}

function buildProductSummaryRows(
  reviews: ReviewRecord[],
  matchedProductNames: string[]
): ProductSummaryRow[] {
  const groupedReviews = new Map<string, ReviewRecord[]>();

  for (const review of reviews) {
    const productName = review.product_name?.trim() || "Unknown product";
    groupedReviews.set(productName, [...(groupedReviews.get(productName) ?? []), review]);
  }

  if (groupedReviews.size === 0) {
    return matchedProductNames.map((productName) => ({
      averageRating: 0,
      category: "Unavailable",
      productName,
      reviewCount: 0
    }));
  }

  return Array.from(groupedReviews.entries()).map(([productName, productReviews]) => ({
    averageRating: average(productReviews.map((review) => review.rating)),
    category: productReviews.find((review) => review.category)?.category ?? "Uncategorized",
    productName,
    reviewCount: productReviews.length
  }));
}

function average(values: Array<number | null | undefined>): number {
  const numericValues = values.filter(
    (value): value is number => typeof value === "number" && Number.isFinite(value)
  );

  if (numericValues.length === 0) {
    return 0;
  }

  return numericValues.reduce((total, value) => total + value, 0) / numericValues.length;
}

function formatNumber(value: number): string {
  return new Intl.NumberFormat("en", {
    maximumFractionDigits: 2,
    minimumFractionDigits: Number.isInteger(value) ? 0 : 2
  }).format(value);
}
