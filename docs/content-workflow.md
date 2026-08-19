# Lumi Hanoi content workflow

## Editorial standard

Publish only when there is real new information or a durable user question. “Daily SEO” is not a publishing target. Never invent inventory, price, transaction, review, progress, handover date or infrastructure completion. This is an independent portal, not CapitaLand Development's official website.

## Publication checklist

1. Search for a meaningful Lumi Hanoi development or a demonstrated reader question.
2. Prefer official CapitaLand Development/Lumi Hanoi sources; use government/planning sources for infrastructure.
3. Verify the event date, publication date and time zone/context.
4. Compare multiple credible sources when the official source does not answer the whole question.
5. Write an original synthesis. Do not copy or closely paraphrase source passages.
6. Add a **Nguồn tham khảo** section with direct links, publisher and access/publication dates.
7. Add a useful approved project image; record its origin and rights in `docs/source-map.md`.
8. Add contextual internal links, not repeated exact-match anchors.
9. Add unique title, description, canonical, Open Graph/Twitter fields and applicable structured data.
10. Add the canonical URL and truthful `lastmod` to `sitemap.xml`.
11. Check the page at 360 px and a desktop viewport; test keyboard navigation and image enlargement.
12. Run link, HTML, metadata and prohibited-language checks; then publish through review.

## Source hierarchy

1. CapitaLand Development / official Lumi Hanoi material.
2. Hanoi or other competent government/planning authorities.
3. Reputable Vietnamese newspapers.
4. Reputable real-estate research/media.
5. Supplemental sources, clearly described and never used to override a newer official source.

When sources conflict, prefer the newer authoritative source and explain the date/context. If uncertainty remains, state it or omit the claim.

## Article file template

Create an evergreen, human-readable directory under `tin-tuc/`, for example `tin-tuc/tien-do-lumi-hanoi-thang-8-2026/index.html` only when an August 2026 update actually exists.

```html
<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>[Unique title] | Lumi Hanoi</title>
  <meta name="description" content="[Specific 140–160 character summary]">
  <link rel="canonical" href="https://lumi-hanoi.com/tin-tuc/[slug]/">
  <!-- Add matching Open Graph and Twitter metadata. -->
  <!-- Add BreadcrumbList + Article JSON-LD with truthful dates. -->
  <link rel="stylesheet" href="/assets/css/site.css">
</head>
<body>
  <!-- Reuse the accessible global header. -->
  <main id="main">
    <nav aria-label="Breadcrumb">...</nav>
    <article>
      <header>
        <p>[Category] · Cập nhật [DD/MM/YYYY]</p>
        <h1>[One descriptive H1]</h1>
        <p>[Answer-first introduction]</p>
      </header>
      <figure>
        <img src="/assets/images/[descriptive-name].webp"
             width="1600" height="1000"
             alt="[Concrete description]">
        <figcaption>[What, where, date, source]</figcaption>
      </figure>
      <h2>Thông tin chính</h2>
      <p>...</p>
      <h2>Điều này có ý nghĩa gì?</h2>
      <p>Separate fact from analysis or inference.</p>
      <h2>Nguồn tham khảo</h2>
      <ul><li><a href="[direct source]">[Publisher — document]</a>, [date].</li></ul>
    </article>
  </main>
  <!-- Reuse the exact independent-site disclaimer in the footer. -->
</body>
</html>
```

## Article QA

- Exactly one H1; logical H2/H3 order.
- Title, description and canonical are unique and match the article.
- Article and breadcrumb schema parse as JSON.
- FAQ schema is included only if visible, genuine FAQ content exists.
- Every time-sensitive statement has a date and source.
- Every content image has useful alt text, intrinsic dimensions and source rights; only the LCP image is eager.
- No private sales documents or personal data are exposed.
- No `RealEstateListing` schema until real verified listings exist.
- All internal links resolve and the article is reachable from a hub/pillar.
