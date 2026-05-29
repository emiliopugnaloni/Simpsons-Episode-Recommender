import os
import random
import time

import pandas as pd
import requests
from bs4 import BeautifulSoup


class NoHomerScraper:
    BASE_URL = "https://nohomers.net/forums/index.php?threads/rate-review-for-all-episodes-go-here-to-rate-review-any-episode.10558/"

    def __init__(
        self,
        dir_scraped_episode_reviews_folder: str = "./scraper/tmp/episodes_reviews/",
        dir_scraped_url_episodes_reviews: str = "./scraper/tmp/episodes_reviews_links.csv",
        dir_scraping_warnings: str = "./scraper/tmp/warnings_reviews.csv",
    ) -> None:
        self.dir_scraped_episode_reviews_folder = dir_scraped_episode_reviews_folder
        self.dir_scraped_url_episodes_reviews = dir_scraped_url_episodes_reviews
        self.dir_scraping_warnings = dir_scraping_warnings

    def scrape_episode_reviews_links(self) -> None:
        response = requests.get(self.BASE_URL)
        soup = BeautifulSoup(response.text, "html.parser")
        first_post = soup.find("article", {"id": "js-post-172093"})
        first_post_links = first_post.find_all("a", class_="link link--internal")

        results = []
        for first_post_link in first_post_links:
            episode_link = first_post_link.get("href")
            episode_name = first_post_link.text.strip()
            results.append((episode_name, episode_link))

        print(f"Total episodes found: {len(results)}")
        df = pd.DataFrame(results, columns=["episode_name", "episode_link"])
        os.makedirs(os.path.dirname(self.dir_scraped_url_episodes_reviews), exist_ok=True)
        df.to_csv(self.dir_scraped_url_episodes_reviews, index=False, sep="|")

    def find_rating_number(self, rating_text: str):
        """Converts a rating text into a numerical rating."""
        if ("5/5" in rating_text) | ("V/V" in rating_text) | (rating_text.startswith("5")):
            rating_number = 5
        elif ("4/5" in rating_text) | ("IV/V" in rating_text) | (rating_text.startswith("4")):
            rating_number = 4
        elif ("3/5" in rating_text) | ("III/V" in rating_text) | (rating_text.startswith("3")):
            rating_number = 3
        elif ("2/5" in rating_text) | ("II/V" in rating_text) | (rating_text.startswith("2")):
            rating_number = 2
        elif ("1/5" in rating_text) | ("I/V" in rating_text) | (rating_text.startswith("1")):
            rating_number = 1
        elif rating_text.startswith("10"):
            rating_number = 10
        else:
            rating_number = None

        return rating_number

    def scrape_rating_reviewers(self, url: str, rating_number: int) -> list:
        """Scrapes reviewers for a given hidden rating URL."""
        r = requests.get(url)
        soup = BeautifulSoup(r.text, "html.parser")
        reviewers = soup.find_all("a", {"class": "username"})

        rating_reviewers_results = []
        for reviewer in reviewers:
            user_id = reviewer["data-user-id"]
            username = reviewer.text.strip()
            user_url = "https://nohomers.net" + reviewer["href"]
            rating_reviewers_results.append((rating_number, user_id, username, user_url))

        return rating_reviewers_results

    def sanitize_episode_name(self, episode_name: str) -> str:
        """Sanitizes an episode name by replacing spaces, slashes, etc. with underscores."""
        unwanted_characters = [" ", "/", ":", "?", "*", '"', "<", ">", "|", ",", ".", "(", ")", "[", "]"]
        for char in unwanted_characters:
            episode_name = episode_name.replace(char, "_")
        return episode_name

    def summarize_scrape_reviews_warnings(self) -> None:
        """Summarizes the warnings by episode and type of warning."""
        warnings_df = pd.read_csv(self.dir_scraping_warnings, sep="|")

        for warning_type in ["unrecognized_rating_text", "missing_reviewers_info_for_rating"]:
            if warning_type not in warnings_df.columns:
                print(f"Episodes with {warning_type}: []")
                continue

            episodes_list = (
                warnings_df.loc[
                    warnings_df[warning_type].notnull(),
                    "episode_name",
                ]
                .unique()
                .tolist()
            )
            print(f"Episodes with {warning_type}: {episodes_list}")

    def scrape_episode_reviews(self, filter_episodes_ratings_visited: bool = False) -> None:
        episodes_reviews_link = pd.read_csv(self.dir_scraped_url_episodes_reviews, sep="|")
        warnings_reviews = []

        for i, episode_reviews_link in episodes_reviews_link.iterrows():
            episode_name, url = episode_reviews_link
            sanitized_episode_name = self.sanitize_episode_name(episode_name)

            if filter_episodes_ratings_visited and os.path.exists(
                f"{self.dir_scraped_episode_reviews_folder}{sanitized_episode_name}.csv"
            ):
                print(
                    f"Skipping episode {i + 1}/{len(episodes_reviews_link)}: {episode_name} (already scraped)",
                    flush=True,
                )
                continue

            print(
                f"Scraping reviews for episode {i + 1}/{len(episodes_reviews_link)}: {episode_name}",
                flush=True,
            )
            time.sleep(random.uniform(0.2, 0.8))

            r = requests.get(url)
            soup = BeautifulSoup(r.text, "html.parser")
            reviews_table = soup.find("ul", {"class": "listPlain"})

            episode_reviews = []
            for review in reviews_table.find_all("li"):
                rating_text = review.text.strip().split()[0]
                rating_number = self.find_rating_number(rating_text)

                if rating_number == 10:
                    warnings_reviews.append(
                        {
                            "episode_name": episode_name,
                            "url": url,
                            "rating_text_with_10": True,
                        }
                    )
                    continue

                if rating_number is None:
                    warnings_reviews.append(
                        {
                            "episode_name": episode_name,
                            "url": url,
                            "unrecognized_rating_text": rating_text,
                        }
                    )
                    continue

                cant_reviews = review.text.strip().split()[-2]
                if cant_reviews == 0:
                    continue

                rating_reviewers_element = review.find("div", {"class": "pollResult-voters"})
                if rating_reviewers_element is None:
                    warnings_reviews.append(
                        {
                            "episode_name": episode_name,
                            "url": url,
                            "missing_reviewers_info_for_rating": rating_text,
                        }
                    )
                    continue

                rating_reviewers_url = "https://nohomers.net" + rating_reviewers_element["data-href"]
                rating_reviewers = self.scrape_rating_reviewers(rating_reviewers_url, rating_number)

                if len(rating_reviewers) != int(cant_reviews):
                    warnings_reviews.append(
                        {
                            "episode_name": episode_name,
                            "url": url,
                            "mismatched_reviews_cant": True,
                        }
                    )

                episode_reviews.extend(rating_reviewers)

            episode_reviews_df = pd.DataFrame(
                episode_reviews,
                columns=["rating_number", "user_id", "username", "user_url"],
            )
            episode_reviews_df["episode_name"] = episode_name
            os.makedirs(self.dir_scraped_episode_reviews_folder, exist_ok=True)
            episode_reviews_df.to_csv(
                f"{self.dir_scraped_episode_reviews_folder}{sanitized_episode_name}.csv",
                index=False,
                sep="|",
            )

        warnings_reviews_df = pd.DataFrame(warnings_reviews)
        os.makedirs(os.path.dirname(self.dir_scraping_warnings), exist_ok=True)
        warnings_reviews_df.to_csv(self.dir_scraping_warnings, index=False, sep="|")


if __name__ == "__main__":
    scraper = NoHomerScraper()
    scraper.scrape_episode_reviews_links()
    scraper.scrape_episode_reviews(filter_episodes_ratings_visited=True)
    scraper.summarize_scrape_reviews_warnings()
