import pandas as pd
from etl.build_reviews import (
    get_episodes_with_10_scale_ratings,
    add_rating_column,
)

data = [
    {"episode_name": "Episode 1", "rating_text": "5/5"},
    {"episode_name": "Episode 2", "rating_text": "10/10"},
    {"episode_name": "Episode 3", "rating_text": "1-I"},
    {"episode_name": "Episode 4", "rating_text": "2/5:The"},
    {"episode_name": "Episode 5", "rating_text": "3/5"},
    {"episode_name": "Episode 6", "rating_text": "2/5--Survival"},
    {"episode_name": "Episode 7", "rating_text": "2/10-Below"},
    {"episode_name": "Episode 8", "rating_text": "15%"},
    {"episode_name": "Episode 9", "rating_text": "20%"},
]

df = pd.DataFrame(data)


def test_get_episodes_with_10_scale_ratings():
    episodes_with_10_scale = get_episodes_with_10_scale_ratings(df)
    assert episodes_with_10_scale == ["Episode 2", "Episode 7"]


def test_add_rating_column():
    df_with_ratings = add_rating_column(df)
    expected_ratings = [5, -1, 1, 2, 3, 2, -1, -1, -1]
    assert df_with_ratings["rating"].tolist() == expected_ratings
