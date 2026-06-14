# MarketMind Learning Log

## Purpose

This file tracks daily learning, implementation progress, errors faced, fixes applied, outputs generated, Git commits made, and next steps while building MarketMind as an AI/ML project.

## Daily Template

### Date

### Phase

### What I learned

### What I implemented

### Errors / issues faced

### How I fixed them

### Output generated

### Git commit made

### Next step

## Day 1

### Date

Day 1

### Phase

Phase 0 complete; Phase 1 dataset exploration and preprocessing workflow started.

### What I learned

- Project idea finalized as MarketMind.
- Learned that dataset quality matters for AI/ML projects.
- Learned basic pandas dataset inspection commands:
  - `df.head()`
  - `df.shape`
  - `df.columns`
  - `df.info()`
  - `df.isnull().sum()`

### What I implemented

- Created the project folder structure.
- Initialized Git.
- Connected the project repository and pushed it to GitHub.
- Selected a better product review dataset.
- Inspected dataset columns.
- Chose `Equal.csv` because it includes:
  - `ProductName`
  - `ProductPrice`
  - `Rate`
  - `Review`
  - `Summary`
  - `Sentiment`
- Created a cleaned dataset workflow:
  - Renamed columns.
  - Combined `Review` and `Summary` into `full_review`.
  - Converted rating values to numeric.
  - Cleaned the price column.
  - Saved `marketmind_clean_reviews.csv`.
- Added README and data documentation cleanup.

### Errors / issues faced

- Faced a `UnicodeDecodeError` while reading the CSV file.

### How I fixed them

- Fixed the CSV reading issue by using:
  - `encoding="latin1"`
  - `low_memory=False`

### Output generated

- Cleaned dataset workflow created.
- `marketmind_clean_reviews.csv` generated.
- README and data documentation cleanup completed.

### Git commit made

- Project setup, dataset exploration, and documentation updates were committed and pushed to GitHub.

### Next step

- Start Phase 2: Text preprocessing.

## Day 2

### Date

Day 2

### Phase

Phase 2: Text preprocessing.

### What I learned

- Learned that missing-looking values can appear as text, such as `"Nan"`, and need explicit cleanup.
- Learned that final validation before saving is important for reliable processed datasets.

### What I implemented

- Implemented the data preprocessing pipeline in `src/data_preprocessing.py`.
- Added reusable functions for loading raw data, standardizing columns, creating `full_review`, cleaning price/rating columns, cleaning review text, and saving the processed dataset.
- Generated `data/processed/marketmind_clean_reviews.csv` locally.

### Errors / issues faced

- After running the preprocessing script, `cleaned_review` still had 1 missing value.
- The problematic row had `full_review = "Nan"` and `cleaned_review = NaN`.

### How I fixed them

- Updated the final cleanup step to strip `full_review` and `cleaned_review`.
- Treated `""`, `"nan"`, `"none"`, and `"null"` as invalid text values.
- Replaced invalid values with `pd.NA`.
- Dropped rows missing `product_name`, `rating`, `full_review`, `cleaned_review`, or `sentiment` before saving.

### Output generated

- Final processed dataset should contain these columns:
  - `product_name`
  - `clean_price`
  - `rating`
  - `full_review`
  - `cleaned_review`
  - `sentiment`
- `cleaned_review` should have 0 missing values after rerunning the script.

### Git commit made

- To be completed.

### Next step

- Continue Phase 2 by preparing the cleaned text data for later sentiment modeling.
