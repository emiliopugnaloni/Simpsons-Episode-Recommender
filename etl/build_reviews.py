import os
import re
import pandas as pd
import json


SCRAPED_EPISODE_REVIEWS_DIR = "./scraper/tmp/episodes_reviews"
REVIEWS_PATH = "./etl/tmp/reviews.csv"
WARNINGS_PATH = "./etl/tmp/warnings_reviews.json"


def load_reviews(scraped_episode_reviews_dir):

    # List all reviews and load them into a dataframe
    review_files = [
        os.path.join(scraped_episode_reviews_dir, f) 
        for f in os.listdir(scraped_episode_reviews_dir) if f.endswith(".csv")
        ]
    df_reviews = pd.concat(
        [pd.read_csv(f, sep="|") for f in review_files],
        ignore_index=True
    )

    df_reviews = df_reviews[['username', 'episode_name', 'rating_text']]

    return df_reviews


def get_episodes_with_10_scale_ratings(df_reviews):

    # Get episodes with 10 scale ratings
    mask_10_scale = (
        df_reviews["rating_text"]
        .astype("string")
        .str.contains("10", na=False)
    )

    episodes_with_10_scale = (
        df_reviews.loc[mask_10_scale, "episode_name"]
        .drop_duplicates()
        .to_list()
    )
    return episodes_with_10_scale


def filter_episodes_with_10_scale_ratings(df_reviews, episodes_with_10_scale):

    # Filter episodes with 10 scale ratings
    df_reviews = df_reviews[
        ~df_reviews["episode_name"].isin(episodes_with_10_scale)
    ].reset_index(drop=True)

    return df_reviews


def parse_rating_text(x):
    '''Parse rating text to a number between 1 and 5. If it cannot be parsed, return -1.'''
    t = str(x).upper().strip().replace(",","").lstrip('("')

    dict_parsing = {
        1: {'startswith': ["1/5", "I/V", "1-", "0/5", "F", "D-","D+"], 'equals': ["1", "D"]},
        2: {'startswith': ["2/5", "II/V", "2-", "C+", "C-"], 'equals': ["2", "C"]},
        3: {'startswith': ["3/5", "III/V", "3-", "B-", "B+"], 'equals': ["3", "B"]},
        4: {'startswith': ["4/5", "IV/V", "4-", "A-"], 'equals': ["4", "A"]},
        5: {'startswith': ["5/5", "V/V", "5-", "6/5", "A+"], 'equals': ["5"]}
    }

    for rating, conditions in dict_parsing.items():
        for eq in conditions["equals"]:
            if t == eq:
                return rating
        for sw in conditions["startswith"]:
            if t.startswith(sw):
                return rating
    return -1


def add_rating_column(df_reviews):
    """Return a copy with parsed integer rating column."""
    df_reviews = df_reviews.copy()
    df_reviews["rating"] = (
        df_reviews["rating_text"]
        .apply(parse_rating_text).astype(int)
        )
    return df_reviews


def get_episodes_with_unparsed_ratings(df_reviews):
    '''
    Get episodes with unparsed ratings (rating = -1). 
    These are episodes with rating_text that cannot be parsed to a number between 1 and 5.
    '''

    episodes_with_unparsed_ratings = (
        df_reviews.loc[df_reviews["rating"] == -1, "episode_name"]
        .drop_duplicates()
        .to_list()
    )
    return episodes_with_unparsed_ratings


def filter_episodes_with_unparsed_ratings(df_reviews, episodes_with_unparsed_ratings):
    '''
    Filter episodes with unparsed ratings. These are episodes with 
    rating_text that cannot be parsed to a number between 1 and 5.
    '''

    df_reviews = df_reviews[
        ~df_reviews["episode_name"].isin(episodes_with_unparsed_ratings)
    ].reset_index(drop=True)

    return df_reviews


def get_parsing_summary_results(df_reviews):
    '''
    Get parsing results. This is a dictionary with rating as key and a list of 
    rating_text that were parsed to that rating as value.
    '''
    rating_text_by_rating = (
        df_reviews[['rating', 'rating_text']]
        .drop_duplicates()
        .groupby('rating')["rating_text"]
        .agg(list)
        .to_dict()
    )
    return rating_text_by_rating


def save_json(data, path):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


def save_csv(data, path):
    data.to_csv(path, index=False, sep="|")


def build_reviews():
    warnings = {}
    df_reviews = load_reviews(SCRAPED_EPISODE_REVIEWS_DIR)
    episodes_with_10_scale = get_episodes_with_10_scale_ratings(df_reviews)
    warnings.update({"episodes_with_10_scale": episodes_with_10_scale})
    df_reviews = filter_episodes_with_10_scale_ratings(df_reviews, episodes_with_10_scale)
    df_reviews = add_rating_column(df_reviews)
    episodes_with_unparsed_ratings = get_episodes_with_unparsed_ratings(df_reviews)
    warnings.update({"episodes_with_unparsed_ratings": episodes_with_unparsed_ratings})
    df_reviews = filter_episodes_with_unparsed_ratings(df_reviews, episodes_with_unparsed_ratings)
    rating_text_by_rating = get_parsing_summary_results(df_reviews)
    warnings.update({"rating_text_by_rating": rating_text_by_rating})
    save_json(warnings, WARNINGS_PATH)
    save_csv(df_reviews, REVIEWS_PATH)


if __name__ == "__main__":
    build_reviews()

