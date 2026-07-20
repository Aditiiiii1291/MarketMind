export type SentimentBucket = {
  count: number;
  percentage: number;
};

export type SentimentDistribution = {
  negative?: SentimentBucket;
  neutral?: SentimentBucket;
  positive?: SentimentBucket;
};

export type DashboardMetrics = {
  review_count?: number;
  average_rating?: number;
  negative_percentage?: number;
  health_score?: number;
  health_label?: string;
  error?: string | null;
};

export type ReviewRecord = {
  product_name?: string;
  clean_price?: number | null;
  rating?: number | null;
  full_review?: string | null;
  cleaned_review?: string | null;
  sentiment?: string | null;
  category?: string | null;
  product_id?: string | null;
};

export type ProductHealthResult = {
  product_query?: string;
  matched_product_names?: string[];
  product_reviews?: ReviewRecord[];
  metrics?: DashboardMetrics;
  sentiment_distribution?: SentimentDistribution;
  health_score?: number;
  health_label?: string;
  recommendations?: string[];
  error?: string | null;
};

export type DashboardTables = {
  sentiment_distribution?: SentimentDistribution;
  category_summary?: Array<Record<string, unknown>>;
  matched_product_names?: string[];
};

export type DashboardResponse = {
  result?: ProductHealthResult;
  metrics?: DashboardMetrics;
  tables?: DashboardTables;
  error?: string | null;
};

export type ProductSummaryRow = {
  productName: string;
  reviewCount: number;
  averageRating: number;
  category: string;
};
