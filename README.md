# MarketMind

MarketMind is a data-backed product feedback simulation and review-intelligence platform. It analyzes product reviews, mines recurring complaints, scores product health, and simulates how feedback personas may react to a new product concept.

Persona feedback in MarketMind is simulated and data-backed. It is not real customer feedback, a demand forecast, or a guarantee that a product will succeed in the market.

## Key Features

- Sentiment classification with TF-IDF and Logistic Regression
- Complaint phrase mining from negative reviews
- Complaint category mapping for business-friendly insights
- Product-specific review analysis
- Review persona segmentation using KMeans
- Data-backed persona profiles based on review behavior
- Product health scoring from ratings, sentiment, and complaints
- Product comparison and ranking by health score
- Product Concept Simulator for new product ideas
- Rule-based natural persona responses
- Streamlit dashboard for interactive analysis

## Dashboard Sections

### Product Concept Simulator

The Product Concept Simulator lets a user enter a new product concept, including name, category, price, features, and description. MarketMind retrieves similar historical review patterns using TF-IDF cosine similarity, estimates reactions from three review persona segments, and returns simulated ratings, likely concerns, buying stances, natural rule-based responses, a launch-readiness score, and recommended next actions.

### Existing Product Analyzer

The Existing Product Analyzer lets a user search for a product already present in the processed review dataset. It shows matched product names, review count, average rating, sentiment distribution, product health score, complaint category summary, and rule-based recommendations.

Product comparison is available as a backend workflow through `src/product_comparator.py`, where 2 to 5 products can be compared and ranked by health score.

## Architecture

```text
Raw Reviews
-> Data Preprocessing
-> Sentiment Model
-> Complaint Mining
-> Persona Clustering
-> Similarity Retrieval
-> Product Concept Simulation / Product Health Analysis
-> Streamlit Dashboard
```

## Technology Stack

- Python
- pandas
- scikit-learn
- TF-IDF
- Logistic Regression
- KMeans
- CountVectorizer
- cosine similarity
- Streamlit
- joblib

## ML and NLP Concepts

- Supervised sentiment classification: learns sentiment labels from cleaned review text.
- TF-IDF vectorization: converts review text into weighted numerical features.
- Logistic Regression: classifies review sentiment from TF-IDF features.
- KMeans clustering: groups reviews into feedback persona segments using rating, sentiment, and review-length signals.
- CountVectorizer bigrams: extracts common two-word complaint phrases from negative reviews.
- Cosine similarity retrieval: finds historical reviews most similar to a new product concept.
- Rule-based recommendation and response generation: creates transparent recommendations and persona replies without claiming real customer quotes.

## How It Works

### Concept Simulator Flow

1. The user enters a product concept.
2. The concept text is combined from name, category, price, features, and description.
3. A saved TF-IDF vectorizer converts the concept and historical reviews into vectors.
4. Cosine similarity retrieves the most relevant historical review patterns.
5. KMeans-based feedback personas estimate ratings, concerns, confidence, and buying stance.
6. Rule-based templates generate natural simulated persona responses.
7. MarketMind calculates a launch-readiness score and recommended next actions.

### Existing Product Analyzer Flow

1. The user searches for an existing product.
2. Matching reviews are selected from the processed dataset.
3. Sentiment distribution, review count, and average rating are calculated.
4. Negative reviews are mined for complaint bigrams.
5. Complaint phrases are mapped to categories such as Quality, Functionality, and Value for Money.
6. A transparent health score and product recommendations are generated.

## Installation and Run Instructions

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the Streamlit dashboard:

```bash
streamlit run app/streamlit_app.py
```

Useful backend commands:

```bash
python src/data_preprocessing.py
python src/sentiment_model.py
python src/complaint_miner.py
python src/persona_generator.py
python src/scoring_engine.py --product "AWC-38"
python src/product_comparator.py --product "AWC-38" --product "PRODUCT_NAME"
python src/concept_simulator.py --name "Smart Water Bottle" --category "Bottle" --price "1499" --features "temperature display, hydration reminders, USB charging" --description "A sturdy metal bottle for students and gym users with temperature display, hydration reminders, and USB charging."
```

## Example Product Concept

```text
Product name: Smart Water Bottle
Price: 1499
Features: temperature display, hydration reminders, USB charging
Description: A sturdy metal bottle for students and gym users.
```

## Results / Example Output

A previous Smart Water Bottle simulation produced a launch score around `62 / 100` with the label `Needs Refinement`.

This should be interpreted as a simulated decision-support signal based on available historical review patterns, not as a real market prediction.

## Repository Structure

```text
MarketMind/
|-- app/
|   `-- streamlit_app.py
|-- data/
|   |-- README.md
|   |-- processed/
|   `-- raw/
|-- models/
|   `-- .gitkeep
|-- notebooks/
|   `-- 01_data_exploration.ipynb
|-- reports/
|   |-- complaint_category_summary.csv
|   |-- concept_simulation.csv
|   |-- persona_profiles.csv
|   |-- product_comparison.csv
|   |-- product_health_score.csv
|   |-- review_personas.csv
|   `-- top_complaints.csv
|-- src/
|   |-- __init__.py
|   |-- complaint_miner.py
|   |-- concept_simulator.py
|   |-- data_preprocessing.py
|   |-- persona_generator.py
|   |-- product_comparator.py
|   |-- scoring_engine.py
|   `-- sentiment_model.py
|-- PRD.md
|-- PROJECT_SETUP.md
|-- ROADMAP.md
|-- requirements.txt
`-- README.md
```

## Limitations and Responsible Use

- Personas are feedback segments, not demographic identities.
- Persona replies are deterministic simulated estimates.
- Similarity matches are based only on the available review dataset.
- Scores should support decisions, not replace real market research, user interviews, surveys, or live product testing.

## Future Improvements

- More diverse product-review datasets
- Better feature extraction
- Semantic embedding retrieval
- User feedback collection
- Database and deployment
- Optional LLM-assisted wording layer while preserving data-based scores
