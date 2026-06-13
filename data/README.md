# Data

This folder stores local datasets used during MarketMind development.

CSV files are not pushed to GitHub because product review datasets can be large. The repository keeps `.gitkeep` files so the expected folder structure remains visible.

## Folders

- `data/raw/`: Original downloaded datasets.
- `data/processed/`: Cleaned datasets created during preprocessing.

## Expected Local Paths

- Raw dataset: `data/raw/Equal.csv`
- Processed dataset: `data/processed/marketmind_clean_reviews.csv`

## Raw Dataset Columns

- `ProductName`
- `ProductPrice`
- `Rate`
- `Review`
- `Summary`
- `Sentiment`

## Cleaned Dataset Columns

- `product_name`
- `clean_price`
- `rating`
- `full_review`
- `sentiment`
