# Simpsons-Episode-Recommender

This repository is for building a Simpsons episode recommender system.

The goal of the project is to create a recommender system for Simpsons episodes, powered by data scraped from internet sources.

The scraping and data-processing layers are the foundation for a later application that will recommend episodes based on user preferences and episode information.

## Project Structure

Current and planned structure:

```text
Simpsons-Episode-Recommender/
├── .github/
│   └── workflows/
│       └── ci.yaml
├── tests/
├── scraper/
│   ├── nohomer_scraper.py
│   ├── wikisimpsons_scraper.py
├── etl/
│   ├── build_users.py
│   ├── build_episodes.py
│   ├── build_ratings.py
│   ├── build_database.py
│   └── run_pipeline.py
└── README.md
```

Notes:

1. `scraper/` contains source-specific scraping code.
2. `scraper/nohomer_scraper.py` is the current scraper for NoHomers episode reviews.
3. `scraper/wikisimpsons_scraper.py` is the planned scraper for episode metadata from WikiSimpsons.
4. `etl/` is for transforming scraped data into project datasets.
5. `tests/` contains the automated test suite.
6. `.github/workflows/ci.yaml` defines the CI pipeline for pull requests.

## Scraper Layer

The scraper layer is responsible for collecting raw data from external sources.

At the moment, the repository is focused on the NoHomers source:

1. scrape the page containing links to episode review pages
2. visit each episode review page
3. scrape the users who rated each episode and their rating values

The planned WikiSimpsons scraper will focus on episode metadata, such as episode names, seasons, production information, and other descriptive attributes needed for the final `episodes.csv` table.

## How The Scraper Is Run

The current scraper is designed to be run directly as a Python script.

From the project root:

```bash
python scraper\nohomer_scraper.py
```

What this does:

1. scrapes the NoHomers episode review links
2. scrapes the review data for each episode
3. saves intermediate outputs used later by the ETL step
4. writes warnings that help identify scraping issues

The scraper currently uses a `main` block at the bottom of the file, so it can be run directly without needing a separate runner file.

## ETL Layer

The ETL layer is responsible for transforming scraped data into the datasets needed by the recommender system and for creating the database used later by the application.

Planned ETL scripts:

1. `build_users.py`
2. `build_episodes.py`
3. `build_ratings.py`
4. `build_database.py`
5. `run_pipeline.py`

`run_pipeline.py` will be useful as a single entrypoint for running the ETL steps in sequence.

## Current Status

Current implementation:

1. `scraper/nohomer_scraper.py` exists and is the active source scraper

Planned next steps:

1. add `scraper/wikisimpsons_scraper.py`
2. create the `etl/` scripts
3. generate the final recommender-system datasets
4. create the SQL database from those outputs

