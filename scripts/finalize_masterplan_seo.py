from pathlib import Path

HUB = Path("mat-bang-lumi-hanoi/index.html")
ELITE = Path("mat-bang-lumi-hanoi/lumi-elite/index.html")
OG = "https://lumi-hanoi.com/assets/media/masterplan/lumi-hanoi-mat-bang-tong-the-og-1200x630.webp"
ALT = "Mặt bằng tổng thể Lumi Hanoi gồm 9 tòa Signature, Prestige và Elite"

hub = HUB.read_text(encoding="utf-8")
hub = hub.replace(
    '<meta property="og:image" content="https://lumi-hanoi.com/assets/media/masterplan/lumi-hanoi-masterplan-1280.webp"><meta property="og:image:alt" content="Mặt bằng cảnh quan Lumi Signature với các tòa S1, S2, S3, S5, S6">',
    f'<meta property="og:image" content="{OG}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:type" content="image/webp"><meta property="og:image:alt" content="{ALT}">',
    1,
)
hub = hub.replace(
    '<meta name="twitter:image" content="https://lumi-hanoi.com/assets/media/masterplan/lumi-hanoi-masterplan-1280.webp">',
    f'<meta name="twitter:image" content="{OG}"><meta name="twitter:image:alt" content="{ALT}">',
    1,
)
if OG not in hub:
    raise RuntimeError("hub OG replacement failed")
HUB.write_text(hub, encoding="utf-8")

elite = ELITE.read_text(encoding="utf-8")
old = '"image":"https://lumi-hanoi.com/assets/media/elite/lumi-elite-facade.webp","primaryImageOfPage":{"@type":"ImageObject","contentUrl":"https://lumi-hanoi.com/assets/media/elite/lumi-elite-facade.webp","width":985,"height":633},'
if old in elite:
    elite = elite.replace(old, "", 1)
if elite.count('primaryImageOfPage') != 1:
    raise RuntimeError(f"Elite schema should contain exactly one primaryImageOfPage, found {elite.count('primaryImageOfPage')}")
if elite.count('"image":"https://lumi-hanoi.com/assets/media/floor-plans/lumi-elite-masterplan.webp"') != 1:
    raise RuntimeError("Elite schema masterplan image not unique")
ELITE.write_text(elite, encoding="utf-8")
