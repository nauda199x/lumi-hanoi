#!/usr/bin/env python3
"""Repository-wide static SEO QA for Lumi Hanoi V5.1.

The checks deliberately use only the Python standard library so they can run in
CI without installing dependencies.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_ORIGIN = "https://lumi-hanoi.com"
REQUIRED_PATHS = {
    "/", "/tong-quan-lumi-hanoi/", "/vi-tri-lumi-hanoi/",
    "/mat-bang-lumi-hanoi/", "/tien-ich-lumi-hanoi/",
    "/phap-ly-lumi-hanoi/", "/thiet-ke-lumi-hanoi/",
    "/tien-do-lumi-hanoi/", "/noi-that-ban-giao-lumi-hanoi/",
    "/lumi-signature/", "/lumi-prestige/", "/lumi-elite/",
    "/can-ho-1-phong-ngu-lumi-hanoi/", "/can-ho-2-phong-ngu-lumi-hanoi/",
    "/can-ho-3-phong-ngu-lumi-hanoi/", "/can-ho-4-phong-ngu-lumi-hanoi/",
    "/duplex-penthouse-lumi-hanoi/", "/mua-ban-lumi-hanoi/",
    "/cho-thue-lumi-hanoi/", "/ky-gui-lumi-hanoi/", "/tin-tuc/",
}
TOWER_LOOKUP_PATH = re.compile(
    r"^/toa-(?:signature-(?:1|2|3|5|6)|prestige-(?:1|2)|elite-(?:1|2))-lumi-hanoi/$"
)


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self.description = ""
        self.canonicals: list[str] = []
        self.h1_count = 0
        self.links: list[str] = []
        self.json_ld: list[str] = []
        self.noindex = False
        self._capture: str | None = None
        self._buffer: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "h1":
            self.h1_count += 1
        elif tag == "title":
            self._capture, self._buffer = "title", []
        elif tag == "script" and values.get("type", "").lower() == "application/ld+json":
            self._capture, self._buffer = "json", []
        elif tag == "meta" and values.get("name", "").lower() == "description":
            self.description = (values.get("content") or "").strip()
        elif tag == "meta" and values.get("name", "").lower() == "robots":
            self.noindex |= "noindex" in (values.get("content") or "").lower()
        elif tag == "link" and "canonical" in (values.get("rel") or "").lower().split():
            self.canonicals.append((values.get("href") or "").strip())
        elif tag == "a" and values.get("href"):
            self.links.append(values["href"] or "")

    def handle_data(self, data: str) -> None:
        if self._capture:
            self._buffer.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "title" and self._capture == "title":
            self.title = " ".join("".join(self._buffer).split())
            self._capture = None
        elif tag == "script" and self._capture == "json":
            self.json_ld.append("".join(self._buffer))
            self._capture = None


def public_path(file_path: Path) -> str:
    relative = file_path.relative_to(ROOT).as_posix()
    return "/" if relative == "index.html" else "/" + relative.removesuffix("index.html")


def local_file(url_path: str) -> Path:
    clean = unquote(url_path).lstrip("/")
    candidate = ROOT / clean
    if not candidate.suffix:
        candidate /= "index.html"
    return candidate


def title_fingerprint(title: str) -> str:
    """Remove the page-specific lead phrase to expose repeated templates."""
    parts = re.split(r"\s*[|–—:]\s*", title, maxsplit=1)
    return re.sub(r"\s+", " ", parts[-1].casefold()).strip()


def main() -> int:
    errors: list[str] = []
    pages: dict[str, PageParser] = {}
    title_owners: dict[str, str] = {}
    description_owners: dict[str, str] = {}
    canonical_owners: dict[str, str] = {}

    for html_file in sorted(ROOT.rglob("*.html")):
        if ".git" in html_file.parts:
            continue
        parser = PageParser()
        parser.feed(html_file.read_text(encoding="utf-8"))
        path = public_path(html_file)
        if parser.noindex:  # 404 and any deliberately excluded utility pages
            continue
        pages[path] = parser
        expected = CANONICAL_ORIGIN + path
        if parser.h1_count != 1:
            errors.append(f"{path} has {parser.h1_count} H1 elements (expected 1)")
        if not parser.title:
            errors.append(f"{path} has no title")
        elif parser.title in title_owners:
            errors.append(f"{path} duplicates title from {title_owners[parser.title]}")
        else:
            title_owners[parser.title] = path
        if not parser.description:
            errors.append(f"{path} has no meta description")
        elif parser.description in description_owners:
            errors.append(f"{path} duplicates description from {description_owners[parser.description]}")
        else:
            description_owners[parser.description] = path
        if len(parser.canonicals) != 1:
            errors.append(f"{path} has {len(parser.canonicals)} canonicals (expected 1)")
        elif parser.canonicals[0] != expected:
            errors.append(f"{path} canonical is {parser.canonicals[0]!r}; expected {expected!r}")
        elif expected in canonical_owners:
            errors.append(f"{path} duplicates canonical from {canonical_owners[expected]}")
        else:
            canonical_owners[expected] = path
        for block in parser.json_ld:
            try:
                json.loads(block)
            except json.JSONDecodeError as exc:
                errors.append(f"{path} has invalid JSON-LD: {exc}")

    missing_required = REQUIRED_PATHS - pages.keys()
    for path in sorted(missing_required):
        errors.append(f"required indexable page is missing or noindexed: {path}")

    for source_path, parser in pages.items():
        for href in parser.links:
            parsed = urlparse(href)
            if parsed.scheme in {"mailto", "tel", "javascript"} or href.startswith("#"):
                continue
            if parsed.netloc and parsed.netloc != urlparse(CANONICAL_ORIGIN).netloc:
                continue
            if parsed.scheme and parsed.scheme not in {"http", "https"}:
                continue
            target_path = parsed.path
            if not target_path:
                continue
            if not target_path.startswith("/"):
                base = source_path if source_path.endswith("/") else source_path.rsplit("/", 1)[0] + "/"
                target_path = str(Path(base) / target_path)
            if not local_file(target_path).is_file():
                errors.append(f"{source_path} links to missing local target: {href}")

    sitemap_root = ElementTree.parse(ROOT / "sitemap.xml")
    sitemap_urls = [node.text.strip() for node in sitemap_root.findall(".//{*}loc") if node.text]
    for url in sitemap_urls:
        parsed = urlparse(url)
        if parsed.netloc != urlparse(CANONICAL_ORIGIN).netloc or not local_file(parsed.path).is_file():
            errors.append(f"sitemap URL does not resolve to a local page: {url}")
        elif parsed.path not in pages:
            errors.append(f"sitemap URL is unexpectedly noindexed: {url}")

    # V8.2 tower lookup pages deliberately form one named entity cluster. Their
    # exact titles, descriptions and canonicals are still required to be unique
    # above, but a shared lookup suffix is not doorway-page evidence by itself.
    fingerprints = Counter(
        title_fingerprint(parser.title)
        for path, parser in pages.items()
        if not TOWER_LOOKUP_PATH.match(path)
    )
    for template, count in fingerprints.items():
        if template and count >= 4:
            errors.append(f"obvious title template repeated on {count} pages: {template!r}")

    if errors:
        print("SEO V5.1 QA failed:")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print(
        f"SEO V5.1 QA passed for {len(pages)} indexable pages, "
        f"{len(sitemap_urls)} sitemap URLs and {sum(len(p.links) for p in pages.values())} links."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
