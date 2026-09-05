"""Prerender sale and rental inventories and real paginated HTML for GitHub Pages.

Called by the existing marketplace SEO sync; never changes listing detail URLs.
The same ten-record boundary and newest ordering are used by the public API.
"""
import json
import math
import re
import shutil
from pathlib import Path

PAGE_SIZE = 10
PAGE_MARKER = ".inventory-generated"
PAGER_START = "<!-- INVENTORY-PAGINATION:START -->"
PAGER_END = "<!-- INVENTORY-PAGINATION:END -->"


def page_url(page, listing_type="sale"):
    base = "/cho-thue-lumi-hanoi/" if listing_type == "rent" else "/mua-ban-lumi-hanoi/"
    return base + (f"page/{page}/" if page > 1 else "")


ICONS = {
    "pin": '<path d="M12 21s7-6.2 7-12a7 7 0 1 0-14 0c0 5.8 7 12 7 12Z"/><circle cx="12" cy="9" r="2.5"/>',
    "area": '<path d="M9 3H3v6m12-6h6v6M3 15v6h6m12-6v6h-6M3 3l5 5m8 8 5 5m0-18-5 5M8 16l-5 5"/>',
    "bed": '<path d="M3 18V7m18 11V7M3 15h18M6 11V7h12v4M3 11h18v9M3 15v5"/>',
    "floor": '<path d="m12 3 9 5-9 5-9-5 9-5Zm-9 9 9 5 9-5M3 16l9 5 9-5"/>',
    "phone": '<path d="m8 3 3 5-3 3c2 3 3 4 6 5l3-3 4 3c-1 4-3 5-6 4C8 18 3 12 3 6c0-2 2-3 5-3Z"/>',
    "image": '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="8" cy="9" r="1.5"/><path d="m3 17 5-5 4 4 3-3 6 6"/>',
}


def icon(name):
    return '<svg class="inventory-icon" viewBox="0 0 24 24" aria-hidden="true">' + ICONS[name] + '</svg>'


def render_row(g, listing, index=0):
    esc = g.esc
    rental = listing.get("listing_type") == "rent"
    url = esc(g.listing_url(listing))
    title = esc(listing.get("title") or "Xem căn hộ")
    images = sorted((i for i in listing.get("listing_images", []) if i.get("storage_path")), key=lambda i: i.get("sort_order") or 0)
    media = '<span class="inventory-placeholder">Chưa có ảnh</span>'
    if images:
        media += (f'<img src="{esc(g.storage_url(images[0]["storage_path"]))}" '
                  f'alt="{esc(images[0].get("alt_text") or listing.get("title") or "Ảnh căn hộ Lumi Hanoi")}" width="560" height="420" '
                  f'loading="{"eager" if index == 0 else "lazy"}" decoding="async">')
        media += f'<span class="inventory-image-count">{icon("image")}{len(images)} ảnh</span>'
    media += '<span class="inventory-status">' + ("CHO THUÊ" if rental else "MUA BÁN") + '</span>'
    place = " · ".join(str(listing[k]) for k in ("phase", "tower") if listing.get(k))
    info = f'<p class="inventory-location" title="{esc(place)}">{icon("pin")}<span>{esc(place)}</span></p>' if place else ""
    info += f'<h3><a href="{url}" title="{title}">{title}</a></h3>'
    specs = [("area", f'{g.format_area(listing["area_sqm"])} m²' if g.numeric(listing.get("area_sqm")) else ""),
             ("bed", g.clean(listing.get("unit_type"))),
             ("floor", f'Tầng {g.clean(listing["floor_label"]).lower()}' if listing.get("floor_label") else "")]
    specs = [(name, value) for name, value in specs if value]
    spec_html = "".join(f'<span>{icon(name)}{esc(value)}{", " if i < len(specs) - 1 else ""}</span>' for i, (name, value) in enumerate(specs))
    if spec_html:
        info += f'<p class="inventory-specs">{spec_html}</p>'
    amount = g.numeric(listing.get("price_vnd"))
    price_text = g.format_market_price(amount, "rent" if rental else "sale") if amount and (rental or amount >= 1e9) else g.format_price(listing)
    parts = re.fullmatch(r"(.*?) (tỷ|triệu/tháng|triệu)", price_text)
    value_html = esc(parts[1]) + f' <span class="inventory-price-unit">{esc(parts[2])}</span>' if parts else esc(price_text)
    price = '<span class="inventory-price-label">' + ("Giá thuê" if rental else "Giá bán") + '</span>' + f'<strong>{value_html}</strong>'
    if not rental and g.numeric(listing.get("price_vnd")) and g.numeric(listing.get("area_sqm")):
        ppsm = float(listing["price_vnd"]) / float(listing["area_sqm"]) / 1e6
        price += f'<small>{esc(f"{ppsm:,.1f}".replace(",", "_").replace(".", ",").replace("_", ".").removesuffix(",0"))} tr/m²</small>'
    name = g.clean(listing.get("poster_name"))
    initials = "".join(next(c for c in word if c.isalnum()) for word in name.split() if any(c.isalnum() for c in word))[-2:].upper()
    avatar = "" if not name else f'<span class="inventory-avatar" aria-hidden="true">{esc(initials)}</span>'
    person = f'<strong title="{esc(name)}">{esc(name)}</strong>' if name else ""
    date = g.date_only(listing.get("approved_at") or listing.get("created_at"))
    if date:
        person += f'<time datetime="{esc(date)}">Đăng {esc(g.vi_date(date))}</time>'
    phone = g.clean(listing.get("contact_phone"))
    tel = re.sub(r"[^+\d]", "", phone)
    actions = ""
    zalo_phone = re.sub(r"\D", "", phone)
    if tel:
        actions = (f'<a class="inventory-call" href="tel:{esc(tel)}" aria-label="Gọi {esc(name or "người đăng")}, {esc(phone)}">'
                   f'{icon("phone")}<span class="inventory-phone">{esc(phone)}</span><span class="inventory-call-label">Gọi</span></a>'
                   f'<a class="inventory-zalo" href="https://zalo.me/{zalo_phone}" target="_blank" rel="noopener">Zalo</a>')
    actions += f'<a class="inventory-view" href="{url}"><span>Xem chi tiết</span><span>→</span></a>'
    return (f'<article class="inventory-row" data-static-listing-card><a class="inventory-media" href="{url}" aria-label="Xem {title}">{media}</a>'
            f'<div class="inventory-info">{info}</div><div class="inventory-price">{price}</div>'
            f'<div class="inventory-poster">{avatar}<div>{person}</div></div><div class="inventory-actions">{actions}</div></article>')


