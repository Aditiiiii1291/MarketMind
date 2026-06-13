# MarketMind PRD

## Project Title

MarketMind

## One-Line Summary

MarketMind is an ML-powered product launch feedback simulator that uses real product reviews to help users evaluate product ideas before launch.

## Problem Statement

Product teams, founders, and learners often need early feedback before launching a product, but collecting real customer feedback can be slow, expensive, and difficult. Existing review data already contains useful signals about customer sentiment, complaints, expectations, and buying concerns, but those signals are often scattered across many reviews.

MarketMind aims to turn product review data into structured launch feedback that can support better product decisions.

## Why This Project Is Useful

MarketMind is useful because it converts raw review text into practical insights. Instead of manually reading hundreds or thousands of reviews, users can explore sentiment trends, common complaints, customer personas, and launch readiness signals in one workflow.

For a learning and portfolio project, it also demonstrates a realistic ML pipeline: dataset exploration, cleaning, text preprocessing, sentiment modeling, complaint mining, persona generation, scoring, and dashboard presentation.

## Target Users

- Students building ML and NLP portfolio projects
- Early-stage founders validating product ideas
- Product managers researching customer pain points
- Marketing teams reviewing customer sentiment
- Analysts exploring product review datasets

## Core User Flow

1. User places the raw product review dataset in the expected local folder.
2. User explores the dataset in a notebook.
3. User cleans the dataset into a consistent schema.
4. Future phases will preprocess review text for ML.
5. Future phases will analyze sentiment and complaints.
6. Future phases will generate customer personas and launch scores.
7. Future phases will display insights in a Streamlit dashboard.
8. A live AI customer panel is planned for a future phase and is not implemented yet.

## Dataset Used

The selected dataset is a product review dataset stored locally. Dataset files are not committed to GitHub because large raw and processed CSV files are intentionally ignored.

Expected local paths:

- Raw dataset: `data/raw/Equal.csv`
- Cleaned dataset: `data/processed/marketmind_clean_reviews.csv`

## Raw Dataset Schema

- `ProductName`
- `ProductPrice`
- `Rate`
- `Review`
- `Summary`
- `Sentiment`

## Cleaned Dataset Schema

- `product_name`
- `clean_price`
- `rating`
- `full_review`
- `sentiment`

## Main Planned Features

- Dataset exploration
- Text preprocessing
- Sentiment analysis
- Complaint mining
- Customer persona generation
- Product launch scoring
- Streamlit dashboard
- Live AI customer panel

The live AI customer panel is a future/planned feature and is not implemented yet.

## MVP Scope

The MVP should include:

- A clean repository structure
- Documented dataset setup
- A cleaned review dataset schema
- Text preprocessing workflow
- Basic sentiment model training and evaluation
- Initial complaint mining
- Simple launch score logic
- A basic Streamlit dashboard showing the main insights

## Out-of-Scope Features For Now

- Live AI customer panel implementation
- LLM agents
- Real-time chat with personas
- Production deployment
- User authentication
- Database integration
- Automated data scraping
- Advanced recommendation systems

## Success Criteria

- The repository is clean, documented, and easy to understand.
- The dataset schema is clearly explained without committing CSV files.
- The preprocessing workflow produces a consistent cleaned dataset.
- Future models can use `full_review`, `rating`, `clean_price`, and `sentiment`.
- The final dashboard can explain sentiment, complaints, personas, and launch readiness in a beginner-friendly way.
- The project remains honest about what is implemented versus planned.

## Risks And Limitations

- The dataset may not represent every product category or customer segment.
- Sentiment labels may contain noise or bias.
- Review text may include missing values, duplicates, short comments, or inconsistent formatting.
- Complaint mining may initially rely on simple NLP methods before becoming more advanced.
- Persona generation may oversimplify real customer behavior.
- Launch scoring should be treated as a decision-support signal, not a guaranteed business prediction.

## Future Improvements

- Improve text preprocessing and feature engineering.
- Compare multiple sentiment models.
- Add explainable complaint categories.
- Build richer customer personas.
- Add product-category-specific launch scoring.
- Add dashboard screenshots and a demo video.
- Add the live AI customer panel after the core ML pipeline is stable.
