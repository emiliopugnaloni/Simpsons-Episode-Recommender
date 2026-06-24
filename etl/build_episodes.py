import os
import json
import pandas as pd
import re

SCRAPED_EPISODE_REVIEWS_DIR = "./scraper/tmp/episodes_reviews"
SCRAPES_EPISODES_DATA_DIR = "./scraper/tmp/episodes_data"
WARNINGS_PATH = "./etl/tmp/warnings_episodes.json"
EPISODES_PATH = "./etl/tmp/episodes.csv"


def load_nohomer_episodes(scraped_episode_reviews_dir: str) -> pd.DataFrame:
    """List all reviews and load them into a dataframe with unique episode names."""

    # List all reviews and load them into a dataframe
    review_files = [
        os.path.join(scraped_episode_reviews_dir, f)
        for f in os.listdir(scraped_episode_reviews_dir)
        if f.endswith(".csv")
    ]
    df_reviews = pd.concat(
        [pd.read_csv(f, sep="|") for f in review_files], ignore_index=True
    )

    # Delete duplicated (if any)
    df_reviews = df_reviews[["episode_name"]].drop_duplicates().reset_index(drop=True)

    return df_reviews


def load_wikisimpsons_episodes(scrapes_episodes_data_dir: str) -> pd.DataFrame:
    """List all episodes data and load them into a dataframe."""

    # List all episodes data and load them into a dataframe
    episode_files = [
        os.path.join(scrapes_episodes_data_dir, f)
        for f in os.listdir(scrapes_episodes_data_dir)
        if f.endswith(".json")
    ]

    episodes = []
    for file_path in episode_files:
        with open(file_path, "r", encoding="utf-8") as file:
            episode_data = json.load(file)
            episodes.append(episode_data)

    df_episodes = (
        pd.DataFrame(episodes)
        .drop_duplicates(subset=["episode_name"])
        .reset_index(drop=True)
    )
    return df_episodes


def create_episode_key(episode_name: str) -> str:
    """Create a key for the episode name by applying parsing rules."""

    # Characters to be deleted
    chars_to_delete = [
        " ",  ",", ":", "-", "(",
        ")",  ".", "'", '"', "&",
        "!",  "?", "¡", "-",  "*",
    ]

    # Cahracters that need to be replaced
    replace_chars = {
        " & ": " AND ",
        " 3 ": "THREE",
        "DREAMS": "DREAM",
        "HELLFISH": "HELFISH",
    }

    # Mapping for KEYS that couldn't be parsed with the above rules
    episode_mapping = {
        "ASERIOUSFLANDERSPART1": "ASERIOUSFLANDERS",
        "ATOTALLYFUNTHINGBARTWILLNEVERDOAGAIN": "ATOTALLYFUNTHINGTHATBARTWILLNEVERDOAGAIN",
        "EIEIANNOYEDGRUNT": "EIEIDOH",
        "NEDNEDNASBLENDAGENDA": "NEDNEDNASBLEND",
        "THEGREATPHATSBYPARTONE": "THEGREATPHATSBY",
        "WARRINPRIESTSPARTONE": "WARRINPRIESTS",
        "THEHOMEROFSEVILLE": "HOMEROFSEVILLE",
        "THEBONFIREOFTHEMANATEES": "BONFIREOFTHEMANATEES",
        "HOMЯ": "HOMR",
        "KILLGILVOLUMESIANDII": "KILLGILVOLUMES1AND2",
    }

    key = episode_name.upper().strip()
    for char in replace_chars:
        key = key.replace(char, replace_chars[char])
    for char in chars_to_delete:
        key = key.replace(char, "")
    if key in episode_mapping:
        return episode_mapping[key]

    return key


def merge_episodes(
    nohomer_episodes: pd.DataFrame, wiki_episodes: pd.DataFrame
) -> pd.DataFrame:
    """Merge no-homer episodes with wiki episodes based on the episode key."""

    episodes_data = nohomer_episodes.merge(
        wiki_episodes.drop(columns=["episode_name"], axis=1),
        on="EP_KEY",
        how="left",
        validate="one_to_one",
        indicator=True,
    )
    return episodes_data


def get_not_merged_episodes(episodes_data: pd.DataFrame) -> list:
    """Get episodes that could not be merged. These are episodes
    that are in the no-homer dataset but not in the wiki dataset.
    """
    not_merged = episodes_data.loc[
        episodes_data["_merge"] == "left_only", "episode_name"
    ].tolist()
    return not_merged


def clean_column_names(episodes_data: pd.DataFrame) -> pd.DataFrame:
    """Change column names to lower case and remove special characters."""

    new_colnames = (
        episodes_data.columns.str.lower()
        .str.replace(":", "")
        .str.replace(" ", "_")
        .tolist()
    )
    episodes_data.columns = new_colnames
    return episodes_data


