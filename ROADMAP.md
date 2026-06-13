# MarketMind Roadmap

## Phase 0: Repository Setup

- Goal: Create a clean project structure for the MarketMind workflow.
- What will be learned: How to organize an ML project for GitHub.
- What will be implemented: Repository folders, placeholder files, `.gitignore`, and basic documentation.
- Expected output: A clean GitHub-friendly project scaffold.
- Status: Complete

## Phase 1: Dataset Exploration And Cleaning

- Goal: Understand the selected product review dataset and create a cleaned dataset.
- What will be learned: Dataset inspection, column cleanup, missing value checks, type conversion, and review text preparation.
- What will be implemented: Notebook-based exploration and a cleaned dataset workflow.
- Expected output: `data/processed/marketmind_clean_reviews.csv` created locally.
- Status: In progress

## Phase 2: Text Preprocessing

- Goal: Prepare review text for NLP and ML modeling.
- What will be learned: Text normalization, tokenization, stopword handling, and feature preparation.
- What will be implemented: Reusable preprocessing functions for `full_review`.
- Expected output: Clean text features ready for sentiment modeling.
- Status: Not started

## Phase 3: Sentiment Model Training

- Goal: Train a model to classify or predict customer sentiment from review text.
- What will be learned: Train/test splits, feature extraction, model training, evaluation metrics, and model persistence.
- What will be implemented: A sentiment model training and evaluation workflow.
- Expected output: A trained sentiment model saved locally in `models/`.
- Status: Not started

## Phase 4: Complaint Mining

- Goal: Identify recurring customer complaints and pain points from review text.
- What will be learned: Keyword extraction, topic patterns, negative review analysis, and complaint grouping.
- What will be implemented: Complaint extraction logic based on review content and sentiment signals.
- Expected output: A structured list or summary of common complaints.
- Status: Not started

## Phase 5: Customer Persona Generation

- Goal: Generate customer persona groups from review behavior and product feedback patterns.
- What will be learned: Customer segmentation, clustering ideas, feature grouping, and persona summarization.
- What will be implemented: Persona generation logic using cleaned review data and model outputs.
- Expected output: A small set of customer personas with traits, needs, and pain points.
- Status: Not started

## Phase 6: Product Launch Scoring

- Goal: Convert review insights into a product launch readiness score.
- What will be learned: Rule-based scoring, metric weighting, and combining ML outputs into decision-support signals.
- What will be implemented: Launch scoring logic using sentiment, complaints, ratings, and persona insights.
- Expected output: A launch readiness score with supporting explanation.
- Status: Not started

## Phase 7: Streamlit Dashboard

- Goal: Present MarketMind insights in an interactive dashboard.
- What will be learned: Streamlit layout, charts, file loading, and user-facing ML presentation.
- What will be implemented: A dashboard for dataset insights, sentiment results, complaints, personas, and launch scores.
- Expected output: A local Streamlit app that summarizes the MarketMind workflow.
- Status: Not started

## Phase 8: Live AI Customer Panel

- Goal: Add real-time customer-style feedback from virtual personas.
- What will be learned: Prompt design, AI response structure, persona simulation, and responsible AI limitations.
- What will be implemented: A future AI-powered customer panel after the core ML pipeline is stable.
- Expected output: A planned interactive panel where virtual personas respond to product ideas.
- Status: Not started

This phase is planned for the future and is not implemented yet.

## Phase 9: Final Polish, README Screenshots, Demo, Resume Preparation

- Goal: Prepare the project for GitHub review, demos, and resume presentation.
- What will be learned: Project storytelling, documentation polish, screenshot preparation, and portfolio positioning.
- What will be implemented: Final README updates, screenshots, demo notes, cleanup, and resume-ready explanations.
- Expected output: A polished portfolio project that clearly shows the ML workflow and final results.
- Status: Not started
