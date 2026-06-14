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

## Day 2 Planned

### Date

Day 2

### Phase

Phase 2: Text preprocessing.

### What I learned

- To be completed after Phase 2 work begins.

### What I implemented

- Planned:
  - Move cleaning logic from the notebook into `src/data_preprocessing.py`.
  - Create reusable preprocessing functions.
  - Generate a `cleaned_review` column.
  - Save the processed dataset.

### Errors / issues faced

- To be completed.

### How I fixed them

- To be completed.

### Output generated

- Planned processed dataset output.

### Git commit made

- To be completed.

### Next step

- Begin implementing reusable text preprocessing logic in Phase 2.
