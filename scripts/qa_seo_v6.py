#!/usr/bin/env python3
"""V6 transfer-cluster QA; intentionally Python-standard-library only."""
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
V5_REQUIRED = (
    "/tong-quan-lumi-hanoi/", "/vi-tri-lumi-hanoi/",
    "/mat-bang-lumi-hanoi/", "/tien-ich-lumi-hanoi/",
    "/phap-ly-lumi-hanoi/", "/thiet-ke-lumi-hanoi/",
    "/lumi-signature/", "/lumi-prestige/", "/lumi-elite/",
    "/can-ho-1-phong-ngu-lumi-hanoi/",
    "/can-ho-2-phong-ngu-lumi-hanoi/",
    "/can-ho-3-phong-ngu-lumi-hanoi/", "/mua-ban-lumi-hanoi/",
)


class Parser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""; self.description = ""; self.h1 = 0
        self.canonical = ""; self.links: list[str] = []
        self.images: list[dict[str, str | None]] = []
        self.blocks: list[str] = []; self.noindex = False
        self._capture = ""; self._data: list[str] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "title": self._capture, self._data = "title", []
        elif tag == "h1": self.h1 += 1
        elif tag == "meta" and a.get("name", "").lower() == "description": self.description = (a.get("content") or "").strip()
        elif tag == "meta" and a.get("name", "").lower() == "robots": self.noindex |= "noindex" in (a.get("content") or "").lower()
        elif tag == "link" and "canonical" in (a.get("rel") or "").split(): self.canonical = a.get("href") or ""
        elif tag == "a" and a.get("href"): self.links.append(a["href"] or "")
        elif tag == "img": self.images.append(a)
        elif tag == "script" and a.get("type") == "application/ld+json": self._capture, self._data = "json", []

    def handle_data(self, data):
        if self._capture: self._data.append(data)

    def handle_endtag(self, tag):
        if tag == "title" and self._capture == "title": self.title = "".join(self._data).strip(); self._capture = ""
        elif tag == "script" and self._capture == "json": self.blocks.append("".join(self._data)); self._capture = ""


def file_for(path: str) -> Path:
    parsed = urlparse(path)
    clean = unquote(parsed.path).lstrip("/")
    target = ROOT / clean
    return target if target.suffix else target / "index.html"


def parse(path: str) -> Parser:
    parser = Parser(); parser.feed(file_for(path).read_text(encoding="utf-8")); return parser


def schema_types(data) -> set[str]:
    found: set[str] = set()
    if isinstance(data, dict):
        value = data.get("@type")
        if isinstance(value, str): found.add(value)
        for child in data.values(): found |= schema_types(child)
    elif isinstance(data, list):
        for child in data: found |= schema_types(child)
    return found


def main() -> int:
    errors: list[str] = []
    pages: dict[str, Parser] = {}
    for path in PATHS:
        if not file_for(path).is_file(): errors.append(f"missing V6 page: {path}"); continue
        p = pages[path] = parse(path)
        if p.h1 != 1: errors.append(f"{path}: expected one H1, found {p.h1}")
        if p.canonical != ORIGIN + path: errors.append(f"{path}: incorrect canonical {p.canonical!r}")
        if p.noindex: errors.append(f"{path}: accidental noindex")
        types: set[str] = set(); schemas = []
        for raw in p.blocks:
            try: schemas.append(json.loads(raw))
            except json.JSONDecodeError as exc: errors.append(f"{path}: invalid JSON-LD: {exc}")
        for item in schemas: types |= schema_types(item)
        if not {"Article", "BreadcrumbList"} <= types: errors.append(f"{path}: missing Article/BreadcrumbList schema")
        joined = " ".join(p.blocks)
        for field in ('"datePublished"', '"dateModified"', '"mainEntityOfPage"', '"inLanguage"'):
            if field not in joined: errors.append(f"{path}: schema missing {field}")
        if "/mua-ban-lumi-hanoi/" not in p.links: errors.append(f"{path}: missing transaction-pillar link")
        for href in p.links:
            u = urlparse(href)
            if u.scheme in {"mailto", "tel"} or href.startswith("#") or (u.netloc and u.netloc != "lumi-hanoi.com"): continue
            if u.path and not file_for(u.path).is_file(): errors.append(f"{path}: unresolved link {href}")
        for image in p.images:
            src = image.get("src") or ""
            if not src or not file_for(src).is_file(): errors.append(f"{path}: missing image {src!r}")
            if not (image.get("alt") or "").strip(): errors.append(f"{path}: image has empty alt")
            if not image.get("width") or not image.get("height"): errors.append(f"{path}: image lacks width/height")

    if len({p.title for p in pages.values()}) != len(pages): errors.append("V6 titles are not unique")
    if len({p.description for p in pages.values()}) != len(pages): errors.append("V6 meta descriptions are not unique")
    sitemap = {n.text.strip() for n in ElementTree.parse(ROOT / "sitemap.xml").findall(".//{*}loc") if n.text}
    for path in PATHS:
        if ORIGIN + path not in sitemap: errors.append(f"sitemap missing {path}")
    for owner in ("/mua-ban-lumi-hanoi/", "/tin-tuc/"):
        links = parse(owner).links
        for path in PATHS:
            if path not in links: errors.append(f"{owner} does not link to {path}")
    for path in V5_REQUIRED:
        if not file_for(path).is_file(): errors.append(f"V5/V5.1 required page missing: {path}")
    public = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in ROOT.rglob("*.html"))
    if "chuyennhuonglumi.vn" in public.lower(): errors.append("competitor domain found in public HTML")
    if re.search(r"(?:giá tốt nhất|cam kết lợi nhuận|còn duy nhất|suất ngoại giao)", public, re.I): errors.append("obvious fake sales CTA found")
    if re.search(r"(?:chuyennhuonglumi[^\s<]*(?:@|tel:)|(?:0|\+84)\d{8,10})", public, re.I): errors.append("possible competitor contact data found")
    if errors:
        print("SEO V6 QA failed:\n" + "\n".join(f"- {e}" for e in errors)); return 1
    print(f"SEO V6 QA passed: {len(pages)} articles, 20 required check groups, sitemap and hub/pillar links verified.")
    return 0


if __name__ == "__main__": sys.exit(main())
