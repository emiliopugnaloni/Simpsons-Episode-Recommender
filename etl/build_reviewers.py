"""
Code to build the users table from the scraped reviews data.
It extracts the unique users
"""

import os
import pandas as pd


def build_reviewers_table(
    scraped_episode_reviews_dir: str, reviewers_path: str
) -> None:
    """Builds the reviewers table from the scraped reviews data."""

    # List all reviews and load them into a dataframe
    review_files = [
        os.path.join(scraped_episode_reviews_dir, f)
        for f in os.listdir(scraped_episode_reviews_dir)
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
    os.makedirs(os.path.dirname(reviewers_path), exist_ok=True)
    df_reviewers.to_csv(reviewers_path, index=False, sep="|")


if __name__ == "__main__":
    scraped_episode_reviews_dir = "./scraper/tmp/episodes_reviews"
    reviewers_path = "./etl/tmp/reviewers.csv"

    build_reviewers_table(scraped_episode_reviews_dir, reviewers_path)