def render_pager(page, pages, listing_type="sale"):
    if pages <= 1:
        return ""
    def link(n, text=None, rel=""):
        attrs = (f' rel="{rel}"' if rel else "") + (' aria-current="page"' if n == page else "")
        return f'<a href="{page_url(n, listing_type)}" data-page="{n}" aria-label="Trang {n}"{attrs}>{text or n}</a>'
    parts = [link(page - 1, "← Trước", "prev")] if page > 1 else []
    visible = {1, pages, page - 1, page, page + 1}
    if page < 3:
        visible.update([2, 3])
    last = 0
    for n in sorted(n for n in visible if 1 <= n <= pages):
        if last and n - last > 1:
            parts.append('<span class="inventory-ellipsis" aria-hidden="true">…</span>')
        parts.append(link(n))
        last = n
    if page < pages:
        parts.append(link(page + 1, "Tiếp →", "next"))
    return "".join(parts)


def render_inventory_page(g, template, rows, page, pages, listing_type="sale"):
    total = len(rows)
    start = (page - 1) * PAGE_SIZE
    selected = rows[start:start + PAGE_SIZE]
    raw = g.replace_marked_block(template, g.STATIC_LISTING_START, g.STATIC_LISTING_END,
                                 "\n".join(render_row(g, row, i) for i, row in enumerate(selected)))
    raw = g.replace_marked_block(raw, PAGER_START, PAGER_END, render_pager(page, pages, listing_type))
    home_title = re.search(r"<title>(.*?)</title>", template)[1]
    raw = re.sub(r'data-inventory-home-title="[^"]*"', lambda _: f'data-inventory-home-title="{g.esc(home_title)}"', raw, count=1)
    raw = re.sub(r'data-inventory-static-pages="\d+"', f'data-inventory-static-pages="{pages}"', raw)
    raw = re.sub(r'(<span class="marketplace-count" data-listing-count[^>]*>).*?(</span>)',
                 lambda m: m[1] + f"{total} tin đăng" + m[2], raw, count=1)
    summary = f"Hiển thị {start + 1}–{min(start + PAGE_SIZE, total)} trong {total} căn" if total else "Hiển thị 0 căn"
    raw = re.sub(r'(<p class="inventory-summary"[^>]*>).*?(</p>)', lambda m: m[1] + summary + m[2], raw, count=1)
    raw = re.sub(r'(<div class="inventory-state" data-listing-state)(?: hidden)?',
                 lambda m: m[1] + (" hidden" if total else ""), raw, count=1)
    raw = re.sub(r'<script type="application/ld\+json" data-inventory-schema>.*?</script>\s*', "", raw, flags=re.S)
    itemlist = {"@context": "https://schema.org", "@type": "ItemList", "@id": g.SITE + page_url(page, listing_type) + "#inventory",
                "numberOfItems": len(selected), "itemListElement": [
                    {"@type": "ListItem", "position": start + i + 1, "url": g.SITE + g.listing_url(row), "name": row.get("title", "")}
                    for i, row in enumerate(selected)]}
    encoded = json.dumps(itemlist, ensure_ascii=False).replace("<", "\\u003c")
    raw = raw.replace("</head>", f'<script type="application/ld+json" data-inventory-schema>{encoded}</script>\n</head>')
    if page > 1:
        canonical = g.SITE + page_url(page, listing_type)
        action = "Cho thuê" if listing_type == "rent" else "Mua bán"
        title = f"{action} căn hộ Lumi Hanoi – Trang {page}"
        description = f"Quỹ căn Lumi Hanoi {action.lower()}, trang {page}. {summary}. Xem giá, diện tích, tòa và liên hệ trực tiếp người đăng."
        raw = re.sub(r'<title>.*?</title>', f'<title>{title}</title>', raw, count=1)
        raw = re.sub(r'(<link rel="canonical" href=")[^"]+', lambda m: m[1] + canonical, raw, count=1)
        for attribute, name, value in [("name", "description", description), ("property", "og:title", title),
                                        ("property", "og:description", description), ("property", "og:url", canonical),
                                        ("name", "twitter:title", title), ("name", "twitter:description", description)]:
            raw = re.sub(rf'(<meta {attribute}="{name}" content=")[^"]*', lambda m: m[1] + g.esc(value), raw, count=1)
        raw = re.sub(r"<h1>(.*?)</h1>", lambda m: f"<h1>{m[1]} · Trang {page}</h1>", raw, count=1)
        # Later pages focus on inventory; the buying guide and its FAQ remain on page 1.
        guide = raw.find('<div class="container article-layout')
        if guide >= 0:
            end = raw.index("</main>", guide)
            raw = raw[:guide] + raw[end:]
        def update_graph(match):
            data = json.loads(match[1])
            graph = data.get("@graph")
            if graph is None:
                return match[0]
            graph[:] = [node for node in graph if node.get("@type") != "FAQPage"]
            for node in graph:
                if node.get("@type") == "CollectionPage":
                    node.update(name=title, headline=title, description=description, mainEntityOfPage=canonical)
                if node.get("@type") == "BreadcrumbList":
                    node["itemListElement"].append({"@type": "ListItem", "position": 3, "name": f"Trang {page}", "item": canonical})
            return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False).replace("<", "\\u003c") + '</script>'
        raw = re.sub(r'<script type="application/ld\+json">(.*?)</script>', update_graph, raw, flags=re.S)
        if 'name="robots"' not in raw:
            raw = raw.replace("</head>", '<meta name="robots" content="index,follow">\n</head>')
    return raw


def sync_inventory(g, rows, listing_type="sale"):
    segment = "cho-thue-lumi-hanoi" if listing_type == "rent" else "mua-ban-lumi-hanoi"
    path = g.ROOT / segment / "index.html"
    template = path.read_text(encoding="utf-8")
    if "data-inventory" not in template:
        raise RuntimeError("Inventory template is missing")
    rows = sorted(rows, key=lambda r: (r.get("approved_at") or "", r.get("created_at") or "", r.get("id") or ""), reverse=True)
    pages = max(1, math.ceil(len(rows) / PAGE_SIZE))
    path.write_text(render_inventory_page(g, template, rows, 1, pages, listing_type), encoding="utf-8")
    directory = g.ROOT / segment / "page"
    for page in range(2, pages + 1):
        target = directory / str(page)
        target.mkdir(parents=True, exist_ok=True)
        (target / PAGE_MARKER).write_text("Generated inventory page\n")
        (target / "index.html").write_text(render_inventory_page(g, template, rows, page, pages, listing_type), encoding="utf-8")
    if directory.exists():
        for child in directory.iterdir():
            if child.is_dir() and (child / PAGE_MARKER).is_file() and (not child.name.isdigit() or int(child.name) > pages):
                shutil.rmtree(child)