def _join_showrunners(row):
    """Join showrunner, showrunners and co-showrunner columns into a
    single list of showrunners"""

    showrunners = []
    for col in ["showrunner", "showrunners", "co-showrunner"]:
        if isinstance(row[col], list):  # they could be nan...
            showrunners.extend(row[col])
        elif isinstance(row[col], str) and row[col].strip():
            showrunners.append(row[col].strip())
    return showrunners


def _extract_season_number(row):
    """The season number is on the column"season number" but
    as "[S11]", "[S9]", ["D+"] (for Disney+). We need to extract the number using regex"""

    value = row.get("season_number")[0]
    if value == "D+":
        return value
    else:
        match = re.search(r"S(\d+)", value)
        return match.group(1) if match else None

def _extract_first_value_from_list(value):
    """Extract the first value from a list if the value is a list, otherwise return the value itself."""
    if isinstance(value, list):
        return value[0]
    return value


def clean_episode_data(episodes_data: pd.DataFrame) -> pd.DataFrame:
    """Clean episode data by joining showrunners and extracting season number."""

    episodes_data["show_runners"] = episodes_data.apply(_join_showrunners, axis=1)
    episodes_data["season"] = episodes_data.apply(_extract_season_number, axis=1)
    episodes_data["episode_number"] = episodes_data["episode_number"].apply(_extract_first_value_from_list)
    episodes_data["original_airdate"] = episodes_data["original_airdate"].apply(_extract_first_value_from_list)

    return episodes_data


def compute_writer_dummies(episodes_data, min_presence=10):
    """Compute dummies for writers that are present in at least min_presence episodes."""

    # The writer column is a list. We need to explode it and count
    writer_counts = episodes_data.explode("written_by")["written_by"].value_counts()

    # Only writers that are present in at least min_presence episodes
    freq_writers = writer_counts[writer_counts >= min_presence].index

    # Create dummies for these writers
    for writer in freq_writers:
        writer_col = f"written_by_{writer.lower().replace(' ', '_')}"
        episodes_data[writer_col] = episodes_data["written_by"].apply(
            lambda x: 1 if isinstance(x, list) and writer in x else 0
        )

    return episodes_data


def compute_showrunner_dummies(episodes_data, min_presence=10):
    """Compute dummies for showrunners that are present in at least min_presence episodes."""

    # The showrunner column is a list. We need to explode it and count
    showrunner_counts = episodes_data.explode("show_runners")[
        "show_runners"
    ].value_counts()

    # Only showrunners that are present in at least min_presence episodes
    freq_showrunners = showrunner_counts[showrunner_counts >= min_presence].index

    # Create dummies for these showrunners
    for showrunner in freq_showrunners:
        showrunner_col = f"showrunner_{showrunner.lower().replace(' ', '_')}"
        episodes_data[showrunner_col] = episodes_data["show_runners"].apply(
            lambda x: 1 if isinstance(x, list) and showrunner in x else 0
        )

    return episodes_data


def select_relevant_columns(episodes_data: pd.DataFrame) -> pd.DataFrame:
    """Select relevant columns for the final dataset."""

    cols = [
        "episode_name",
        "main_image_url",
        "season",
        "episode_number",
        "original_airdate",
        "written_by",
        "synopsis",
        "show_runners",
    ]

    showrunners_cols = [
        col for col in episodes_data.columns if col.startswith("showrunner_")
    ]
    writers_cols = [
        col for col in episodes_data.columns if col.startswith("written_by_")
    ]

    selected_cols = cols + showrunners_cols + writers_cols

    return episodes_data[selected_cols]


def save_json(data, path):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


def save_csv(data, path):
    data.to_csv(path, index=False, sep="|")


def build_episodes():

    warnings = []
    nohomer_episodes = load_nohomer_episodes(SCRAPED_EPISODE_REVIEWS_DIR)
    wikisimpsons_episodes = load_wikisimpsons_episodes(SCRAPES_EPISODES_DATA_DIR)
    nohomer_episodes["EP_KEY"] = nohomer_episodes["episode_name"].apply(
        create_episode_key
    )
    wikisimpsons_episodes["EP_KEY"] = wikisimpsons_episodes["episode_name"].apply(
        create_episode_key
    )
    episodes_data = merge_episodes(nohomer_episodes, wikisimpsons_episodes)
    not_merged_episodes = get_not_merged_episodes(episodes_data)

    if not_merged_episodes:
        print(
            f"Warning: {len(not_merged_episodes)} no-homer episodes could not be merged"
        )
        warnings["episodes_not_merged"] = not_merged_episodes

    episodes_data = clean_column_names(episodes_data)
    episodes_data = clean_episode_data(episodes_data)
    episodes_data = compute_writer_dummies(episodes_data, min_presence=10)
    episodes_data = compute_showrunner_dummies(episodes_data, min_presence=10)
    episodes_data = select_relevant_columns(episodes_data)
    save_json(warnings, WARNINGS_PATH)
    save_csv(episodes_data, EPISODES_PATH)


if __name__ == "__main__":
    build_episodes()
