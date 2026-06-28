# MarketMind Data Layer Upgrade Plan

This plan describes how MarketMind can move from a single processed CSV file to a local SQLite-backed data layer. It is a planning document only; no backend logic, dashboard code, datasets, requirements, or README content are changed here.

## 1. Current Data-Layer Assessment

MarketMind currently stores raw review data as local CSV files under `data/raw/` and writes one cleaned CSV to `data/processed/marketmind_clean_reviews.csv`. The local processed dataset is available and currently has this schema:

```text
product_name, clean_price, rating, full_review, cleaned_review, sentiment
```

The local processed file has about 76,745 data rows plus the header. It is intentionally ignored by Git, so each developer needs a local copy.

Current loading pattern:

- `src/data_preprocessing.py` reads `data/raw/Equal.csv`, cleans it, and writes `data/processed/marketmind_clean_reviews.csv`.
- `src/sentiment_model.py`, `src/complaint_miner.py`, `src/persona_generator.py`, `src/scoring_engine.py`, `src/product_comparator.py`, and `src/concept_simulator.py` read the processed CSV with `pandas.read_csv`.
- `app/streamlit_app.py` uses `st.cache_data` for the dashboard's product-analysis CSV load, but `simulate_product_concept()` still loads the CSV internally.
- Product lookup is currently based on normalized product-name text, with exact matching first and partial matching as fallback.
- Product concept simulation rebuilds persona clusters and transforms review text for similarity during the simulation flow.

Inefficiencies in the current CSV approach:

- Each backend entry point can load the whole processed CSV even when only one product or category is needed.
- Product search requires string operations over the full DataFrame.
- Product comparison repeatedly analyzes each product from the same in-memory DataFrame, but there is no shared repository layer for filtered database queries.
- Concept simulation loads the full processed CSV, rebuilds KMeans persona clusters, and recalculates review TF-IDF vectors during each run.
- The current CSV has no primary keys, foreign keys, source tracking, or durable product identity.
- Adding more datasets will make full-file reads, full-data clustering, and full-data similarity search slower and harder to debug.

Data-quality risks:

- Garbled product titles: current code already includes console-safe printing and partial matching because some names contain encoding artifacts. A database layer should preserve original names while also storing normalized names for matching.
- Missing product IDs: products are identified by text only, so equivalent product titles from different datasets may split into separate products or unrelated titles may merge accidentally.
- Mixed categories: the current schema has no category field. Similarity retrieval across all reviews may match unrelated categories and produce weak concept feedback.
- Duplicate reviews: without source IDs or deduplication fingerprints, repeated reviews can inflate sentiment, complaint frequency, health scores, and persona evidence counts.
- Repeated full-dataset processing: preprocessing, clustering, complaint mining, and similarity retrieval repeatedly operate on broad DataFrames instead of using persisted, reusable data slices and artifacts.

## 2. Recommended Local Database Choice

SQLite is the recommended next database for MarketMind.

Why SQLite fits now:

- It is local, file-based, and beginner-friendly.
- Python includes `sqlite3` in the standard library, so the first version does not require a new dependency.
- It is enough for a laptop-scale product-review prototype with tens of thousands to a few hundred thousand reviews.
- It supports primary keys, foreign keys, indexes, uniqueness constraints, and simple SQL queries.
- It keeps the project easy to run without accounts, cloud setup, credentials, billing, or network access.
- It is a good stepping stone: repository functions can later be moved to PostgreSQL if the project grows.

Why not Firebase yet:

- Firebase is a cloud service and adds authentication, project configuration, security rules, and vendor-specific operational work.
- MarketMind's current workload is local analytics over structured review data, not real-time multi-user synchronization.

Why not MongoDB yet:

- MongoDB is useful for flexible document storage, but the planned data model is naturally relational: products have many reviews, reviews come from dataset sources, and product/category filters need indexes.
- Adding a separate database server would increase setup complexity without solving the immediate bottlenecks.

Why not PostgreSQL yet:

- PostgreSQL is powerful and a good future option, but it requires server setup and connection configuration.
- The current project does not yet need concurrent multi-user writes, production deployment, or advanced database operations.
- Starting with SQLite keeps Phase 9 focused on schema quality and clean repository functions.

## 3. Proposed Database Schema

Suggested local database path:

```text
data/marketmind.db
```

The database file should be ignored by Git, like local CSVs and model artifacts.

### `dataset_sources`

