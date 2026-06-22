"""
Code to build the users table from the scraped reviews data.
It extracts the unique users
"""

import os
import pandas as pd

SCRAPED_EPISODE_REVIEWS_DIR = "./scraper/tmp/episodes_reviews"
REVIEWERS_PATH = "./etl/tmp/reviewers.csv"


def build_reviewers()-> None:
    """Builds the reviewers table from the scraped reviews data."""

    # List all reviews and load them into a dataframe
    review_files = [
        os.path.join(SCRAPED_EPISODE_REVIEWS_DIR, f)
        for f in os.listdir(SCRAPED_EPISODE_REVIEWS_DIR)
        if f.endswith(".csv")
    ]
    df_reviews = pd.concat(
        [pd.read_csv(f, sep="|") for f in review_files], ignore_index=True
    )

    # Extract the unique reviewers
    df_reviewers = (
        df_reviews[["username", "user_url"]].drop_duplicates().reset_index(drop=True)
    )

    # Save the reviewers table
    os.makedirs(os.path.dirname(REVIEWERS_PATH), exist_ok=True)
    df_reviewers.to_csv(REVIEWERS_PATH, index=False, sep="|")


if __name__ == "__main__":

    build_reviewers()
