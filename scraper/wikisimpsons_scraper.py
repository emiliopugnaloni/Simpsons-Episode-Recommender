"""
WikiSimpsons Scraper.
This module contains the WikiSimpsonScraper class, which scrapes episode
information from the WikiSimpsons website.
"""

import json
import os
import random
import time
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup


class WikiSimpsonScraper:
    def __init__(
        self,
        base_url: str = "https://simpsonswiki.com/",
        episodes_link_path: str = "./scraper/tmp/episodes_data_links_2.csv",
        episodes_data_dir: str = "./scraper/tmp/episodes_data/",
        warnings_dir: str = "./scraper/tmp/warnings_data/",
    ) -> None:
        self.base_url = base_url
        self.list_of_episodes_url = f"{self.base_url}wiki/List_of_episodes"
        self.episodes_link_path = episodes_link_path
        self.episodes_data_dir = episodes_data_dir
        self.warnings_dir = warnings_dir

        self.scrape_timestamp = time.strftime("%Y%m%d_%H%M")
        self.warnings_csv_path = os.path.join(self.warnings_dir, f"{self.scrape_timestamp}.csv")


    def add_warning(
        self,
        warnings: list,
        warning_type: str,
        detail: str = None,
    ) -> None:
        """Adds a warning row using a normalized schema."""
        warnings.append(
            {
                "scrape_time": self.scrape_timestamp,
                "episode_name": self.episode_name,
                "url": self.episode_url,
                "warning_type": warning_type,
                "detail": detail,
            }
        )


    def scrape_episodes_links(self) -> None:
        try:
            response = requests.get(self.list_of_episodes_url, timeout=20)
        except requests.RequestException as error:
            print(f"Error fetching episode links: {error}")
            return

        if response.status_code != 200:
            print(f"Error fetching episode links: HTTP {response.status_code}")
            return

        soup = BeautifulSoup(response.text, "html.parser")

        # The episode information is contained in row tables on the page.
        rows = soup.find_all("tr")
        episodes_link = []
        for row in rows:
            # Each episode row has exactly 4 cells.
            cells = row.find_all("td")
            if len(cells) not in (3, 4):
                continue

            first_cell = cells[0]
            link = first_cell.find("a", href=True)
            if link is None:
                continue

            episodes_link.append(
                {
                    "episode_name": link.get_text(strip=True),
                    "url": urljoin(self.base_url, link["href"]),
                }
            )

        print(f"Total episodes found: {len(episodes_link)}")

        episodes_link_df = pd.DataFrame(episodes_link)
        os.makedirs(os.path.dirname(self.episodes_link_path), exist_ok=True)
        episodes_link_df.to_csv(self.episodes_link_path, index=False, sep="|")


    def sanitize_episode_name(self, episode_name: str) -> str:
        """Sanitizes an episode name by replacing unsupported characters with underscores."""
        unwanted_characters = [" ", "/", ":", "?", "*", '"', "<", ">", "|", ",", ".", "(", ")", "[", "]"]
        for char in unwanted_characters:
            episode_name = episode_name.replace(char, "_")
        return episode_name
    

    def scrape_right_panel(self, soup: BeautifulSoup) -> dict:
        """Scrapes the right panel of the episode page, with main episode info."""
        right_panel_data = {}
        right_panel = soup.find(
            "table",
            attrs={
                "align": "right",
                "style": "background:#f0e3a2; border:2px solid #e9d677; width:19%; border-radius:10px;",
            },
        )

        if right_panel is None:
            return right_panel_data

        main_image = right_panel.find("img")
        right_panel_data["main_image_url"] = main_image["src"] if main_image else None

        for episode_info_row in right_panel.find_all("tr"):
            attribute = episode_info_row.find_all("th")
            values_data = episode_info_row.find_all("td")

            if len(attribute) == 1 and len(values_data) == 1:
                attribute_name = attribute[0].get_text(strip=True).lower().replace(" |:", "_")
                attribute_values = values_data[0].find_all("a")

                if len(attribute_values) > 0:
                    attribute_values_list = [a.get_text(strip=True) for a in attribute_values]
                else:
                    attribute_values_list = [values_data[0].get_text(strip=True)]

                right_panel_data[attribute_name] = attribute_values_list

        return right_panel_data


    def scrape_synopsis(self, soup: BeautifulSoup) -> str:
        """Scrapes the synopsis section for an episode page."""

        synopsis_title_element = soup.find("span", {"id": "Synopsis"})
        if synopsis_title_element is not None:
            synopsis_element = synopsis_title_element.find_parent("h2").find_next_sibling("dl")
            if synopsis_element is not None:
                return synopsis_element.get_text(" ", strip=True)

        summary_title_element = soup.find("span", {"id": "Summary"})
        if summary_title_element is not None:
            summary_element = summary_title_element.find_parent("h2").find_next_sibling("dl")
            if summary_element is not None:
                return summary_element.get_text(" ", strip=True)
        else:
            return ""
        
    

    def scrape_episodes_data(self, skip_existing_episodes: bool = False) -> None:

        warnings = []
        episodes_link_df = pd.read_csv(self.episodes_link_path, sep="|")
        total_episodes = len(episodes_link_df)

        for i, row in episodes_link_df.iterrows():
            self.episode_name = row["episode_name"]
            self.episode_url = row["url"]
            self.sanitized_episode_name = self.sanitize_episode_name(self.episode_name)
            self.episode_json_path = os.path.join(
                self.episodes_data_dir,
                f"{self.sanitized_episode_name}.json",
            )

            if skip_existing_episodes and os.path.isfile(self.episode_json_path):
                print(
                    f"Skipping episode {i + 1}/{total_episodes}: {self.episode_name:<80}",
                    end="\r",
                )
                continue

            print(
                f"Scraping episode {i + 1}/{total_episodes}: {self.episode_name:<80}",
                end="\r",
            )

            time.sleep(random.uniform(1, 3))

            try:
                response = requests.get(self.episode_url, timeout=20)
            except requests.RequestException as error:
                self.add_warning(warnings, "request_error_url", str(error))
                continue

            if response.status_code != 200:
                self.add_warning(
                    warnings,
                    "request_error_url",
                    f"HTTP {response.status_code}",
                )
                time.sleep(60)
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            episode_data = {
                "episode_name": self.episode_name,
                "url": self.episode_url,
            }

            right_panel_data = self.scrape_right_panel(soup)
            if right_panel_data == {}:
                self.add_warning(warnings, "missing_right_panel")
            episode_data.update(right_panel_data)

            episode_synopsis = self.scrape_synopsis(soup)
            if episode_synopsis == "":
                self.add_warning(warnings, "missing_synopsis")
            episode_data["synopsis"] = episode_synopsis

            os.makedirs(self.episodes_data_dir, exist_ok=True)
            with open(self.episode_json_path, "w", encoding="utf-8") as file:
                json.dump(episode_data, file)

        warnings_df = pd.DataFrame(warnings)
        os.makedirs(self.warnings_dir, exist_ok=True)
        warnings_df.to_csv(self.warnings_csv_path, index=False, sep="|")


if __name__ == "__main__":
    scraper = WikiSimpsonScraper()
    scraper.scrape_episodes_links()
    scraper.scrape_episodes_data(skip_existing_episodes=True)


