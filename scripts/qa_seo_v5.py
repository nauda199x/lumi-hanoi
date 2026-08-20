#!/usr/bin/env python3
"""Static QA checks for the SEO Content V5 pages."""

from __future__ import annotations

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
NEW_SLUGS = (
    "phap-ly-lumi-hanoi",
    "thiet-ke-lumi-hanoi",
    "can-ho-1-phong-ngu-lumi-hanoi",
    "can-ho-2-phong-ngu-lumi-hanoi",
    "can-ho-3-phong-ngu-lumi-hanoi",
    "can-ho-4-phong-ngu-lumi-hanoi",
    "duplex-penthouse-lumi-hanoi",
)
PILLAR_SLUGS = ("tong-quan-lumi-hanoi", "vi-tri-lumi-hanoi", "tien-ich-lumi-hanoi")
EXPECTED_DATE = "2026-08-20"


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.h1_count = 0
        self.title = ""
        self.canonical = ""
        self.description = ""
        self.links: list[str] = []
        self.json_ld: list[str] = []
        self._capture: str | None = None
        self._buffer: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "h1":
            self.h1_count += 1
        elif tag == "title":
            self._capture, self._buffer = "title", []
        elif tag == "script" and values.get("type") == "application/ld+json":
            self._capture, self._buffer = "json", []
        elif tag == "link" and values.get("rel") == "canonical":
            self.canonical = values.get("href") or ""
        elif tag == "meta" and values.get("name") == "description":
            self.description = values.get("content") or ""
        elif tag == "a" and values.get("href"):
            self.links.append(values["href"] or "")

    def handle_data(self, data: str) -> None:
        if self._capture:
            self._buffer.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "title" and self._capture == "title":
            self.title = "".join(self._buffer).strip()
            self._capture = None
        elif tag == "script" and self._capture == "json":
            self.json_ld.append("".join(self._buffer))
            self._capture = None


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def main() -> int:
    errors: list[str] = []
    titles: dict[str, str] = {}
    descriptions: dict[str, str] = {}
    pages = NEW_SLUGS + PILLAR_SLUGS

    for slug in pages:
        path = ROOT / slug / "index.html"
        if not path.is_file():
            fail(errors, f"missing page: /{slug}/")
            continue
        source = path.read_text(encoding="utf-8")
        parser = PageParser()
        parser.feed(source)
        expected_url = f"https://lumi-hanoi.com/{slug}/"
        if parser.h1_count != 1:
            fail(errors, f"/{slug}/ has {parser.h1_count} H1 elements")
        if parser.canonical != expected_url:
            fail(errors, f"/{slug}/ has unexpected canonical: {parser.canonical}")
        if not parser.title or parser.title in titles:
            fail(errors, f"/{slug}/ has a missing or duplicate title")
        if not parser.description or parser.description in descriptions:
            fail(errors, f"/{slug}/ has a missing or duplicate description")
        titles[parser.title] = slug
        descriptions[parser.description] = slug

        structured_data = []
        for block in parser.json_ld:
            try:
                structured_data.append(json.loads(block))
            except json.JSONDecodeError as exc:
                fail(errors, f"/{slug}/ has invalid JSON-LD: {exc}")
        serialized = json.dumps(structured_data, ensure_ascii=False)
        if "BreadcrumbList" not in serialized:
            fail(errors, f"/{slug}/ is missing BreadcrumbList schema")
        if EXPECTED_DATE not in serialized:
            fail(errors, f"/{slug}/ is missing the V5 schema date")

        for href in parser.links:
            parsed = urlparse(href)
            if parsed.scheme or href.startswith(("#", "mailto:", "tel:")):
                continue
            target = href.split("#", 1)[0].split("?", 1)[0]
            if not target:
                continue
            local = ROOT / target.lstrip("/")
            if target.endswith("/"):
                local /= "index.html"
            if not local.exists():
                fail(errors, f"/{slug}/ links to missing local target: {href}")

        for date in ("30/08/2026", "31/01/2027"):
            bad = re.compile(
                rf"(?:ngày bàn giao\s*(?:là|:)?\s*{date}|"
                rf"{date}\s*(?:là|—|-)\s*(?:ngày\s*)?bàn giao)",
                re.I,
            )
            if bad.search(source):
                fail(errors, f"/{slug}/ may describe {date} as a handover date")

    sitemap = ElementTree.parse(ROOT / "sitemap.xml")
    locations = {node.text for node in sitemap.findall(".//{*}loc")}
    for slug in NEW_SLUGS:
        url = f"https://lumi-hanoi.com/{slug}/"
        if url not in locations:
            fail(errors, f"sitemap missing {url}")

    if errors:
        print("SEO V5 QA failed:")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print(f"SEO V5 QA passed for {len(pages)} pages and {len(NEW_SLUGS)} new sitemap URLs.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
