from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ROOM_PAGES = [
    ROOT / "can-ho-1-phong-ngu-lumi-hanoi/index.html",
    ROOT / "can-ho-2-phong-ngu-lumi-hanoi/index.html",
    ROOT / "can-ho-3-phong-ngu-lumi-hanoi/index.html",
]

TOWER_PAGES = {
    "Signature": ["s1", "s2", "s3", "s5", "s6"],
    "Prestige": ["p1", "p2"],
    "Elite": ["e1", "e2"],
}


def fail(message: str) -> None:
    raise SystemExit(message)


def text(path: Path) -> str:
    if not path.is_file():
        fail(f"Missing required page: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def img_sources(fragment: str) -> list[str]:
    return re.findall(r'<img\b[^>]*\bsrc="([^"]+)"', fragment, flags=re.I)


def assert_core_seo(path: Path, html: str) -> None:
    for needle in ("<title>", "<h1>", 'rel="canonical"', 'application/ld+json'):
        if needle not in html:
            fail(f"{path.relative_to(ROOT)} missing {needle}")


# Room-type pages must stay ordered Signature -> Prestige -> Elite and must not
# accidentally display images from a different phase inside each phase section.
for path in ROOM_PAGES:
    html = text(path)
    assert_core_seo(path, html)
    markers = ['id="signature"', 'id="prestige"', 'id="elite"']
    if not all(marker in html for marker in markers):
        fail(f"{path.relative_to(ROOT)} missing one or more phase sections")
    s, p, e = (html.index(marker) for marker in markers)
    if not s < p < e:
        fail(f"{path.relative_to(ROOT)} phase order is not Signature -> Prestige -> Elite")

    sections = {
        "signature": html[s:p],
        "prestige": html[p:e],
        "elite": html[e:],
    }
    forbidden = {
        "signature": ("/assets/media/prestige/", "/assets/media/elite/"),
        "prestige": ("/assets/media/signature/", "/assets/media/elite/"),
        "elite": ("/assets/media/signature/", "/assets/media/prestige/"),
    }
    for phase, fragment in sections.items():
        for src in img_sources(fragment):
            if any(src.startswith(prefix) for prefix in forbidden[phase]):
                fail(
                    f"{path.relative_to(ROOT)} uses wrong-phase image in {phase}: {src}"
                )

# Signature source registry must be exactly 51 records and every source must
# resolve to a committed local asset. This includes authenticated/private Drive
# sources: private availability is never a reason to skip the local file.
registry_items: list[dict] = []
for registry in (
    ROOT / "assets/data/drive-unit-layout-import.json",
    ROOT / "assets/data/drive-unit-layout-import-extra.json",
):
    registry_items.extend(json.loads(text(registry))["items"])

signature_items = [item for item in registry_items if item.get("phase") == "signature"]
if len(signature_items) != 51:
    fail(f"Expected 51 Signature registry records, got {len(signature_items)}")

local_assets = [item["localAsset"] for item in signature_items]
if len(local_assets) != len(set(local_assets)):
    fail("Duplicate Signature localAsset entries in registry")
for asset in local_assets:
    path = ROOT / asset
    if not path.is_file() or path.stat().st_size < 10_000:
        fail(f"Missing/invalid Signature local asset: {asset}")

# The public Signature library must be local-only and keep the six Duplex files
# matched to their authoritative registry names. This catches the prior DL-04 /
# DL-05 label swap as well as regressions back to Drive thumbnails.
library_path = ROOT / "layout-can-ho-lumi-signature/index.html"
library = text(library_path)
assert_core_seo(library_path, library)
if "drive.google.com/thumbnail" in library:
    fail("Signature layout library still depends on Drive thumbnails")
match = re.search(r"const signatureLayouts=(\[.*?\]);const esc=", library, flags=re.S)
if not match:
    fail("Cannot parse Signature layout catalog")
layouts = json.loads(match.group(1))
if len(layouts) != 51:
    fail(f"Signature library contains {len(layouts)} records, expected 51")
if len({item.get("asset") for item in layouts}) != 51:
    fail("Signature library local asset references are not unique")

expected_duplex = {
    f"Duplex DL-{number:02d}": f"/assets/media/signature/unit-layouts/signature-duplex-dl-{number:02d}.webp"
    for number in range(1, 7)
}
actual_duplex = {
    item["name"]: item["asset"] for item in layouts if item.get("bedrooms") == "4"
}
if actual_duplex != expected_duplex:
    fail(f"Signature Duplex mapping mismatch: {actual_duplex}")

for anchor in ("one-bedroom", "two-bedroom", "three-bedroom", "duplex"):
    if f'id="{anchor}"' not in library:
        fail(f"Signature library missing #{anchor} anchor")

# The 9 tower pages are part of the primary information architecture. Guard
# their existence and minimum SEO/indexing structure, plus links to all three
# phase guides in the shared navigation.
for phase, towers in TOWER_PAGES.items():
    phase_slug = phase.lower()
    for tower in towers:
        path = ROOT / f"mat-bang-lumi-hanoi/lumi-{phase_slug}/{tower}/index.html"
        html = text(path)
        assert_core_seo(path, html)
        expected_canonical = f'https://lumi-hanoi.com/mat-bang-lumi-hanoi/lumi-{phase_slug}/{tower}/'
        if expected_canonical not in html:
            fail(f"{path.relative_to(ROOT)} has wrong/missing canonical")
        for href in ("/lumi-signature/", "/lumi-prestige/", "/lumi-elite/"):
            if f'href="{href}"' not in html:
                fail(f"{path.relative_to(ROOT)} missing phase navigation link {href}")

# Hub must expose all nine tower destinations and the three phase guides.
hub_path = ROOT / "mat-bang-lumi-hanoi/layout-can-ho-lumi-hanoi/index.html"
hub = text(hub_path)
assert_core_seo(hub_path, hub)
for phase, towers in TOWER_PAGES.items():
    phase_slug = phase.lower()
    if f'href="/lumi-{phase_slug}/"' not in hub:
        fail(f"Layout hub missing {phase} guide link")
    for tower in towers:
        href = f'/mat-bang-lumi-hanoi/lumi-{phase_slug}/{tower}/'
        if f'href="{href}"' not in hub:
            fail(f"Layout hub missing tower link {href}")

print(
    "Layout phase integrity QA OK: 51/51 Signature assets local, Duplex mapping exact, "
    "1PN/2PN/3PN phase images isolated, and all 9 tower pages + hub SEO/navigation validated."
)
