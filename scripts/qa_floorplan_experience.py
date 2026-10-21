#!/usr/bin/env python3
"""Protect canonical, indexing and floorplan source content during UX upgrades."""
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HUB=ROOT/"mat-bang-lumi-hanoi/index.html"
LAYOUT=ROOT/"mat-bang-lumi-hanoi/layout-can-ho-lumi-hanoi/index.html"
TOWERS={"signature":["s1","s2","s3","s5","s6"],"prestige":["p1","p2"],"elite":["e1","e2"]}

def read(path):
    return path.read_text(encoding="utf-8")

def seo(page,canonical):
    html=read(page)
    assert re.search(r'<link\s+rel="canonical"\s+href="'+re.escape(canonical)+r'"',html),str(page)
    assert len(re.findall(r'<h1\b',html,re.I))==1,str(page)
    assert '<meta name="robots" content="index,follow' in html,str(page)
    assert '<title>' in html and '<meta name="description"' in html,str(page)
    for raw in re.findall(r'<script\s+type="application/ld\+json"[^>]*>(.*?)</script>',html,re.S):
        json.loads(raw)
    return html

def main():
    root="https://lumi-hanoi.com/"
    hub=seo(HUB,root+"mat-bang-lumi-hanoi/")
    layout=seo(LAYOUT,root+"mat-bang-lumi-hanoi/layout-can-ho-lumi-hanoi/")
    assert all(f'id="{x}"' in hub for x in ("layout-all","tower-all","signature","prestige","elite"))
    assert hub.index('id="tower-all"') < hub.index('id="signature"') < hub.index('id="phase-unit-layouts"'),"Tower list must precede secondary galleries"
    assert 'class="cutaway-teaser"' not in hub,"AI illustration is not part of the core floor lookup"
    assert hub.index('id="signature"') < hub.index('id="prestige"') < hub.index('id="elite"')
    assert layout.index('id="signature"') < layout.index('id="prestige"') < layout.index('id="elite"') < layout.index('class="layout-seo-article"')
    assert 'layout-phase-jump' in layout and 'layout-type-jump' in layout
    for segment in ['can-ho-1-phong-ngu-lumi-hanoi','can-ho-2-phong-ngu-lumi-hanoi','can-ho-3-phong-ngu-lumi-hanoi','can-ho-4-phong-ngu-lumi-hanoi']:
        assert f'/{segment}/' in hub and f'/{segment}/' in layout
    manifest=json.loads(read(ROOT/"assets/data/floor-plans.json"))
    assert len(manifest['towers'])==9
    assert sum(len(t['plans']) for t in manifest['towers'].values())==65
    for phase,codes in TOWERS.items():
        for code in codes:
            path=f"mat-bang-lumi-hanoi/lumi-{phase}/{code}/"
            page=seo(ROOT/path/"index.html",root+path)
            assert f'/{path}' in hub and f'/{path}' in layout
            for plan in manifest['towers'][code.upper()]['plans']:
                assert f'href="#{plan["anchor"]}"' in page, (code,plan["anchor"])
            if phase=="elite":
                assert 'elite-floor-viewer.js?v=20261021-ux1' in page
                assert 'data-primary-floor-plan' in page
            else:
                assert 'floor-plan-tower.js?v=20261021-ux1' in page
    viewer=read(ROOT/"assets/js/floor-plan-tower.js")
    css=read(ROOT/"assets/css/floor-plan-explorer.css")
    assert "app.classList.add('floor-explorer-ready')" in viewer
    assert "[data-floor-plan-app].floor-explorer-ready .floor-plan-section" in css
    assert ".elite-floor-ready .floor-plan-section.is-active" in css
    assert "data-floor-group-select" in viewer and "data-floor-open" in viewer
    print("PASS: floorplan UX — 9 towers / 65 groups, canonical + indexation + schema + SEO text retained")

if __name__=="__main__":
    main()
