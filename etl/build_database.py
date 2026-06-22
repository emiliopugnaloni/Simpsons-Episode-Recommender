from etl.build_episodes import EPISODES_PATH
from etl.build_reviews import REVIEWS_PATH
from etl.build_reviewers import REVIEWERS_PATH
import pandas as pd
import sqlite3
import os


def build_database():
    """Builds the database by loading episodes, reviews, and reviewers data."""

    # Load episodes, reviews, and reviewers data
    episodes = pd.read_csv(EPISODES_PATH, sep="|")
    reviews = pd.read_csv(REVIEWS_PATH, sep="|")
    reviewers = pd.read_csv(REVIEWERS_PATH, sep="|")

    # Create a SQLite database and store the data
    os.makedirs("data", exist_ok=True)
        
    with sqlite3.connect("data/simpsons.db") as conn:
        episodes.to_sql("episodes", conn, if_exists="replace", index=False)
        reviews.to_sql("reviews", conn, if_exists="replace", index=False)
        reviewers.to_sql("reviewers", conn, if_exists="replace", index=False)


if __name__ == "__main__":
    build_database()

    


