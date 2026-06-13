# MarketMind

MarketMind is an ML-powered product launch feedback simulator. The project is being built to analyze real customer product reviews, identify sentiment and complaints, generate customer personas, score product launch readiness, and later provide real-time AI feedback from virtual customer personas.

This project is currently in progress. Real-time AI persona feedback is planned for a later phase and is not implemented yet.

## Current Status

- Phase 0: Complete
- Phase 1: Dataset exploration and preprocessing workflow in progress
- Phase 2: Not started

## Planned Features

- Sentiment analysis
- Complaint mining
- Customer persona generation
- Launch scoring
- Streamlit dashboard
- Live AI customer panel

## Dataset Schema

The selected dataset is a product review dataset. Large dataset files are stored locally and are not pushed to GitHub.

Raw dataset columns:

- `ProductName`
- `ProductPrice`
- `Rate`
- `Review`
- `Summary`
- `Sentiment`

Cleaned dataset columns:

- `product_name`
- `clean_price`
- `rating`
- `full_review`
- `sentiment`

Expected local data paths:

- Raw dataset: `data/raw/Equal.csv`
- Processed dataset: `data/processed/marketmind_clean_reviews.csv`

## Folder Structure

```text
MarketMind/
|-- app/
|   `-- streamlit_app.py
|-- data/
|   |-- raw/
|   `-- processed/
|-- models/
|-- notebooks/
|   `-- 01_data_exploration.ipynb
|-- reports/
|-- src/
|   |-- data_preprocessing.py
|   |-- sentiment_model.py
|   |-- complaint_miner.py
|   |-- persona_generator.py
|   `-- scoring_engine.py
|-- requirements.txt
`-- README.md
```

Folder purpose:

- `app/`: Streamlit application entry point planned for later phases.
- `data/raw/`: Original downloaded datasets stored locally.
- `data/processed/`: Cleaned datasets created during preprocessing.
- `models/`: Trained model artifacts planned for later phases.
- `notebooks/`: Dataset exploration and experimentation notebooks.
- `reports/`: Future analysis outputs, charts, and summaries.
- `src/`: Source modules for the planned ML pipeline.

Large datasets and trained models are ignored using `.gitignore` so the repository stays lightweight and GitHub-friendly.

## Tech Stack

- Python
- Pandas
- NumPy
- Scikit-learn
- Streamlit
- NLP