Optional but recommended once multiple datasets are added.

Columns:

- `source_id` INTEGER PRIMARY KEY
- `source_name` TEXT NOT NULL
- `source_file` TEXT
- `source_type` TEXT DEFAULT 'csv'
- `source_category` TEXT
- `license_notes` TEXT
- `imported_at` TEXT NOT NULL
- `row_count_raw` INTEGER DEFAULT 0
- `row_count_inserted` INTEGER DEFAULT 0
- `row_count_skipped` INTEGER DEFAULT 0
- `notes` TEXT

Important indexes:

- `idx_dataset_sources_name` on `source_name`
- `idx_dataset_sources_category` on `source_category`

### `products`

Columns:

- `product_id` TEXT PRIMARY KEY
- `original_product_name` TEXT NOT NULL
- `normalized_product_name` TEXT NOT NULL
- `display_product_name` TEXT NOT NULL
- `category` TEXT
- `brand` TEXT
- `clean_price` REAL
- `source_id` INTEGER
- `created_at` TEXT NOT NULL
- `updated_at` TEXT NOT NULL

Foreign keys:

- `source_id` REFERENCES `dataset_sources(source_id)`

Important indexes:

- `idx_products_normalized_name` on `normalized_product_name`
- `idx_products_category` on `category`
- `idx_products_source_id` on `source_id`
- Optional unique index on `(normalized_product_name, category, source_id)` after normalization rules are stable

Product ID strategy:

- Create stable IDs from a deterministic hash of normalized product name, category, and source information.
- Preserve `original_product_name` exactly as found in the source.
- Use `display_product_name` as the cleaned human-readable name shown in the UI.

### `reviews`

Columns:

- `review_id` TEXT PRIMARY KEY
- `product_id` TEXT NOT NULL
- `source_id` INTEGER
- `source_dataset` TEXT NOT NULL
- `category` TEXT
- `rating` REAL
- `sentiment` TEXT
- `review_title` TEXT
- `review_text` TEXT
- `full_review` TEXT NOT NULL
- `cleaned_review` TEXT NOT NULL
- `review_fingerprint` TEXT NOT NULL
- `created_at` TEXT NOT NULL

Foreign keys:

- `product_id` REFERENCES `products(product_id)`
- `source_id` REFERENCES `dataset_sources(source_id)`

Important indexes:

- `idx_reviews_product_id` on `product_id`
- `idx_reviews_category` on `category`
- `idx_reviews_sentiment` on `sentiment`
- `idx_reviews_rating` on `rating`
- `idx_reviews_source_dataset` on `source_dataset`
- `idx_reviews_fingerprint` on `review_fingerprint`
- Unique index on `(product_id, review_fingerprint)` to reduce duplicate reviews for the same product

Review ID strategy:

- Create stable IDs from a deterministic hash of source dataset, normalized product name, rating, and cleaned review text.
- Use `review_fingerprint` for deduplication, likely based on normalized product name plus cleaned review text. Keep this separate from `review_id` so deduplication rules can be audited.

## 4. Data-Ingestion Strategy

The ingestion flow should preserve raw files and map every dataset into one common database schema.

Recommended steps:

1. Keep downloaded source files in `data/raw/`.
2. Add an ingestion script that reads one source file at a time.
3. Standardize source columns into the common fields used by `products`, `reviews`, and `dataset_sources`.
4. Add `source_dataset` and `category` during ingestion, even when they must be manually configured for a dataset.
5. Generate stable `product_id` values from normalized product name, category, and source.
6. Normalize product names for matching while preserving original product names for display and audit.
7. Generate review fingerprints and skip clear duplicates.
8. Write a data-quality report for every ingestion run.

Name handling:

- Store original product names exactly as received.
- Store normalized product names for lookup and product ID generation.
- Store display product names for dashboard use.
- Track suspicious names with replacement characters, broken encodings, empty strings, or unusually long titles in the quality report.

Deduplication should be careful, not aggressive:

- Exact duplicate cleaned reviews for the same normalized product can be skipped.
- Near-duplicate detection can be planned later, but should not be added until false positives are reviewed.
- Reviews from different products should not be merged only because the text is similar.

Data-quality report fields:

- Source dataset name
- Raw row count
- Inserted review count
- Skipped row count
- Duplicate review count
- Missing product-name count
- Missing review-text count
- Missing or invalid rating count
- Missing category count
- Suspicious or garbled product-name examples
- Sentiment-label distribution

