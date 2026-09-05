"""Contract tests for generated inventory pages; fixtures never reach the site."""
import ast
import json
import re
import tempfile
from pathlib import Path
from types import SimpleNamespace
from html.parser import HTMLParser

import generate_marketplace_seo as gen
import marketplace_inventory as inv


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.rows = 0
        self.links = []
        self.images = []
        self.canonical = None
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "article" and a.get("class") == "inventory-row":
            self.rows += 1
        if tag == "a":
            self.links.append(a)
        if tag == "img":
            self.images.append(a)
        if tag == "link" and a.get("rel") == "canonical":
            self.canonical = a["href"]


def main():
    template = (gen.ROOT / "mua-ban-lumi-hanoi/index.html").read_text()
    # Synthetic records exercise page boundaries and escaping only in a temp dir.
    rows = [dict(id=f"{i:04}", slug=f"qa-listing-{i:04}", listing_type="sale", title=f"QA căn hộ {i}",
                 approved_at="2026-09-05T10:00:00Z", created_at="2026-09-05T09:00:00Z",
                 unit_type="2PN", phase="Signature", tower="S3", price_vnd=4280000000,
                 area_sqm=54, poster_name="QA", contact_phone="", listing_images=[]) for i in range(56)]
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        target = root / "mua-ban-lumi-hanoi/index.html"
        target.parent.mkdir(parents=True)
        target.write_text(template)
        g = SimpleNamespace(**{k: getattr(gen, k) for k in dir(gen) if not k.startswith("__")})
        g.ROOT = root
        inv.sync_sale_inventory(g, rows)
        seen = set()
        for n in range(1, 7):
            page = root / inv.page_url(n).lstrip("/") / "index.html"
            raw = page.read_text()
            parsed = Page(raw)
            assert parsed.rows == (10 if n < 6 else 6), (n, parsed.rows)
            assert parsed.canonical == gen.SITE + inv.page_url(n)
            links = {a["href"] for a in parsed.links if "data-page" in a}
            if n < 6:
                assert inv.page_url(n+1) in links
            if n > 1:
                assert inv.page_url(n-1) in links
                assert 'content="index,follow"' in raw
                assert "Hướng dẫn mua chuyển nhượng căn hộ Lumi Hanoi" not in raw
            detail_links = {a["href"] for a in parsed.links if "/qa-listing-" in a.get("href", "")}
            assert not seen.intersection(detail_links), "Pages repeat listings"
            seen.update(detail_links)
            for data in re.findall(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', raw, re.S):
                json.loads(data)
        assert len(seen) == 56
        original = target.read_bytes()
        inv.sync_sale_inventory(g, rows)
        assert target.read_bytes() == original, "Scheduled sync must be idempotent"
        inv.sync_sale_inventory(g, [])
        assert Page(target.read_text()).rows == 0
        assert 'data-listing-state hidden' not in target.read_text()
        assert not (root / "mua-ban-lumi-hanoi/page/2").exists()

    unusual = dict(rows[0], title='<script>alert("x")</script>', poster_name="", area_sqm=None, floor_label=None,
                   tower="", phase="", listing_images=[dict(storage_path="qa/one.jpg", sort_order=0)])
    raw = inv.render_row(gen, unusual)
    parsed = Page(raw)
    assert "<script>" not in raw and "&lt;script&gt;" in raw
    assert "— m²" not in raw and "Tầng —" not in raw and 'class="inventory-avatar"' not in raw
    assert parsed.images[0]["loading"] == "eager"
    assert parsed.images[0]["width"] and parsed.images[0]["height"] and parsed.images[0]["alt"]
    assert 'loading="lazy"' in inv.render_row(gen, unusual, 1)
    assert r"\1" in gen.replace_marked_block("A body B", "A", "B", r"Title \1"), "User text is not a regex replacement"
    for file in ("marketplace_inventory.py", "generate_marketplace_seo.py"):
        ast.parse((gen.ROOT / "scripts" / file).read_text(), feature_version=(3, 11))
    print("Inventory QA: 56 records → 6 crawlable pages, 10/page, self-canonicals, no duplicates, empty state, escaping, image hints, idempotent sync: PASS")


if __name__ == "__main__":
    main()
