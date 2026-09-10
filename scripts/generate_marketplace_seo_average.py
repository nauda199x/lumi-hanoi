#!/usr/bin/env python3
"""Generate marketplace SEO pages with arithmetic averages on the market price page.

The base marketplace generator remains responsible for listing pages, sitemaps and
market aggregation. For the price page, its statistics function is switched from
median to arithmetic mean before generation, then the explanatory copy is kept in
sync with that methodology.

Approved listing pages are also post-processed so user-written promotional headlines
stay visible on-page without becoming the SEO title/meta shown to search engines.
"""
import html as html_lib
import json
import re
from statistics import mean

import generate_marketplace_seo as gen

SEO_TITLE_MAX = 70
SEO_DESCRIPTION_MAX = 158


def allow_short_descriptions_for_indexing() -> None:
    """Keep approved listings indexable even when the description is short.

    The public form intentionally accepts any non-empty description. SEO indexing
    must follow the same rule instead of silently dropping listings below 40 chars.
    All other quality requirements (image, price, area, tower and unit type) remain.
    """
    def indexable(listing: dict) -> bool:
        images = listing.get("listing_images") or []
        return all(
            [
                len(gen.compact_text(listing.get("title", ""))) >= 12,
                bool(gen.compact_text(listing.get("description", ""))),
                bool(images),
                bool(listing.get("price_vnd")),
                bool(listing.get("area_sqm")),
                bool(listing.get("tower")),
                bool(listing.get("unit_type")),
            ]
        )

    gen.indexable = indexable


def _compact(value) -> str:
    return gen.compact_text(value)


def _floor_phrase(value) -> str:
    floor = _compact(value)
    if not floor:
        return ""
    floor = re.sub(r"^tầng\s+", "", floor, flags=re.I).strip()
    return f"tầng {floor}" if floor else ""


def _location(listing: dict, *, compact: bool = False) -> str:
    phase = _compact(listing.get("phase"))
    tower = _compact(listing.get("tower"))
    if compact and tower:
        return f"Lumi Hanoi {tower}"
    if phase:
        base = phase if phase.lower().startswith("lumi ") else f"Lumi {phase}"
    else:
        base = "Lumi Hanoi"
    if tower and tower.lower() not in base.lower().split():
        base = f"{base} {tower}"
    return base


def _subject(listing: dict) -> str:
    unit = _compact(listing.get("unit_type")) or "căn hộ"
    if unit.lower() == "shop chân đế":
        return "shop chân đế"
    if unit.lower() in {"căn hộ", "can ho"}:
        return "căn hộ"
    return f"căn {unit}"


def _trim_with_suffix(text: str, suffix: str, max_length: int) -> str:
    text = _compact(text)
    candidate = text + suffix
    if len(candidate) <= max_length:
        return candidate
    room = max_length - len(suffix) - 1
    shortened = text[: max(1, room)].rsplit(" ", 1)[0].rstrip(" ,.-")
    return shortened + suffix


def build_listing_seo(listing: dict) -> dict[str, str]:
    """Build deterministic SEO text from structured fields, never the UGC headline."""
    action = "Cho thuê" if listing.get("listing_type") == "rent" else "Bán"
    subject = _subject(listing)
    location = _location(listing)
    area = gen.format_area(listing.get("area_sqm"))
    floor = _floor_phrase(listing.get("floor_label"))

    seo_name = f"{action} {subject} {location}"
    if area:
        seo_name += f" {area}m²"
    full_name = f"{seo_name}, {floor}" if floor else seo_name
    suffix = " | Lumi Hanoi"

    # Keep the strongest entities (intent, unit, phase/tower, area) before optional floor.
    title = full_name + suffix
    if len(title) > SEO_TITLE_MAX:
        title = seo_name + suffix
    if len(title) > SEO_TITLE_MAX:
        compact_name = f"{action} {subject} {_location(listing, compact=True)}"
        if area:
            compact_name += f" {area}m²"
        title = compact_name + suffix
        seo_name = compact_name
    if len(title) > SEO_TITLE_MAX:
        title = _trim_with_suffix(seo_name, suffix, SEO_TITLE_MAX)
        seo_name = title[: -len(suffix)]

    facts = []
    if area:
        facts.append(f"diện tích {area}m²")
    if floor:
        facts.append(floor)
    price = gen.format_price(listing)
    if price and price != "Liên hệ":
        facts.append(f"giá {price}")
    intro = f"{action} {subject} tại {location}"
    if facts:
        intro += ", " + ", ".join(facts)
    description = intro + ". Xem hình ảnh, thông tin căn và liên hệ người đăng trên Lumi Hanoi."
    if len(description) > SEO_DESCRIPTION_MAX:
        description = intro + ". Xem hình ảnh và liên hệ người đăng trên Lumi Hanoi."
    if len(description) > SEO_DESCRIPTION_MAX:
        description = intro + ". Xem thông tin chi tiết trên Lumi Hanoi."
    if len(description) > SEO_DESCRIPTION_MAX:
        description = description[: SEO_DESCRIPTION_MAX - 1].rsplit(" ", 1)[0].rstrip(" ,.-") + "…"

    return {"title": title, "name": seo_name, "description": description}