## 5. Dataset Expansion Strategy

MarketMind should add product-review datasets that improve coverage without making similarity retrieval noisy.

Best datasets to add:

- Category-labelled consumer-product reviews
- E-commerce review datasets with product names, review text, rating, and category
- Datasets with enough reviews per product to support product-level health scoring
- Datasets focused on everyday consumer products, electronics, home goods, fitness products, personal accessories, and student/gym/travel-friendly items

Avoid for now:

- App-store reviews, movie reviews, restaurant reviews, or service reviews mixed into the same retrieval pool as physical products
- Datasets without clear product names or categories
- Very large datasets that cannot be inspected manually during early migration

Realistic first target size:

- Move from about 76,745 local rows to roughly 100,000 to 250,000 cleaned reviews first.
- This is large enough to test scaling and category filtering, but still realistic for a laptop, pandas, SQLite, and scikit-learn artifacts.
- After the pipeline is stable, test larger targets in controlled steps.

Avoiding unrelated-category matches:

- Require a category value for each review whenever possible.
- Let concept simulation accept or infer a broad category, then filter candidate reviews by category before cosine similarity.
- If category is missing, use only a controlled fallback pool and clearly mark confidence as lower.
- Keep category labels coarse at first, such as `electronics`, `kitchen`, `fitness`, `beauty`, `home`, `student accessories`, and `bottles`.

## 6. Performance Strategy

The goal is to avoid reloading and recomputing the full dataset for every analysis.

Recommended performance changes for later implementation:

- Load data once per dashboard session through repository functions and Streamlit caching.
- Use `st.cache_data` for query results that return DataFrames.
- Use `st.cache_resource` for heavier reusable artifacts such as vectorizers, sparse review vectors, and persona models.
- Save and reuse persona clusters instead of running full KMeans inside each concept simulation.
- Precompute TF-IDF review vectors after ingestion or model training.
- Store a review-vector artifact keyed by dataset version, category, or artifact metadata.
- Filter by category before cosine similarity so a bottle concept does not search unrelated categories first.
- Load only needed columns from SQLite for each workflow.
- Avoid full CSV loading in `simulate_product_concept()` and product-analysis flows once repository functions exist.
- Recompute artifacts only when the database version, source datasets, or preprocessing rules change.

Suggested reusable artifacts:

- `models/tfidf_vectorizer.pkl`
- `models/review_tfidf_matrix.joblib`
- `models/review_vector_metadata.joblib`
- `models/persona_cluster_model.joblib`
- `reports/persona_profiles.csv` or a future database/artifact equivalent

Artifact metadata should include:

- Source database path
- Review count used
- Category scope
- Preprocessing version
- Created timestamp
- Vectorizer parameters

## 7. Exact Files Likely to Be Created or Modified Later

Likely new files:

- `src/database.py` - SQLite connection helpers and schema initialization
- `src/review_repository.py` - database-backed product and review query functions
- `src/ingest_reviews.py` - CSV-to-SQLite ingestion entry point
- `src/artifact_builder.py` - builds cached TF-IDF vectors and persona artifacts
- `src/data_quality.py` - data-quality checks and report helpers
- `data/marketmind.db` - local SQLite database, ignored by Git
- `reports/data_quality_report.csv` - ingestion quality summary
- `models/review_tfidf_matrix.joblib` - precomputed sparse review vectors
- `models/review_vector_metadata.joblib` - metadata for cached review vectors
- `models/persona_cluster_model.joblib` - reusable KMeans artifact if needed

Likely modified files:

- `.gitignore` - ignore `data/*.db`, SQLite sidecar files, and generated artifacts if needed
- `data/README.md` - document database path, raw-data preservation, and ingestion workflow
- `requirements.txt` - likely no change for SQLite if using Python `sqlite3`; only change if a deliberate helper library is added later
- `src/data_preprocessing.py` - reuse cleaning helpers during ingestion instead of only writing CSV
- `src/sentiment_model.py` - train from repository-loaded reviews or a database export
- `src/complaint_miner.py` - accept review DataFrames from repository queries
- `src/persona_generator.py` - save/reuse persona outputs instead of recomputing everywhere
- `src/concept_simulator.py` - use repository filters and cached similarity artifacts
- `src/scoring_engine.py` - query product reviews by `product_id` or normalized name
- `src/product_comparator.py` - compare products through repository-backed lookups
- `app/streamlit_app.py` - call repository functions and cached artifacts
- `README.md` - update only after the migration is implemented and validated

