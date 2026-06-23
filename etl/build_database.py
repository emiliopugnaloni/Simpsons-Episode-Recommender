from etl.build_episodes import EPISODES_PATH
from etl.build_reviews import REVIEWS_PATH
from etl.build_reviewers import REVIEWERS_PATH
import pandas as pd
import sqlite3
import os


def get_create_table_query(df, table_name, primary_keys: list):
    dtype_map = {
        "object": "TEXT",
        "int64": "INTEGER",
        "float64": "REAL",
        "bool": "INTEGER"
    }

    cols = []
    
    # Column: Type
    for col, dtype in df.dtypes.items():
        sqlite_type = dtype_map.get(str(dtype), "TEXT")
        cols.append(f'"{col}" {sqlite_type}')

    # Primary Key Clause
    pk_clause = ""
    if primary_keys:
        pk_clause = f", PRIMARY KEY ({', '.join(primary_keys)})"

    return f"""
    CREATE TABLE {table_name} (
        {', '.join(cols)}
        {pk_clause}
    );
    """


def build_database():
    """Builds the database by loading episodes, reviews, and reviewers data."""

    # Load episodes, reviews, and reviewers data
    episodes = pd.read_csv(EPISODES_PATH, sep="|")
    reviews = pd.read_csv(REVIEWS_PATH, sep="|").drop(columns=["rating_text"])
    reviewers = pd.read_csv(REVIEWERS_PATH, sep="|").drop(columns=["user_url"])

    # Create a SQLite database and store the data
    os.makedirs("data", exist_ok=True)

    # Get the create table queries for each DataFrame
    episodes_create_query = get_create_table_query(episodes, "episodes", ["episode_name"])
    reviews_create_query = get_create_table_query(reviews, "reviews", ["username", "episode_name"])
    reviewers_create_query = get_create_table_query(reviewers, "reviewers", ["username"])

        
    with sqlite3.connect("data/simpsons.db") as conn:

        # Drop existing tables if they exist
        conn.execute("DROP TABLE IF EXISTS reviews")
        conn.execute("DROP TABLE IF EXISTS reviewers")
        conn.execute("DROP TABLE IF EXISTS episodes")

        # Create tables
        conn.execute(episodes_create_query)
        conn.execute(reviews_create_query)
        conn.execute(reviewers_create_query)

        # Insert data into tables
        episodes.to_sql("episodes", conn, if_exists="append", index=False)
        reviews.to_sql("reviews", conn, if_exists="append", index=False)
        reviewers.to_sql("reviewers", conn, if_exists="append", index=False)


if __name__ == "__main__":
    build_database()

    


