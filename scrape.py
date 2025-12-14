"""Simple web scraping utility.

This script fetches a webpage, extracts its title and all hyperlinks, and prints
basic metadata. It avoids external dependencies by relying solely on the Python
standard library.
"""
from __future__ import annotations

import argparse
import sys
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from typing import Iterable, List, Tuple

USER_AGENT = "Mozilla/5.0 (compatible; SimpleWebScraper/1.0)"


class SimpleHTMLParser(HTMLParser):
    """HTML parser that collects the document title and hyperlinks."""

    def __init__(self) -> None:
        super().__init__()
        self._in_title = False
        self._title_parts: List[str] = []
        self._links: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, str | None]]) -> None:
        if tag.lower() == "title":
            self._in_title = True
        if tag.lower() == "a":
            href = self._get_attr(attrs, "href")
            if href:
                self._links.append(href)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._title_parts.append(data.strip())

    @staticmethod
    def _get_attr(attrs: Iterable[Tuple[str, str | None]], name: str) -> str | None:
        for attr_name, attr_value in attrs:
            if attr_name.lower() == name:
                return attr_value
        return None

    @property
    def title(self) -> str | None:
        """Return the document title if found."""

        title = " ".join(part for part in self._title_parts if part)
        return title or None

    @property
    def links(self) -> List[str]:
        """Return all discovered hyperlinks."""

        return self._links


def fetch_page(url: str, timeout: float = 10.0) -> tuple[str, str]:
    """Fetch a page and return its text content and final URL."""

    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        text = response.read().decode(charset, errors="replace")
        return text, response.geturl()


def scrape(url: str, timeout: float = 10.0) -> tuple[str | None, List[str]]:
    """Fetch and parse the given URL, returning title and absolute links."""

    html, final_url = fetch_page(url, timeout)
    parser = SimpleHTMLParser()
    parser.feed(html)
    absolute_links = [urllib.parse.urljoin(final_url, link) for link in parser.links]
    return parser.title, absolute_links


def format_output(url: str, title: str | None, links: List[str]) -> str:
    """Create a readable string summarizing the scrape results."""

    lines = [f"URL: {url}"]
    lines.append(f"Title: {title or 'N/A'}")
    if links:
        lines.append("Links:")
        lines.extend(f"- {link}" for link in links)
    else:
        lines.append("Links: none found")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch a page and extract links.")
    parser.add_argument("url", nargs="?", help="URL to fetch")
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="Request timeout in seconds (default: 10)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    url = args.url or input("Enter URL to fetch: ").strip()
    if not url:
        print("No URL provided.", file=sys.stderr)
        return 1
    try:
        title, links = scrape(url, timeout=args.timeout)
    except Exception as exc:  # pragma: no cover - simple CLI
        print(f"Failed to scrape {url}: {exc}", file=sys.stderr)
        return 1

    print(format_output(url, title, links))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
