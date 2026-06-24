import sqlite3
from pathlib import Path

REPO_FOLDER = Path("__file__").resolve().parent.parent
DATABASE_PATH = REPO_FOLDER / "data" / "simpsons_clone.db"


def sql_execute(query, params=None):
    """Execute a SQL query with optional parameters and commit the changes to the database.

    Args:
        query (str): The SQL query to execute.
        params (tuple, optional): Parameters to pass to the SQL query. Defaults to None.
    """
    con = sqlite3.connect(DATABASE_PATH)
    cur = con.cursor()
    if params:
        cur.execute(query, params)
    else:
        cur.execute(query)

    con.commit()
    con.close()


def sql_select(query, params=None):
    """Execute a SQL SELECT query with optional parameters.

    Args:
        query (str): The SQL SELECT query to execute.
        params (tuple, optional): Parameters to pass to the SQL query. Defaults to None.

    Returns:
        list: Rows returned by the query as sqlite3.Row objects.
    """
    con = sqlite3.connect(DATABASE_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    if params:
        res = cur.execute(query, params)
    else:
        res = cur.execute(query)

    ret = res.fetchall()
    con.close()
    return ret


def create_user(username):
    """Create a new user in the reviewers table if it does not already exist."""
    query = "INSERT INTO reviewers(username) VALUES (?) ON CONFLICT DO NOTHING;"
    sql_execute(query, (username,))


def insert_reviews(username, episode_name, rating):
    """Insert or update a user rating for an episode."""
    query = (
        "INSERT INTO reviews(username, episode_name, rating) VALUES (?, ?, ?) "
        "ON CONFLICT (username, episode_name) DO UPDATE SET rating=?;"
    )
    sql_execute(query, (username, episode_name, rating, rating))


def reset_user(username):
    """Delete all reviews for a user."""
    query = "DELETE FROM reviews WHERE username = ?;"
    sql_execute(query, (username,))


def get_episode(episode_name):
    """Retrieve one episode by name."""
    query = "SELECT * FROM episodes WHERE episode_name = ?;"
    episode = sql_select(query, (episode_name,))[0]
    return episode


def get_reviews(username):
    """Retrieve all rated episodes (rating > 0) for a user."""
    query = "SELECT * FROM reviews WHERE username = ? AND rating > 0"
    reviews = sql_select(query, (username,))
    return reviews


def get_ignored_episodes(username):
    """Retrieve all ignored episodes (rating = 0) for a user."""
    query = "SELECT * FROM reviews WHERE username = ? AND rating = 0"
    ignored_episodes = sql_select(query, (username,))
    return ignored_episodes