## 8. Migration Stages

### Phase 9A: Database Schema and Migration Script

Goal: create the SQLite schema and migrate the current processed CSV into it.

Tasks:

- Create schema initialization logic.
- Add `products`, `reviews`, and optional `dataset_sources` tables.
- Generate stable product IDs and review IDs.
- Preserve original product names and cleaned review fields.
- Add category support, with current rows marked as `unknown` or a manually selected source category until better labels exist.
- Produce a data-quality report.
- Validate row counts against the existing processed CSV.

Success criteria:

- SQLite database is created locally.
- Review count matches expectations after skipped invalid rows and duplicates are explained.
- Product lookup by normalized name works for known examples.
- No existing CSV flow is removed yet.

### Phase 9B: Database-Backed Repository Functions

Goal: introduce a small query layer without changing model behavior.

Tasks:

- Add functions for product search, product reviews, category-filtered reviews, sentiment distributions, and source summaries.
- Keep return values compatible with existing pandas-based functions where practical.
- Add simple checks for empty query, no matched product, and multiple matched products.

Success criteria:

- Existing product health analysis can be run from database-loaded reviews in a test path.
- Product comparison can reuse the same repository functions.
- Current dashboard behavior can still be reproduced.

### Phase 9C: Dataset Expansion and Ingestion

Goal: add more review data safely.

Tasks:

- Define accepted source schema mappings per dataset.
- Require `source_dataset` and category assignment.
- Ingest one new dataset at a time.
- Review quality reports before using new data in simulation.
- Keep raw files unchanged.

Success criteria:

- New datasets are loaded into the shared schema.
- Duplicate and invalid-row counts are visible.
- Category labels are good enough for filtered similarity retrieval.

### Phase 9D: Cached Similarity and Persona Artifacts

Goal: reduce expensive repeated computation.

Tasks:

- Build review TF-IDF vectors once and save them with metadata.
- Save reusable persona clusters or persona profiles.
- Add category-specific retrieval support.
- Rebuild artifacts only after database or preprocessing changes.

Success criteria:

- Concept simulation no longer recomputes full KMeans and full review-vector transforms on every run.
- Similarity retrieval can filter by category first.
- Artifact metadata makes stale-cache problems easy to detect.

### Phase 9E: Dashboard Integration and Validation

Goal: connect the Streamlit dashboard to the database-backed layer.

Tasks:

- Replace direct CSV loading in the dashboard with repository functions.
- Cache database query results and heavy artifacts with Streamlit.
- Keep user-facing outputs consistent with the current dashboard.
- Add clear messages when category coverage or review evidence is low.

Success criteria:

- Product Concept Simulator and Existing Product Analyzer work through the database-backed layer.
- Results are close to the previous CSV-based outputs for the same dataset.
- Runtime is acceptable on the local laptop.

## 9. Risks and Validation Steps

Risks:

- Product ID generation may split the same product into multiple records if names vary too much.
- Product ID generation may merge unrelated products if normalization is too aggressive.
- Category labels may be too broad or too inconsistent for reliable similarity retrieval.
- Deduplication may remove valid repeated reviews if fingerprints are too broad.
- Cached TF-IDF or persona artifacts may become stale after ingestion changes.
- SQLite queries may still return too many rows if indexes and filters are not designed carefully.
- Scores may shift after deduplication or category filtering, so old example outputs should not be treated as fixed targets.

Validation steps:

- Compare processed CSV row count with inserted, skipped, and duplicate counts.
- Verify table schemas, primary keys, foreign keys, and indexes.
- Test known product searches such as `AWC-38`.
- Compare product health outputs before and after database-backed loading on the same data.
- Compare concept simulation outputs on the Smart Water Bottle example before and after cached retrieval.
- Inspect a sample of normalized names, product IDs, and duplicate decisions manually.
- Test category-filtered similarity with concepts from at least two different categories.
- Confirm Streamlit caching does not hide database updates during development.
- Confirm database files and generated large artifacts are ignored by Git.

## Recommended First Implementation Phase

Start with Phase 9A only: create the SQLite schema and a migration script for the existing processed CSV. This gives MarketMind durable product and review IDs, source tracking, deduplication reporting, and a clean base for later repository functions without changing the dashboard or model behavior immediately.
