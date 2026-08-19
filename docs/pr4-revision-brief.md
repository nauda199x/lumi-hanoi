# PR #4 revision brief

This brief supersedes the generic “pending source access” approach currently visible in the PR.

Read first:
- `docs/source-package-v1.md`
- existing `docs/source-map.md`

Then revise PR #4 in place. Do not open a second PR.

## Required corrections before merge

### A. Replace generic methodology copy with real project content

Public pages must answer user questions about Lumi Hanoi. They should not explain the editorial process.

Remove or rewrite public phrases such as:
- “website chưa công bố các thuộc tính chi tiết…”
- “tại lần rà soát…”
- “nội dung sẽ được kiểm tra…”
- “thư viện sẽ được xuất bản thế nào…”
- “chỉ bổ sung sau khi hoàn tất nhật ký nguồn…”

Keep source/audit methodology inside `/docs/` only.

### B. Rewrite the three phase pages so they are materially different

`/lumi-signature/`
- establish the 5 Signature towers supported by source inventory: S1, S2, S3, S5, S6
- explain product mix and verified area ranges
- include an apartment-type/area table
- explain typical-floor source structure without inventing tower totals
- include expected handover examples with “or equivalent” caveat
- internally link to masterplan, amenities, handover and future market pages

`/lumi-prestige/`
- establish P1/P2 from source inventory
- describe the available typical-floor ranges from the named files in source-package
- use verified Prestige differentiators from training material: Safety & Privacy, Facilities for Community, Sustainability, Residential Design; Aurora 50m lap pool; close-to-parking-podium positioning; upgraded handover specs; variety of unit types
- include the verified 1BR example 42.2 sqm NFA / 46.2 sqm GFA
- keep wording factual, not copied marketing slogans

`/lumi-elite/`
- establish Elite 1 / Elite 2 and legal codes Z29M.1 / Z29.1
- explain developer positioning as the most prestigious subphase and lowest-density enclave, attributed to the dated eBrochure
- include unit-mix overview: 1–3BR, 4BR duplex, penthouse
- include a compact verified area table using source-package examples
- include a curated amenity section (not the entire huge list)
- clearly label brochure amenities as planned/rendered until operational status is verified

### C. Fix project-wide exact facts

Where the detailed article cites the official Project Introduction PDF, use:
- 5.6 ha
- 3,950 apartments
- 9 towers
- 29–35 floors
- construction start Q4/2023

Do not silently change 3,950 to “about 4,000” in detailed factual tables. The homepage may use a rounded marketing snapshot only if labeled approximate.

### D. Restore useful progress information with dated context

Do not delete previously sourced progress simply because it is older.

The progress page should:
- preserve the official June 2026 progress as a dated historical snapshot if the existing page already has an official source
- separately state that newer progress should be added only with a newer dated official source
- never present June 2026 as “current” without the date
- never convert construction progress into a handover promise

### E. Build the commercial URLs now

Create and add to sitemap/internal navigation:
- `/mua-ban-lumi-hanoi/`
- `/cho-thue-lumi-hanoi/`
- `/ky-gui-lumi-hanoi/`

Current stage copy:
- useful explanation of how the market is expected to form around handover
- clear statement that verified inventory is not yet displayed
- no fake counts, prices or listings

These slugs are intended to remain permanent when the marketplace launches.

### F. Make `/tin-tuc/` a real content hub

The page should look like a publishable news/knowledge hub, not an article about editorial philosophy.

Create visible sections/cards for:
- Tiến độ Lumi Hanoi
- Hạ tầng khu vực
- Lumi Signature
- Lumi Prestige
- Lumi Elite
- Mua bán
- Cho thuê
- Hướng dẫn cư dân

Do not create empty indexable category URLs yet. Keep categories as filters/labels on the hub until multiple real posts exist.

Create at least 2 useful starter articles from already verified material, for example:
1. `/tin-tuc/lumi-hanoi-3-phan-khu-signature-prestige-elite/`
2. `/tin-tuc/cach-doc-mat-bang-lumi-hanoi/`

These articles must be substantive and source-backed, not thin placeholders.

### G. HTML maintainability

Reformat public HTML files into readable multi-line HTML. Do not minify source code in Git. Netlify can handle optimization later if needed.

### H. Imagery honesty

Do not present CSS abstract-building blocks as if they are Lumi project imagery.

If actual source images cannot be downloaded into the repo in this task:
- keep the visual system premium but neutral
- remove copy claiming image work is complete
- explicitly list real-image integration as pending in the PR summary

### I. SEO / QA

Preserve:
- canonical URLs
- one H1 per page
- unique titles/descriptions
- BreadcrumbList / Article schema where appropriate
- static HTML crawlability
- non-www canonical host
- sitemap coverage

Add commercial pages and starter news articles to sitemap.

Before finishing:
- check internal links
- check HTML validity
- check duplicate titles/descriptions
- check mobile overflow
- check no public `V1`, `placeholder`, `TODO`, `Lorem`, “pending verification” implementation-language remains

## Done condition

PR #4 is ready for reviewer re-check only when:
- phase pages contain real differentiated data from `source-package-v1.md`
- commercial URLs exist
- news hub has at least two real starter articles
- public copy no longer reads like an internal QA document
- source code is readable
- no fake listings/prices/handover claims are introduced
