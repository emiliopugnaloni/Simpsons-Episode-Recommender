from pathlib import Path
from scraper.nohomer_scraper import NoHomerScraper


def test_parse_episode_links_from_real_fixture_extracts_expected_entries():
    fixture_path = Path("tests/fixtures/html/nohomer_forum_index.html")
    html = fixture_path.read_text(encoding="utf-8")

    scraper = NoHomerScraper()
    results = scraper.parse_episode_links_from_html(html)

    assert len(results) > 100
    assert ("Bart the Genius", "https://nohomers.net/forums/index.php?threads/rate-review-bart-the-genius.22736/") in results

    for episode_name, episode_url in results:
        assert episode_name
        assert episode_url.startswith("https://nohomers.net/forums/index.php?threads/")
