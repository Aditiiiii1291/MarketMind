# MarketMind SQLite Database Schema

Phase 9A introduces a local SQLite database at:

```text
data/marketmind.db
```

This database is generated from the existing processed CSV. It does not replace CSV loading in the dashboard, ML training, sentiment analysis, persona generation, scoring, product comparison, or concept simulation yet.

## Table Overview

```text
dataset_sources
  -> products
      -> reviews
```

- `dataset_sources` records where imported review data came from.
- `products` stores one normalized product record per stable product ID.
- `reviews` stores review text, rating, sentiment, and the product/source links.

## `dataset_sources`

Columns:

- `source_id` INTEGER PRIMARY KEY
- `source_name` TEXT NOT NULL UNIQUE
- `source_path` TEXT
- `imported_at` TEXT NOT NULL
- `description` TEXT

Purpose:

- Tracks each dataset imported into the database.
- Keeps the source name unique so repeated migrations can refer to the same source.

## `products`

Columns:

- `product_id` TEXT PRIMARY KEY
- `product_name` TEXT NOT NULL
- `normalized_name` TEXT NOT NULL
- `category` TEXT NOT NULL DEFAULT 'Uncategorized'
- `clean_price` REAL
- `source_id` INTEGER
- `created_at` TEXT NOT NULL

Foreign key:

- `source_id` references `dataset_sources(source_id)`

Purpose:

- Preserves the original product name in `product_name`.
- Stores a normalized product name for matching and stable ID generation.
- Uses `Uncategorized` for Phase 9A because the current processed CSV does not provide reliable categories.

## `reviews`

Columns:

- `review_id` TEXT PRIMARY KEY
- `product_id` TEXT NOT NULL
- `rating` REAL
- `full_review` TEXT
- `cleaned_review` TEXT NOT NULL
- `sentiment` TEXT
- `source_id` INTEGER
- `created_at` TEXT NOT NULL

Foreign keys:

- `product_id` references `products(product_id)`
- `source_id` references `dataset_sources(source_id)`

Purpose:

- Stores the review fields currently available in `data/processed/marketmind_clean_reviews.csv`.
- Uses stable deterministic review IDs to skip duplicate reviews during migration.

## Indexes

The schema creates these indexes:

- `idx_products_normalized_name` on `products(normalized_name)`
- `idx_products_category` on `products(category)`
- `idx_reviews_product_id` on `reviews(product_id)`
- `idx_reviews_sentiment` on `reviews(sentiment)`
- `idx_reviews_rating` on `reviews(rating)`
- `idx_reviews_source_id` on `reviews(source_id)`

Why these indexes matter:

- Product name and category indexes prepare for faster product lookup and category filtering.
- Review indexes prepare for product analysis, sentiment summaries, rating filters, source-level checks, and later repository functions.

## Stable IDs

`src/database.py` creates deterministic SHA-256 based IDs:

- Product IDs are based on normalized product names.
- Review IDs are based on product ID, cleaned review text, rating, and source name.

The IDs are shortened to readable prefixes such as `prod_...` and `rev_...`.

## Migration Command

Default migration:

```bash
python scripts/migrate_csv_to_sqlite.py
```

Clean rebuild:

```bash
python scripts/migrate_csv_to_sqlite.py --reset
```

Optional arguments:

```bash
python scripts/migrate_csv_to_sqlite.py --input data/processed/marketmind_clean_reviews.csv --database data/marketmind.db --source-name marketmind_clean_reviews_csv
```

The migration script:

- Validates required CSV columns.
- Creates the database schema if needed.
- Reads the CSV in 5,000-row chunks.
- Preserves the original product name.
- Normalizes product names for IDs and lookup.
- Uses `Uncategorized` as the Phase 9A category.
- Skips invalid rows safely.
- Deduplicates reviews by stable review ID.
- Prints migration and data-quality summaries.

## Phase 9A Boundary

Phase 9A adds the SQLite foundation only. Existing project behavior remains CSV-based until later phases intentionally integrate repository functions into the analysis modules and Streamlit dashboard.
