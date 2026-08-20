#!/usr/bin/env python3
"""Static QA for the V6 transfer/resale content cluster (stdlib only)."""
from __future__ import annotations

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://lumi-hanoi.com"
SLUGS = (
    "quy-trinh-chuyen-nhuong-lumi-hanoi",
    "mua-chuyen-nhuong-lumi-hanoi-can-kiem-tra-gi",
    "thue-phi-chuyen-nhuong-can-ho-lumi-hanoi",
    "so-sanh-signature-prestige-elite-khi-mua-chuyen-nhuong",
    "chon-1pn-2pn-3pn-lumi-hanoi-khi-mua-chuyen-nhuong",
    "checklist-dat-coc-mua-chuyen-nhuong-lumi-hanoi",
)
PATHS = tuple(f"/tin-tuc/{slug}/" for slug in SLUGS)
LEGACY = ("/", "/mua-ban-lumi-hanoi/", "/tin-tuc/", "/phap-ly-lumi-hanoi/",
          "/mat-bang-lumi-hanoi/", "/lumi-signature/", "/lumi-prestige/", "/lumi-elite/")


class Parser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(); self.h1 = 0; self.title = ""; self.description = ""
        self.canonical = ""; self.links: list[str] = []; self.images: list[dict[str, str | None]] = []
        self.json_blocks: list[str] = []; self.noindex = False; self._capture = ""; self._buf: list[str] = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "h1": self.h1 += 1
        elif tag == "title": self._capture, self._buf = "title", []
        elif tag == "script" and values.get("type", "").lower() == "application/ld+json":
            self._capture, self._buf = "json", []
        elif tag == "meta" and values.get("name", "").lower() == "description": self.description = (values.get("content") or "").strip()
        elif tag == "meta" and values.get("name", "").lower() == "robots": self.noindex |= "noindex" in (values.get("content") or "").lower()
        elif tag == "link" and "canonical" in (values.get("rel") or "").lower().split(): self.canonical = values.get("href") or ""
        elif tag == "a" and values.get("href"): self.links.append(values["href"] or "")
        elif tag == "img": self.images.append(values)

    def handle_data(self, data):
        if self._capture: self._buf.append(data)

    def handle_endtag(self, tag):
        if tag == "title" and self._capture == "title": self.title = "".join(self._buf).strip(); self._capture = ""
        elif tag == "script" and self._capture == "json": self.json_blocks.append("".join(self._buf)); self._capture = ""


def file_for(path: str) -> Path:
    clean = unquote(urlparse(path).path).lstrip("/"); target = ROOT / clean
    return target if target.suffix else target / "index.html"


def parse(path: str) -> Parser:
    parser = Parser(); parser.feed(file_for(path).read_text(encoding="utf-8")); return parser


def schema_types(value) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        kind = value.get("@type")
        if isinstance(kind, str): found.add(kind)
        for child in value.values(): found |= schema_types(child)
    elif isinstance(value, list):
        for child in value: found |= schema_types(child)
    return found


def main() -> int:
    errors: list[str] = []; pages: dict[str, Parser] = {}
    for path in PATHS:
        if not file_for(path).is_file(): errors.append(f"missing V6 page: {path}"); continue
        p = pages[path] = parse(path)
        if p.h1 != 1: errors.append(f"{path}: expected one H1, found {p.h1}")
        if not p.title or not p.description: errors.append(f"{path}: title or description missing")
        if p.canonical != ORIGIN + path: errors.append(f"{path}: incorrect canonical {p.canonical!r}")
        if p.noindex or re.search(r"noindex", file_for(path).read_text(encoding="utf-8"), re.I): errors.append(f"{path}: accidental noindex")
        schemas = []
        for raw in p.json_blocks:
            try: schemas.append(json.loads(raw))
            except json.JSONDecodeError as exc: errors.append(f"{path}: invalid JSON-LD: {exc}")
        types = set().union(*(schema_types(s) for s in schemas)) if schemas else set()
        if not {"Article", "BreadcrumbList"} <= types: errors.append(f"{path}: Article/Breadcrumb schema missing")
        joined = " ".join(p.json_blocks)
        if "datePublished" not in joined or "dateModified" not in joined: errors.append(f"{path}: publication dates missing")
        if "/mua-ban-lumi-hanoi/" not in p.links: errors.append(f"{path}: missing pillar backlink")
        for href in p.links:
            parsed = urlparse(href)
            if parsed.scheme in ("mailto", "tel", "javascript") or href.startswith("#") or (parsed.netloc and parsed.netloc != "lumi-hanoi.com"): continue
            if parsed.path.startswith("/") and not file_for(parsed.path).is_file(): errors.append(f"{path}: broken local link {href}")
        for image in p.images:
            src = image.get("src") or ""
            if not (image.get("alt") or "").strip(): errors.append(f"{path}: image without alt: {src}")
            if not image.get("width") or not image.get("height"): errors.append(f"{path}: image missing dimensions: {src}")
            if src.startswith("/") and not (ROOT / src.lstrip("/")).is_file(): errors.append(f"{path}: missing image: {src}")
    titles = [p.title for p in pages.values()]; descriptions = [p.description for p in pages.values()]
    if len(titles) != len(set(titles)): errors.append("V6 titles are not unique")
    if len(descriptions) != len(set(descriptions)): errors.append("V6 descriptions are not unique")
    sitemap = {node.text.strip() for node in ElementTree.parse(ROOT / "sitemap.xml").findall(".//{*}loc") if node.text}
    for path in PATHS:
        if ORIGIN + path not in sitemap: errors.append(f"sitemap missing {path}")
    for hub in ("/mua-ban-lumi-hanoi/", "/tin-tuc/"):
        links = parse(hub).links
        for path in PATHS:
            if path not in links: errors.append(f"{hub} does not link to {path}")
    for path in LEGACY:
        if not file_for(path).is_file(): errors.append(f"required V5/V5.1 page missing: {path}")
    public = "\n".join(f.read_text(encoding="utf-8", errors="ignore") for f in ROOT.rglob("*.html"))
    if "chuyennhuonglumi.vn" in public.lower(): errors.append("competitor domain found in public HTML")
    if re.search(r"(?:liên hệ ngay|giữ chỗ ngay|cam kết lợi nhuận|giá tốt nhất)", public, re.I): errors.append("prohibited/obvious sales CTA wording found")
    if errors:
        print("SEO V6 QA failed:\n" + "\n".join(f"- {e}" for e in errors)); return 1
    print(f"SEO V6 QA passed: {len(PATHS)} articles, schemas, media, links, hubs and sitemap verified."); return 0


if __name__ == "__main__": sys.exit(main())
