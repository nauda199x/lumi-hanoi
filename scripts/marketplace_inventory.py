"""Prerender the sale inventory and real paginated HTML for GitHub Pages.

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


def page_url(page):
    return "/mua-ban-lumi-hanoi/" + (f"page/{page}/" if page > 1 else "")


def render_row(g, listing, index=0):
    esc = g.esc
    url = esc(g.listing_url(listing))
    title = esc(listing.get("title") or "Xem căn hộ")
    images = sorted((i for i in listing.get("listing_images", []) if i.get("storage_path")), key=lambda i: i.get("sort_order") or 0)
    media = '<span class="inventory-placeholder">Chưa có ảnh</span>'
    if images:
        media += (f'<img src="{esc(g.storage_url(images[0]["storage_path"]))}" '
                  f'alt="{esc(images[0].get("alt_text") or listing.get("title"))}" width="280" height="210" '
                  f'loading="{"eager" if index == 0 else "lazy"}" decoding="async">')
        if len(images) > 1:
            media += f'<span class="inventory-image-count">{len(images)} ảnh</span>'
    specs = " · ".join(s for s in [
        f'{g.format_area(listing["area_sqm"])} m²' if g.numeric(listing.get("area_sqm")) else "",
        g.clean(listing.get("unit_type")),
        f'Tầng {g.clean(listing["floor_label"]).lower()}' if listing.get("floor_label") else "",
    ] if s)
    place = " · ".join(str(listing[k]) for k in ("phase", "tower") if listing.get(k))
    info = f'<h3><a href="{url}" title="{title}">{title}</a></h3>'
    if specs:
        info += f'<p class="inventory-specs">{esc(specs)}</p>'
    if place:
        info += f'<p class="inventory-location" title="{esc(place)}">{esc(place)}</p>'
    amount = g.numeric(listing.get("price_vnd"))
    price_text = g.format_market_price(amount, "sale") if amount and amount >= 1e9 else g.format_price(listing)
    price = f'<strong>{esc(price_text)}</strong>'
    if g.numeric(listing.get("price_vnd")) and g.numeric(listing.get("area_sqm")):
        ppsm = float(listing["price_vnd"]) / float(listing["area_sqm"]) / 1e6
        price += f'<small>{esc(f"{ppsm:,.1f}".replace(",", "_").replace(".", ",").replace("_", ".").removesuffix(",0"))} tr/m²</small>'
    name = g.clean(listing.get("poster_name"))
    avatar = "" if not name else f'<span class="inventory-avatar" aria-hidden="true">{esc("".join(p[0] for p in name.split()[-2:]).upper())}</span>'
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
                   f'<span class="inventory-phone">{esc(phone)}</span><span class="inventory-call-label">Gọi</span></a>'
                   f'<a class="inventory-zalo" href="https://zalo.me/{zalo_phone}" target="_blank" rel="noopener">Zalo</a>')
    actions += f'<a class="inventory-view" href="{url}">Xem chi tiết →</a>'
    return (f'<article class="inventory-row" data-static-listing-card><a class="inventory-media" href="{url}" aria-label="Xem {title}">{media}</a>'
            f'<div class="inventory-info">{info}</div><div class="inventory-price">{price}</div>'
            f'<div class="inventory-poster">{avatar}<div>{person}</div></div><div class="inventory-actions">{actions}</div></article>')


def render_pager(page, pages):
    if pages <= 1:
        return ""
    def link(n, text=None, rel=""):
        attrs = (f' rel="{rel}"' if rel else "") + (' aria-current="page"' if n == page else "")
        return f'<a href="{page_url(n)}" data-page="{n}" aria-label="Trang {n}"{attrs}>{text or n}</a>'
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


def render_inventory_page(g, template, rows, page, pages):
    total = len(rows)
    start = (page - 1) * PAGE_SIZE
    selected = rows[start:start + PAGE_SIZE]
    raw = g.replace_marked_block(template, g.STATIC_LISTING_START, g.STATIC_LISTING_END,
                                 "\n".join(render_row(g, row, i) for i, row in enumerate(selected)))
    raw = g.replace_marked_block(raw, PAGER_START, PAGER_END, render_pager(page, pages))
    raw = re.sub(r'data-inventory-static-pages="\d+"', f'data-inventory-static-pages="{pages}"', raw)
    raw = re.sub(r'(<span class="marketplace-count" data-listing-count[^>]*>).*?(</span>)',
                 lambda m: m[1] + f"{total} tin đăng" + m[2], raw, count=1)
    summary = f"Hiển thị {start + 1}–{min(start + PAGE_SIZE, total)} trong {total} căn" if total else "Hiển thị 0 căn"
    raw = re.sub(r'(<p class="inventory-summary"[^>]*>).*?(</p>)', lambda m: m[1] + summary + m[2], raw, count=1)
    raw = re.sub(r'(<div class="inventory-state" data-listing-state)(?: hidden)?',
                 lambda m: m[1] + (" hidden" if total else ""), raw, count=1)
    raw = re.sub(r'<script type="application/ld\+json" data-inventory-schema>.*?</script>\s*', "", raw, flags=re.S)
    itemlist = {"@context": "https://schema.org", "@type": "ItemList", "@id": g.SITE + page_url(page) + "#inventory",
                "numberOfItems": len(selected), "itemListElement": [
                    {"@type": "ListItem", "position": start + i + 1, "url": g.SITE + g.listing_url(row), "name": row.get("title", "")}
                    for i, row in enumerate(selected)]}
    encoded = json.dumps(itemlist, ensure_ascii=False).replace("<", "\\u003c")
    raw = raw.replace("</head>", f'<script type="application/ld+json" data-inventory-schema>{encoded}</script>\n</head>')
    if page > 1:
        canonical = g.SITE + page_url(page)
        title = f"Mua bán căn hộ Lumi Hanoi – Trang {page}"
        description = f"Quỹ căn Lumi Hanoi đang bán, trang {page}. {summary}. Xem giá, diện tích, tòa và liên hệ trực tiếp người đăng."
        raw = re.sub(r'<title>.*?</title>', f'<title>{title}</title>', raw, count=1)
        raw = re.sub(r'(<link rel="canonical" href=")[^"]+', lambda m: m[1] + canonical, raw, count=1)
        for attribute, name, value in [("name", "description", description), ("property", "og:title", title),
                                        ("property", "og:description", description), ("property", "og:url", canonical),
                                        ("name", "twitter:title", title), ("name", "twitter:description", description)]:
            raw = re.sub(rf'(<meta {attribute}="{name}" content=")[^"]*', lambda m: m[1] + g.esc(value), raw, count=1)
        raw = raw.replace("<h1>Mua bán căn hộ Lumi Hanoi</h1>", f"<h1>Mua bán căn hộ Lumi Hanoi · Trang {page}</h1>")
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


def sync_sale_inventory(g, rows):
    path = g.ROOT / "mua-ban-lumi-hanoi/index.html"
    template = path.read_text(encoding="utf-8")
    if "data-inventory" not in template:
        raise RuntimeError("Sale inventory template is missing")
    rows = sorted(rows, key=lambda r: (r.get("approved_at") or "", r.get("created_at") or "", r.get("id") or ""), reverse=True)
    pages = max(1, math.ceil(len(rows) / PAGE_SIZE))
    path.write_text(render_inventory_page(g, template, rows, 1, pages), encoding="utf-8")
    directory = g.ROOT / "mua-ban-lumi-hanoi/page"
    for page in range(2, pages + 1):
        target = directory / str(page)
        target.mkdir(parents=True, exist_ok=True)
        (target / PAGE_MARKER).write_text("Generated sale inventory page\n")
        (target / "index.html").write_text(render_inventory_page(g, template, rows, page, pages), encoding="utf-8")
    if directory.exists():
        for child in directory.iterdir():
            if child.is_dir() and (child / PAGE_MARKER).is_file() and (not child.name.isdigit() or int(child.name) > pages):
                shutil.rmtree(child)
