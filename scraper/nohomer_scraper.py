"""
Scraper for NoHomers.net episode reviews.
Scrapes episode review links and per-episode reviewer ratings.
Outputs are saved to scraper/tmp/.
"""

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
        episode_reviews_dir: str = "./scraper/tmp/episodes_reviews/",
        episode_links_csv_path: str = "./scraper/tmp/episodes_reviews_links.csv",
        warnings_dir: str = "./scraper/tmp/warnings_reviews/",
    ) -> None:
        self.episode_reviews_dir = episode_reviews_dir
        self.episode_links_csv_path = episode_links_csv_path
        self.warnings_dir = warnings_dir
        self.scrape_timestamp = time.strftime("%Y%m%d_%H%M")
        self.warnings_csv_path = os.path.join(self.warnings_dir, f"{self.scrape_timestamp}.csv")

    def add_warning(self, warnings: list, episode_name: str, 
                    url: str, warning_type: str, detail: str = None) -> None:
        """Adds a warning row using a normalized schema."""
        warnings.append(
            {
                "scrape_time": self.scrape_timestamp,
                "episode_name": episode_name,
                "url": url,
                "warning_type": warning_type,
                "detail": detail,
            }
        )

    def parse_episode_links_from_html(self, html_text: str) -> list:
        """Parses episode names and URLs from the main NoHomers forum HTML."""
        soup = BeautifulSoup(html_text, "html.parser")
        first_post = soup.find("article", {"id": "js-post-172093"})
        if first_post is None:
            return []

        episode_link_tags = first_post.find_all("a", class_="link link--internal")

        results = []
        for episode_link in episode_link_tags:
            episode_url = episode_link.get("href")
            episode_name = episode_link.text.strip()
            if episode_url and episode_name:
                results.append((episode_name, episode_url))

        return results

    def scrape_episode_links(self) -> None:
        try:
            response = requests.get(self.BASE_URL, timeout=20)
        except requests.RequestException as error:
            print(f"Error fetching episode review links: {error}")
            return

        if response.status_code != 200:
            print(f"Error fetching episode review links: HTTP {response.status_code}")
            return

        results = self.parse_episode_links_from_html(response.text)
       
        print(f"Total episodes found: {len(results)}")
        self.episode_links_df = pd.DataFrame(results, columns=["episode_name", "episode_url"])
        os.makedirs(os.path.dirname(self.episode_links_csv_path), exist_ok=True)
        self.episode_links_df.to_csv(self.episode_links_csv_path, index=False, sep="|")


    def scrape_rating_reviewers(self, url: str, rating_text: int):
        """Scrapes reviewers for a given hidden rating URL."""
        try:
            response = requests.get(url, timeout=20)
        except requests.RequestException as error:
            return [], str(error)

        if response.status_code != 200:
            return [], f"HTTP {response.status_code}"

        soup = BeautifulSoup(response.text, "html.parser")
        reviewers = soup.find_all("a", {"class": "username"})

        results = []
        for reviewer in reviewers:
            user_id = reviewer["data-user-id"]
            username = reviewer.text.strip()
            user_url = "https://nohomers.net" + reviewer["href"]
            results.append((rating_text, user_id, username, user_url))

        return results, None


    def sanitize_episode_name(self, episode_name: str) -> str:
        """Sanitizes an episode name by replacing spaces, slashes, etc. with underscores."""
        unwanted_characters = [" ", "/", ":", "?", "*", '"', "<", 
                               ">", "|", ",", ".", "(", ")", "[", "]"]
        for char in unwanted_characters:
            episode_name = episode_name.replace(char, "_")
        return episode_name
    

    def summarize_scrape_warnings(self) -> None:
        """Summarizes the warnings by episode and type of warning."""
        if not os.path.isfile(self.warnings_csv_path):
            print("No warnings file found.")
            return

        warnings_df = pd.read_csv(self.warnings_csv_path, sep="|")

        summary_df = (
            warnings_df.groupby("warning_type", dropna=False)["episode_name"]
            .nunique()
            .reset_index(name="episodes_count")
            .sort_values("episodes_count", ascending=False)
        )
        
        print("\nScrape Warnings Summary:")
        for _, row in summary_df.iterrows():
            print(f"---{int(row['episodes_count'])} episodes with {row['warning_type']}")


    def delete_episode_files_with_retryable_warnings(self) -> None:
        '''Episodes with selected warnings are deleted to allow a new scraping attempt 
        in the next run (e.g., those with request errors).'''

        warning_types_to_retry = ["request_error_url", "request_error_rating_url"]

        warnings_df = pd.read_csv(self.warnings_csv_path, sep="|")
        episode_names = warnings_df[
            warnings_df.warning_type.isin(warning_types_to_retry)
            ].episode_name.unique()

        for episode_name in episode_names:
            sanitized_episode_name = self.sanitize_episode_name(episode_name)
            episode_file_path = f"{self.episode_reviews_dir}{sanitized_episode_name}.csv"
            if os.path.isfile(episode_file_path):
                os.remove(episode_file_path)
                print(f"Deleted scraped reviews file for episode '{episode_name}' due to warnings.")
        

    def scrape_episode_reviews(self, skip_existing_episodes: bool = False) -> None:

        warnings = []
        episode_links_df = pd.read_csv(self.episode_links_csv_path, sep="|")
        total_episodes = len(episode_links_df)


        for i, episode_link in episode_links_df.iterrows():
            episode_name, url = episode_link
            sanitized_episode_name = self.sanitize_episode_name(episode_name)
            
            if skip_existing_episodes and os.path.exists(
                f"{self.episode_reviews_dir}{sanitized_episode_name}.csv"
            ):
                print(
                    f"Skipping episode {i + 1}/{total_episodes}: {episode_name:<120}",
                    end="\r"
                )
                continue

            print(
                f"Scraping episode {i + 1}/{total_episodes}: {episode_name:<120}",
                end="\r"
            )
            time.sleep(random.uniform(1, 3))

            try:
                response = requests.get(url, timeout=20)
            except requests.RequestException as error:
                self.add_warning(warnings, episode_name, url, "request_error_url", detail=str(error))
                time.sleep(random.uniform(1, 3))
                continue

            if response.status_code != 200:
                self.add_warning(warnings, episode_name, url, "request_error_url", 
                                 detail=f"HTTP {response.status_code}")
                print(f"--- Error fetching episode reviews: HTTP {response.status_code}")
                time.sleep(random.uniform(1, 3))
                continue

            # The reviews are on a table. Each one at a different row.
            soup = BeautifulSoup(response.text, "html.parser")
            reviews_table = soup.find("ul", {"class": "listPlain"})

            episode_reviews = []
            for review in reviews_table.find_all("li"):

                rating_text = review.text.strip().split()[0]

                # The reviewers are on a hidden link that needs to be scraped (if accesible)
                reviewers_panel  = review.find("div", {"class": "pollResult-voters"})
                if reviewers_panel  is None:
                    self.add_warning(warnings, episode_name, url, "missing_reviewer_info")
                    continue

                rating_reviewers_url = "https://nohomers.net" + reviewers_panel["data-href"]
                rating_reviewers, request_error = self.scrape_rating_reviewers(rating_reviewers_url, rating_text)

                if request_error is not None:
                    self.add_warning(
                        warnings,
                        episode_name,
                        rating_reviewers_url,
                        "request_error_rating_url",
                        detail=request_error,
                    )
                    time.sleep(random.uniform(1, 3))
                    continue

                episode_reviews.extend(rating_reviewers)


            episode_reviews_df = pd.DataFrame(
                episode_reviews,
                columns=["rating_text", "user_id", "username", "user_url"],
            )

            episode_reviews_df["episode_name"] = episode_name
            os.makedirs(self.episode_reviews_dir, exist_ok=True)
            episode_reviews_df.to_csv(
                f"{self.episode_reviews_dir}{sanitized_episode_name}.csv",
                index=False,
                sep="|",
            )
                
        warnings_df = pd.DataFrame(warnings)
        os.makedirs(self.warnings_dir, exist_ok=True)
        warnings_df.to_csv(self.warnings_csv_path, index=False, sep="|")


if __name__ == "__main__":
    scraper = NoHomerScraper()
    scraper.scrape_episode_links()
    scraper.scrape_episode_reviews(skip_existing_episodes=True)
    scraper.summarize_scrape_warnings()
    scraper.delete_episode_files_with_retryable_warnings()