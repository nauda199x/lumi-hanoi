# V8.2 floor-plan architecture audit

Updated: 2026-08-23

This document supersedes older floor-plan URL notes where they conflict with V8.2. The machine-readable source of truth is `assets/data/floor-plans.json`.

## Canonical intent ownership

- `/mat-bang-lumi-hanoi/` owns the broad project-level “mặt bằng Lumi Hanoi” lookup intent.
- Signature tower intent is owned by `/toa-signature-1-lumi-hanoi/`, `/toa-signature-2-lumi-hanoi/`, `/toa-signature-3-lumi-hanoi/`, `/toa-signature-5-lumi-hanoi/`, `/toa-signature-6-lumi-hanoi/`.
- Prestige tower intent is owned by `/toa-prestige-1-lumi-hanoi/` and `/toa-prestige-2-lumi-hanoi/`.
- Elite tower intent is owned by `/toa-elite-1-lumi-hanoi/` and `/toa-elite-2-lumi-hanoi/`.
- Floor groups remain in-page anchors, not separate indexable URLs.
- `/layout-can-ho-lumi-prestige/` owns the Prestige unit-layout library intent and must not compete with tower-floor pages.
- Phase pages `/lumi-signature/`, `/lumi-prestige/`, `/lumi-elite/` remain phase profiles, while bedroom pages remain product-type guides.

## Redirected legacy tower paths

The legacy short paths `/toa-s1-lumi-hanoi/`, `/toa-s2-lumi-hanoi/`, `/toa-s3-lumi-hanoi/`, `/toa-s5-lumi-hanoi/`, `/toa-s6-lumi-hanoi/`, `/toa-p1-lumi-hanoi/`, and `/toa-p2-lumi-hanoi/` are not canonical and are excluded from the sitemap. Netlify permanently redirects them to the V8.2 canonical paths.

## Media/source status

- Prestige P1/P2: eight verified floor-plan WebP derivatives are stored locally under `assets/media/prestige/floor-plans/` and mapped in the manifest.
- Signature S1/S2/S3/S5/S6: verified Drive file IDs and exact source groupings are recorded in the manifest; the current V8.2 pages render owner-trusted Drive thumbnails and link to the source file.
- Elite E1/E2: verified brochure-page Drive IDs are recorded and rendered; E2 floor 24 remains a separate source PDF (`1zqhh1L1f4Nbo4I-ecD1YbgO3y26_fdgU`).
- No competitor floor-plan imagery is used.

## Current technical-debt boundary

V8.2 intentionally does not create per-floor crawlable URLs or invent unit-number-to-layout/hướng mappings. A future localization pass may move Signature/Elite technical images from Drive delivery into local WebP assets; when that happens, preserve the existing tower canonicals, anchors and source provenance.

## Regression gate

`scripts/qa_floorplans_v8_2.py` validates the exact nine-tower inventory, 54 image records plus the E2 floor-24 PDF, canonical URLs, hub↔tower↔phase links, Prestige local assets, sitemap membership and legacy redirects. `.github/workflows/repo-qa.yml` runs the full repository QA suite for pull requests and pushes to `main`.
