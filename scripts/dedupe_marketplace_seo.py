#!/usr/bin/env python3
"""Ensure generated marketplace SEO metadata is unique across listing URLs.

The structured SEO normalizer intentionally avoids user-written promotional copy.
That can make two genuinely different listings with identical structured facts share
one title/description. This post-process only touches duplicate metadata and adds the
listing code as a stable disambiguator. Visible H1, slug and canonical stay unchanged.
"""
from __future__ import annotations

import html
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATED_MARKER = ".marketplace-generated"
ROOTS = (ROOT / "mua-ban-lumi-hanoi", ROOT / "cho-thue-lumi-hanoi")
TITLE_MAX = 70
DESCRIPTION_MAX = 158
SITE_SUFFIX = " | Lumi Hanoi"


def generated_pages() -> list[Path]:
    pages: list[Path] = []
    for root in ROOTS:
        if not root.exists():
            continue
        for child in root.iterdir():
            if child.is_dir() and (child / GENERATED_MARKER).is_file() and (child / "index.html").is_file():
                pages.append(child / "index.html")
    return sorted(pages)


def extract(pattern: str, raw: str) -> str:
    match = re.search(pattern, raw, flags=re.I | re.S)
    return html.unescape(match.group(1)).strip() if match else ""


def listing_code(raw: str, path: Path) -> str:
    code = extract(r'<span\s+data-detail-code[^>]*>([^<]+)</span>', raw)
    if code:
        return code
    match = re.search(r'-lh-([a-z0-9]{6,12})$', path.parent.name, flags=re.I)
    return f"LH-{match.group(1).upper()}" if match else path.parent.name[-12:].upper()


def unique_title(current: str, code: str) -> str:
    marker = f" · {code}"
    suffix = SITE_SUFFIX if current.endswith(SITE_SUFFIX) else ""
    base = current[:-len(suffix)] if suffix else current
    room = TITLE_MAX - len(marker) - len(suffix)
    if len(base) > room:
        trimmed = base[:max(1, room)].rsplit(" ", 1)[0].rstrip(" ,.-")
        base = trimmed or base[:max(1, room)].rstrip(" ,.-")
    return f"{base}{marker}{suffix}"[:TITLE_MAX]


def unique_description(current: str, code: str) -> str:
    marker = f" Mã tin {code}."
    room = DESCRIPTION_MAX - len(marker)
    base = current.strip()
    if len(base) > room:
        base = base[:max(1, room)].rsplit(" ", 1)[0].rstrip(" ,.-") + "."
    elif base and not base.endswith((".", "!", "?", "…")):
        base += "."
    return (base.rstrip() + marker)[:DESCRIPTION_MAX]


def replace_meta(raw: str, key: str, value: str, attr: str = "name") -> str:
    escaped = html.escape(value, quote=True)
    pattern = rf'<meta\s+{attr}="{re.escape(key)}"\s+content="[^"]*"\s*/?>'
    return re.sub(pattern, f'<meta {attr}="{key}" content="{escaped}">', raw, count=1, flags=re.I)


def rewrite_schema(raw: str, *, title: str | None, description: str | None) -> str:
    pattern = r'(<script\s+type="application/ld\+json">)(.*?)(</script>)'
    match = re.search(pattern, raw, flags=re.S | re.I)
    if not match:
        return raw
    try:
        schema = json.loads(match.group(2))
    except json.JSONDecodeError:
        return raw
    graph = schema.get("@graph", []) if isinstance(schema, dict) else []
    for node in graph:
        if not isinstance(node, dict):
            continue
        if node.get("@type") == "BreadcrumbList" and title:
            for item in node.get("itemListElement", []):
                if isinstance(item, dict) and item.get("position") == 3:
                    item["name"] = title.removesuffix(SITE_SUFFIX)
        if node.get("@type") == "WebPage":
            if title:
                name = title.removesuffix(SITE_SUFFIX)
                node["name"] = name
                offer = node.get("mainEntity")
                if isinstance(offer, dict) and isinstance(offer.get("itemOffered"), dict):
                    offer["itemOffered"]["name"] = name
            if description:
                node["description"] = description
    encoded = json.dumps(schema, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return raw[:match.start(2)] + encoded + raw[match.end(2):]


def main() -> None:
    pages = generated_pages()
    records = []
    title_groups: dict[str, list[int]] = defaultdict(list)
    description_groups: dict[str, list[int]] = defaultdict(list)

    for path in pages:
        raw = path.read_text(encoding="utf-8")
        title = extract(r'<title>(.*?)</title>', raw)
        description = extract(r'<meta\s+name="description"\s+content="([^"]*)"', raw)
        index = len(records)
        records.append({"path": path, "raw": raw, "title": title, "description": description, "code": listing_code(raw, path)})
        if title:
            title_groups[title].append(index)
        if description:
            description_groups[description].append(index)

    title_changes: dict[int, str] = {}
    description_changes: dict[int, str] = {}
    for indexes in title_groups.values():
        if len(indexes) > 1:
            for index in indexes[1:]:
                title_changes[index] = unique_title(records[index]["title"], records[index]["code"])
    for indexes in description_groups.values():
        if len(indexes) > 1:
            for index in indexes[1:]:
                description_changes[index] = unique_description(records[index]["description"], records[index]["code"])

    changed = 0
    for index, record in enumerate(records):
        title = title_changes.get(index)
        description = description_changes.get(index)
        if not title and not description:
            continue
        raw = record["raw"]
        if title:
            escaped_title = html.escape(title, quote=False)
            raw = re.sub(r'<title>.*?</title>', f'<title>{escaped_title}</title>', raw, count=1, flags=re.I | re.S)
            raw = replace_meta(raw, "og:title", title, attr="property")
            raw = replace_meta(raw, "twitter:title", title)
        if description:
            raw = replace_meta(raw, "description", description)
            raw = replace_meta(raw, "og:description", description, attr="property")
            raw = replace_meta(raw, "twitter:description", description)
        raw = rewrite_schema(raw, title=title, description=description)
        record["path"].write_text(raw, encoding="utf-8")
        changed += 1

    # Final hard guard: no duplicate crawler-visible title or description remains.
    seen_titles: dict[str, Path] = {}
    seen_descriptions: dict[str, Path] = {}
    for path in pages:
        raw = path.read_text(encoding="utf-8")
        title = extract(r'<title>(.*?)</title>', raw)
        description = extract(r'<meta\s+name="description"\s+content="([^"]*)"', raw)
        if title in seen_titles:
            raise RuntimeError(f"duplicate title remains: {path} == {seen_titles[title]}")
        if description in seen_descriptions:
            raise RuntimeError(f"duplicate description remains: {path} == {seen_descriptions[description]}")
        if title:
            seen_titles[title] = path
        if description:
            seen_descriptions[description] = path

    print(f"Marketplace SEO dedupe: checked {len(pages)} pages, changed {changed}")


if __name__ == "__main__":
    main()