def _replace_meta(raw: str, *, key: str, value: str, attr: str = "name") -> str:
    escaped = html_lib.escape(value, quote=True)
    pattern = rf'<meta\s+{attr}="{re.escape(key)}"\s+content="[^"]*"\s*/?>'
    replacement = f'<meta {attr}="{key}" content="{escaped}">'
    return re.sub(pattern, replacement, raw, count=1, flags=re.I)


def _rewrite_schema(raw: str, seo: dict[str, str]) -> str:
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
        if node.get("@type") == "BreadcrumbList":
            for item in node.get("itemListElement", []):
                if isinstance(item, dict) and item.get("position") == 3:
                    item["name"] = seo["name"]
        if node.get("@type") == "WebPage":
            node["name"] = seo["name"]
            node["description"] = seo["description"]
            offer = node.get("mainEntity")
            if isinstance(offer, dict):
                offered = offer.get("itemOffered")
                if isinstance(offered, dict):
                    offered["name"] = seo["name"]

    schema_json = json.dumps(schema, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return raw[: match.start(2)] + schema_json + raw[match.end(2) :]


def normalize_generated_listing_metadata(listings: list[dict]) -> int:
    """Rewrite crawler-visible metadata while preserving H1, slug and canonical URL."""
    changed = 0
    checked = 0
    for listing in listings:
        listing_type = listing.get("listing_type")
        slug = _compact(listing.get("slug"))
        if listing_type not in gen.CATEGORY or not slug:
            continue
        segment = gen.CATEGORY[listing_type][0]
        path = gen.ROOT / segment / slug / "index.html"
        if not path.exists():
            continue

        checked += 1
        seo = build_listing_seo(listing)
        raw = path.read_text(encoding="utf-8")
        original = raw
        escaped_title = html_lib.escape(seo["title"], quote=False)
        raw = re.sub(r"<title>.*?</title>", f"<title>{escaped_title}</title>", raw, count=1, flags=re.S | re.I)
        raw = _replace_meta(raw, key="description", value=seo["description"])
        raw = _replace_meta(raw, key="og:title", value=seo["title"], attr="property")
        raw = _replace_meta(raw, key="og:description", value=seo["description"], attr="property")

        raw = _replace_meta(raw, key="twitter:title", value=seo["title"])
        raw = _replace_meta(raw, key="twitter:description", value=seo["description"])
        if 'name="twitter:title"' not in raw:
            twitter = (
                '<meta name="twitter:card" content="summary_large_image">\n'
                f'  <meta name="twitter:title" content="{html_lib.escape(seo["title"], quote=True)}">\n'
                f'  <meta name="twitter:description" content="{html_lib.escape(seo["description"], quote=True)}">'
            )
            raw = re.sub(
                r'<meta\s+name="twitter:card"\s+content="summary_large_image"\s*/?>',
                twitter,
                raw,
                count=1,
                flags=re.I,
            )

        raw = _rewrite_schema(raw, seo)

        # Hard guards: metadata must be normalized; visible UGC title/canonical stay untouched.
        expected_title = f"<title>{escaped_title}</title>"
        if expected_title not in raw:
            raise RuntimeError(f"SEO title normalization failed for {path}")
        headline_match = re.search(
            r'<h1\b[^>]*\bdata-detail-title\b[^>]*>(.*?)</h1>',
            raw,
            flags=re.S | re.I,
        )
        visible_title = ""
        if headline_match:
            visible_title = html_lib.unescape(re.sub(r"<[^>]+>", "", headline_match.group(1))).strip()
        if visible_title != _compact(listing.get("title")):
            raise RuntimeError(f"Visible listing headline changed unexpectedly for {path}")
        canonical = gen.SITE + gen.listing_url(listing)
        if f'<link rel="canonical" href="{gen.esc(canonical)}">' not in raw:
            raise RuntimeError(f"Canonical changed unexpectedly for {path}")

        if raw != original:
            path.write_text(raw, encoding="utf-8")
            changed += 1

    print(f"Listing SEO metadata: normalized {checked} generated pages ({changed} changed)")
    return changed


def update_price_methodology_copy() -> None:
    path = gen.PRICE_PAGE
    if not path.exists():
        return

    raw = path.read_text(encoding="utf-8")
    replacements = {
        "giá bán/thuê trung vị": "giá bán/thuê trung bình",
        "Giá trung vị và giá trên mét vuông được tính từ giá rao và diện tích của các tin đang công khai; không phải giá giao dịch công chứng.":
            "Giá trung bình và giá trung bình trên mét vuông được tính từ giá rao và diện tích của các tin đang công khai; không phải giá giao dịch công chứng.",
        "Giá/m² được tính bằng giá rao chia cho diện tích khai báo của từng tin đủ dữ liệu, sau đó dùng trung vị để giảm ảnh hưởng của các mức giá quá cao hoặc quá thấp.":
            "Giá/m² được tính bằng giá rao chia cho diện tích khai báo của từng tin đủ dữ liệu, sau đó lấy trung bình cộng đơn giá/m² của các tin trong cùng nhóm.",
        "Giá bán trung vị": "Giá bán trung bình",
        "Giá/m² trung vị": "Giá/m² trung bình",
        "Dùng trung vị, không dùng trung bình": "Trung bình cộng từ các tin đủ dữ liệu",
        "Giá thuê trung vị": "Giá thuê trung bình",
        ">Trung vị</th>": ">Trung bình</th>",
        "Với mỗi nhóm, chúng tôi ưu tiên <strong>trung vị</strong> thay vì trung bình cộng để một tin quá cao hoặc quá thấp không kéo sai toàn bộ kết quả.":
            "Với mỗi nhóm, hệ thống tính <strong>trung bình cộng</strong> từ các tin đủ dữ liệu để phản ánh mức giá rao bình quân của nguồn hàng đang công khai.",
        "Dùng trung vị cho giá và giá/m².": "Dùng trung bình cộng cho giá và giá/m².",
        "<details><summary>Vì sao dùng trung vị?</summary><p>Trung vị ít bị méo bởi một vài mức giá bất thường hơn trung bình cộng, đặc biệt khi số tin của một nhóm còn chưa lớn.</p></details>":
            "<details><summary>Giá trung bình được tính thế nào?</summary><p>Hệ thống cộng các mức giá hợp lệ trong từng nhóm rồi chia cho số tin đủ dữ liệu. Giá/m² trung bình được tính từ đơn giá/m² của từng tin đủ giá và diện tích.</p></details>",
    }
    for old, new in replacements.items():
        raw = raw.replace(old, new)

    if "trung vị" in raw.lower():
        raise RuntimeError("Price page still contains median wording after average conversion")

    path.write_text(raw, encoding="utf-8")


def remove_rental_ppsm_display() -> None:
    """Keep rental market pricing in monthly totals; price/m² remains sale-only."""
    path = gen.PRICE_PAGE
    if not path.exists():
        return

    raw = path.read_text(encoding="utf-8")
    rent_marker = '<div class="market-table-head"><div><p class="eyebrow">Cho thuê</p><h3>Giá rao thuê theo loại căn</h3></div><a href="/cho-thue-lumi-hanoi/">Xem quỹ thuê →</a></div>'
    start = raw.find(rent_marker)
    if start < 0:
        raise RuntimeError("Could not locate rental price table")

    card_start = raw.rfind('<div class="market-table-card">', 0, start)
    next_card = raw.find('<div class="market-table-card">', start + len(rent_marker))
    if card_start < 0 or next_card < 0:
        raise RuntimeError("Could not isolate rental price table")

    block = raw[card_start:next_card]
    block = block.replace('<th>Giá/m²/tháng</th>', '')
    block = re.sub(
        r'(<tr><th>[^<]+</th><td>[^<]*</td><td>[^<]*</td><td>[^<]*</td>)<td>[^<]*</td>(</tr>)',
        r'\1\2',
        block,
    )
    raw = raw[:card_start] + block + raw[next_card:]

    # Shop rental pricing follows the same rule: show total monthly rent only.
    raw = re.sub(
        r'(<dt>Shop đang thuê</dt><dd>[^<]*?) · khoảng [^<]*(</dd>)',
        r'\1\2',
        raw,
        count=1,
    )

    if "Giá/m²/tháng" in raw:
        raise RuntimeError("Rental price/m² column still present after cleanup")

    path.write_text(raw, encoding="utf-8")


def main() -> None:
    # The public posting form allows short descriptions. Keep the SEO generator in
    # sync so approved listings are not excluded from indexability by text length.
    allow_short_descriptions_for_indexing()

    # generate_marketplace_seo imports `median` into module scope. Rebinding that
    # symbol makes all price-page aggregate calculations use arithmetic mean,
    # including overall, unit-type, phase and shop statistics.
    gen.median = mean

    # Capture the same approved rows used by the generator so metadata normalization
    # does not need a second Supabase request every five minutes.
    approved_rows: list[dict] = []
    original_fetch = gen.fetch_approved

    def fetch_and_capture() -> list[dict]:
        rows = original_fetch()
        approved_rows[:] = rows
        return rows

    gen.fetch_approved = fetch_and_capture
    try:
        gen.main()
    finally:
        gen.fetch_approved = original_fetch

    normalize_generated_listing_metadata(approved_rows)
    update_price_methodology_copy()
    remove_rental_ppsm_display()
    from optimize_responsive_photos import apply_markup
    apply_markup()
    print("Market price page: arithmetic-average methodology applied; rental price/m² hidden")


if __name__ == "__main__":
    main()