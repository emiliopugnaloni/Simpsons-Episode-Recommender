from etl.build_episodes import build_episodes
from etl.build_reviews import build_reviews
from etl.build_reviewers import build_reviewers
from etl.build_database import build_database

if __name__ == "__main__":
    build_episodes()
    build_reviews()
    build_reviewers()
    build_database()



