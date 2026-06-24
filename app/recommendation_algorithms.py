from app.recommender_db import sql_select


def top8_recommendation_by_rating(username):
    """Retrieve 8 unseen episodes with +50 reviews by highest average rating."""
    query = """
        SELECT episode_name, AVG(rating) as rating, count(*) AS count
        FROM reviews
        WHERE episode_name NOT IN (
            SELECT episode_name
            FROM reviews
            WHERE username = ?)
        AND rating > 0
        GROUP BY 1
        HAVING count > 50
        ORDER BY 2 DESC, 3 DESC
        LIMIT 8
    """
    episode_names = [r["episode_name"] for r in sql_select(query, (username,))]
    return episode_names


def top8_recommendation_by_count(username):
    """Retrieve 8 unseen episodes by highest count of reviews with rating > 3."""
    query = """
        SELECT episode_name, count(*) AS count
        FROM reviews
        WHERE episode_name NOT IN (
            SELECT episode_name
            FROM reviews
            WHERE username = ?)
        AND rating > 3
        GROUP BY 1
        ORDER BY 2 DESC
        LIMIT 8
    """
    episode_names = [r["episode_name"] for r in sql_select(query, (username,))]
    return episode_names


def top8_recommendation(username, by="rating"):
    """Retrieve top 8 recommended episodes for a user."""
    if by == "rating":
        return top8_recommendation_by_rating(username)
    if by == "count":
        return top8_recommendation_by_count(username)
    raise ValueError("Invalid 'by' parameter. Must be 'rating' or 'count'.")
