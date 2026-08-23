#!/usr/bin/env python3
"""Static regression checks for the V8.2 nine-tower floor-plan hub."""
from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://lumi-hanoi.com"
EXPECTED = {
    "S1": ("signature", "toa-signature-1-lumi-hanoi"),
    "S2": ("signature", "toa-signature-2-lumi-hanoi"),
    "S3": ("signature", "toa-signature-3-lumi-hanoi"),
    "S5": ("signature", "toa-signature-5-lumi-hanoi"),
    "S6": ("signature", "toa-signature-6-lumi-hanoi"),
    "P1": ("prestige", "toa-prestige-1-lumi-hanoi"),
    "P2": ("prestige", "toa-prestige-2-lumi-hanoi"),
    "E1": ("elite", "toa-elite-1-lumi-hanoi"),
    "E2": ("elite", "toa-elite-2-lumi-hanoi"),
}
PHASE_URL = {
    "signature": "/lumi-signature/",
    "prestige": "/lumi-prestige/",
    "elite": "/lumi-elite/",
}
STALE_REDIRECTS = {
    "/toa-s1-lumi-hanoi/": "/toa-signature-1-lumi-hanoi/",
    "/toa-s2-lumi-hanoi/": "/toa-signature-2-lumi-hanoi/",
    "/toa-s3-lumi-hanoi/": "/toa-signature-3-lumi-hanoi/",
    "/toa-s5-lumi-hanoi/": "/toa-signature-5-lumi-hanoi/",
    "/toa-s6-lumi-hanoi/": "/toa-signature-6-lumi-hanoi/",
    "/toa-p1-lumi-hanoi/": "/toa-prestige-1-lumi-hanoi/",
    "/toa-p2-lumi-hanoi/": "/toa-prestige-2-lumi-hanoi/",
}


def read(path: str) -> str:
    p = ROOT / path
    assert p.exists(), f"missing {path}"
    return p.read_text(encoding="utf-8")


def canonical(html: str) -> str:
    match = re.search(r'<link\s+rel="canonical"\s+href="([^"]+)"', html, re.I)
    assert match, "missing canonical"
    return match.group(1)


def title(html: str) -> str:
    match = re.search(r"<title>(.*?)</title>", html, re.I | re.S)
    assert match and match.group(1).strip(), "missing title"
    return re.sub(r"\s+", " ", match.group(1)).strip()


def description(html: str) -> str:
    match = re.search(r'<meta\s+name="description"\s+content="([^"]+)"', html, re.I)
    assert match and match.group(1).strip(), "missing meta description"
    return match.group(1).strip()


def main() -> None:
    data = json.loads(read("assets/data/floor-plans.json"))
    assert set(data["towers"]) == set(EXPECTED), "tower inventory must be exactly 9 towers"
    assert sum(len(v["plans"]) for v in data["towers"].values()) == 54, "expected 54 image plan records"

    supplemental = data.get("supplemental", [])
    assert len(supplemental) == 1, "expected exactly one supplemental record"
    e2_pdf = supplemental[0]
    assert e2_pdf.get("tower") == "E2" and e2_pdf.get("floorLabel") == "Tầng 24"
    assert e2_pdf.get("sourceDriveId") == "1zqhh1L1f4Nbo4I-ecD1YbgO3y26_fdgU"

    hub = read("mat-bang-lumi-hanoi/index.html")
    sitemap_text = read("sitemap.xml")
    ET.fromstring(sitemap_text)
    netlify = read("netlify.toml")
    renderer = read("assets/js/floor-plan-tower.js")
    assert "/assets/data/floor-plans.json" in renderer
    assert "drive.google.com/thumbnail" in renderer
    assert (ROOT / "assets/css/floor-plan-hub.css").exists()

    titles: set[str] = set()
    descriptions: set[str] = set()
    for tower, (phase, slug) in EXPECTED.items():
        meta = data["towers"][tower]
        assert meta["phase"] == phase, f"{tower}: wrong phase"
        assert meta["slug"] == slug, f"{tower}: wrong slug"
        assert f"/{slug}/" in hub, f"hub missing {tower}"

        html = read(f"{slug}/index.html")
        expected_canonical = f"{SITE}/{slug}/"
        assert canonical(html) == expected_canonical, f"{tower}: wrong canonical"
        assert len(re.findall(r"<h1\b", html, re.I)) == 1, f"{tower}: expected one H1"
        assert "/mat-bang-lumi-hanoi/" in html, f"{tower}: missing hub backlink"
        assert PHASE_URL[phase] in html, f"{tower}: missing phase backlink"

        page_title = title(html)
        page_desc = description(html)
        assert page_title not in titles, f"duplicate tower title: {page_title}"
        assert page_desc not in descriptions, f"duplicate tower description: {page_desc}"
        titles.add(page_title)
        descriptions.add(page_desc)

        assert expected_canonical in sitemap_text, f"sitemap missing {tower}"
        for plan in meta["plans"]:
            for key in ("label", "anchor", "driveId", "source"):
                assert plan.get(key), f"{tower}: plan missing {key}"
            if phase == "prestige":
                asset = plan.get("asset")
                assert asset, f"{tower}: Prestige plan missing local asset"
                assert (ROOT / asset.lstrip("/")).exists(), f"{tower}: missing {asset}"

        if phase in {"signature", "prestige"}:
            assert "data-floor-plan-app" in html and f'data-tower="{tower}"' in html
            assert "/assets/js/floor-plan-tower.js" in html
        else:
            for plan in meta["plans"]:
                assert plan["driveId"] in html, f"{tower}: source ID not rendered"

    e2 = read("toa-elite-2-lumi-hanoi/index.html")
    assert e2_pdf["sourceDriveId"] in e2, "E2 floor-24 PDF missing from page"
    assert "5 nguồn mặt bằng" in e2, "E2 source-count copy is inconsistent"

    for old, new in STALE_REDIRECTS.items():
        assert f"{SITE}{old}" not in sitemap_text, f"stale URL in sitemap: {old}"
        pattern = rf'from\s*=\s*"{re.escape(old)}"[\s\S]*?to\s*=\s*"{re.escape(new)}"[\s\S]*?status\s*=\s*301'
        assert re.search(pattern, netlify), f"missing 301: {old} -> {new}"

    print("PASS: V8.2 floor-plan hub — 9 towers, 54 images, E2 floor-24 PDF, canonical/sitemap/redirect checks")


if __name__ == "__main__":
    main()
