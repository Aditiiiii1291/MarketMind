# MarketMind Project Setup

This guide explains how to set up MarketMind locally for development.

## Clone The Repository

```bash
git clone https://github.com/Aditiiiii1291/MarketMind.git
cd MarketMind
```

## Create A Virtual Environment On Windows

```bash
python -m venv .venv
```

## Activate The Virtual Environment

Using PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Using Command Prompt:

```cmd
.venv\Scripts\activate.bat
```

## Install Requirements

```bash
pip install -r requirements.txt
```

## Add The Raw Dataset Locally

Place the raw product review dataset at:

```text
data/raw/Equal.csv
```

Raw and processed CSV files are intentionally ignored by Git, so this file should stay local and should not be pushed to GitHub.

## Save The Cleaned Dataset Locally

The cleaned dataset should be saved at:

```text
data/processed/marketmind_clean_reviews.csv
```

Processed CSV files are also ignored by Git.

## Open Notebooks

Start Jupyter Notebook:

```bash
jupyter notebook
```

Then open:

```text
notebooks/01_data_exploration.ipynb
```

If using VS Code, open the repository folder and select the notebook file from the `notebooks/` folder.

## Run The Future Streamlit App

The Streamlit dashboard is planned for a later phase and is not implemented yet. When it is ready, it will be run with:

```bash
streamlit run app/streamlit_app.py
```

## Git Workflow Commands

Check changed files:

```bash
git status
```

Stage changes:

```bash
git add .
```

Commit changes:

```bash
git commit -m "message"
```

Push changes:

```bash
git push
```

## Git Ignore Notes

The following types of files are intentionally ignored by Git:

- Raw CSV files in `data/raw/`
- Processed CSV files in `data/processed/`
- Trained model files in `models/`
- Virtual environments
- Python cache files
