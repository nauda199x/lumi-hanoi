#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

required_files = [
    "assets/css/marketplace.css",
    "assets/js/marketplace-config.js",
    "assets/js/marketplace-api.js",
    "assets/js/marketplace-list.js",
    "assets/js/marketplace-form.js",
    "assets/js/marketplace-detail.js",
    "assets/js/marketplace-admin.js",
    "assets/js/marketplace-static-status.js",
    "giao-dich-lumi-hanoi/index.html",
    "dang-tin-lumi-hanoi/index.html",
    "tin-dang-lumi-hanoi/index.html",
    "admin/index.html",
    "supabase/marketplace-schema.sql",
    "scripts/generate_marketplace_seo.py",
    ".github/workflows/sync-marketplace-seo.yml",
    "sitemap-tin-dang.xml",
]
for relative in required_files:
    assert (ROOT / relative).is_file(), f"Missing {relative}"

sale = (ROOT / "mua-ban-lumi-hanoi/index.html").read_text(encoding="utf-8")
rent = (ROOT / "cho-thue-lumi-hanoi/index.html").read_text(encoding="utf-8")
submit = (ROOT / "dang-tin-lumi-hanoi/index.html").read_text(encoding="utf-8")
admin = (ROOT / "admin/index.html").read_text(encoding="utf-8")
detail = (ROOT / "tin-dang-lumi-hanoi/index.html").read_text(encoding="utf-8")
schema = (ROOT / "supabase/marketplace-schema.sql").read_text(encoding="utf-8")
config = (ROOT / "assets/js/marketplace-config.js").read_text(encoding="utf-8")
api = (ROOT / "assets/js/marketplace-api.js").read_text(encoding="utf-8")
list_js = (ROOT / "assets/js/marketplace-list.js").read_text(encoding="utf-8")
form_js = (ROOT / "assets/js/marketplace-form.js").read_text(encoding="utf-8")
detail_js = (ROOT / "assets/js/marketplace-detail.js").read_text(encoding="utf-8")
admin_js = (ROOT / "assets/js/marketplace-admin.js").read_text(encoding="utf-8")
market_css = (ROOT / "assets/css/marketplace.css").read_text(encoding="utf-8")
site_css = (ROOT / "assets/css/site.css").read_text(encoding="utf-8")
home = (ROOT / "index.html").read_text(encoding="utf-8")
transaction_hub = (ROOT / "giao-dich-lumi-hanoi/index.html").read_text(encoding="utf-8")
site_js = (ROOT / "assets/js/site.js").read_text(encoding="utf-8")
robots = (ROOT / "robots.txt").read_text(encoding="utf-8")
marketplace_sitemap = (ROOT / "sitemap-tin-dang.xml").read_text(encoding="utf-8")
seo_generator = (ROOT / "scripts/generate_marketplace_seo.py").read_text(encoding="utf-8")
seo_workflow = (ROOT / ".github/workflows/sync-marketplace-seo.yml").read_text(encoding="utf-8")

assert 'data-listing-type="sale"' in sale and 'marketplace-list.js' in sale
assert 'data-listing-type="rent"' in rent and 'marketplace-list.js' in rent
assert all(('Đang tải…' in page) or ('MARKETPLACE-STATIC-LISTINGS:START' in page) for page in (sale, rent)), "Hub HTML must show loading copy or prerendered listing data"
assert 'data-empty-benefits' in sale and 'data-empty-benefits' in rent, "Empty states should explain the real posting benefits"
assert 'data-marketplace-submit' in submit and 'name="contact_public"' in submit
assert 'name="website"' in submit, "Submission form needs a honeypot"
assert all('Shop chân đế' in page for page in (submit, sale, rent, admin)), "Shop listings must work in form, filters and admin"
assert all(f'<option>{floor}</option>' in submit for floor in ("Thấp", "Trung", "Cao")), "Floor must use three privacy-safe bands"
for removed_name in ("unit_code", "direction", "view_text", "poster_type", "contact_zalo", "contact_email"):
    assert f'name="{removed_name}"' not in submit, f"Submission form must not collect {removed_name}"
    assert f'value("{removed_name}")' not in form_js, f"Submission payload must not send {removed_name}"
assert 'Số điện thoại (Zalo) *' in submit
assert 'data-form-progress' in submit and submit.count('data-form-step=') == 4, "Submission form needs a four-step progress indicator"
assert 'data-mobile-submit' in submit, "Submission form needs a mobile sticky submit action"
assert 'data-phone-help' in submit, "Phone input needs realtime validation help"
assert 'lumi-marketplace-draft-v2' in form_js and 'localStorage.setItem' in form_js and 'restoreDraft' in form_js, "Submission form must autosave and restore a local draft"
assert 'visualViewport' in form_js and 'is-keyboard' in form_js, "Mobile sticky CTA must avoid the on-screen keyboard"
assert 'Đang tối ưu ảnh' in form_js and 'isSubmitting' in form_js, "Submission needs visible upload progress and duplicate-submit protection"
assert 'data-legal-field' in submit and '.field[hidden]{display:none}' in market_css, "Rental legal status must really stay hidden"
assert 'data-marketplace-admin' in admin and 'noindex,nofollow' in admin
assert 'data-listing-detail' in detail and 'noindex,follow' in detail
assert 'detail-shell--portal' in detail and 'detail-mobile-contact' in detail, "Dynamic listing detail must use the portal layout and mobile CTA"
assert 'data-detail-price-per-sqm' in detail, "Sale detail should expose price per sqm when available"
assert 'detail-gallery-track' in detail_js and 'detail-gallery-counter' in detail_js, "Dynamic detail gallery must support horizontal swiping with a counter"
assert 'detail-gallery-nav--prev' in detail_js and 'detail-gallery-nav--next' in detail_js, "Desktop detail gallery needs previous/next controls"
assert 'ArrowLeft' in detail_js and 'ArrowRight' in detail_js, "Desktop gallery should support keyboard arrow navigation"
assert 'detail-gallery-nav--prev' in market_css and 'detail-gallery-nav--next' in market_css, "Desktop gallery arrows need visible styling"
assert 'detail-gallery-nav--prev' in (ROOT / "assets/js/marketplace-static-status.js").read_text(encoding="utf-8"), "Static SEO listings need desktop gallery controls"
assert 'marketplace-detail.js?v=20260902-procopy' in detail, "Dynamic detail page must use the current detail script cache key"
assert 'marketplace-lightbox.js?v=20260902-fullimage' in detail and 'marketplace-lightbox.js?v=20260902-fullimage' in seo_generator, "Dynamic and generated detail pages must use the current full-image lightbox cache key"
assert 'DETAIL PORTAL UX 2026-08-29' in market_css and 'scroll-snap-type:x mandatory' in market_css, "Marketplace detail CSS must keep swipe-first gallery behavior"
assert 'detail-shell detail-shell--portal' in seo_generator and 'detail-mobile-contact' in seo_generator, "Generated SEO listing pages must share the same portal layout"
assert 'detail-gallery-track' in seo_generator and 'data-static-gallery-counter' in seo_generator, "Generated listing pages must include swipe gallery markup"
assert 'data-detail-direction' not in detail
assert 'data-detail-poster' in detail and 'poster_name' in detail_js, "Approved listing detail must show the poster name entered in the form"
assert 'listing.contact_zalo' not in detail_js, "Public Zalo link must reuse the contact phone"
assert "enable row level security" in schema.lower()
assert "listings_anon_submit_pending" in schema and "listings_admin_manage" in schema
assert "can_upload_pending_image" in schema, "Storage uploads must belong to a pending listing"
assert "create or replace function private.is_public_listing" in schema, "Public image RLS needs a private visibility helper"
assert "using (private.is_public_listing(listing_id))" in schema, "Image reads must not require broad listings table access"
assert "revoke all on public.admin_users,public.listings" in schema
assert "create or replace function private.is_admin" in schema
assert "create or replace function public.is_admin" not in schema, "SECURITY DEFINER helpers must not live in an exposed schema"
assert "grant all on public.admin_users" not in schema, "Authenticated access must use least privilege"
assert "alter table public.listings set schema archive" in schema, "Existing empty scaffold must be preserved, not deleted"
assert "drop table" not in schema.lower(), "Marketplace setup must not destructively drop project tables"
assert "notify pgrst, 'reload schema'" in schema
assert "'Shop chân đế'" in schema and "listings_unit_type_check" in schema
assert "floor_label in ('Thấp','Trung','Cao')" in schema
assert "alter column poster_type drop not null" in schema
anon_insert_grant = schema.split("grant insert (", 1)[1].split(") on public.listings to anon;", 1)[0]
for removed_column in ("unit_code", "direction", "view_text", "poster_type", "contact_zalo", "contact_email"):
    assert removed_column not in anon_insert_grant, f"Anonymous insert grant must not include {removed_column}"
assert 'select:"id,slug,listing_code,listing_type,title,description' in api, "Public detail must use an explicit safe column list"
assert "const listingUrl=listing=>" in api, "Marketplace API must expose clean listing URLs"
assert 'slide.href=cleanUrl' in list_js and 'titleLink.href=cleanUrl' in list_js, "Listing cards must keep clean static SEO URLs in anchors"
assert 'listing-card--marketplace' in list_js and 'listing-card-gallery-track' in list_js, "Marketplace list must render rich horizontal/mobile carousel cards"
assert 'listing-card-poster' in list_js and 'listing-card-action--call' in list_js and 'listing-card-action--zalo' in list_js, "Cards must expose poster and direct contact actions"
assert 'marketplace-mobile-controls' in list_js and 'marketplace-filter-backdrop' in list_js, "Mobile list needs compact filter controls and bottom sheet"
assert 'mobileSort' not in list_js and 'filters.sort' not in list_js, "Client-side sorting must not override system ranking"
assert 'order:"is_featured.desc,sort_priority.desc,approved_at.desc"' in api, "System ranking must keep featured and paid-priority positions first"
assert 'marketplace-load-more' in list_js and 'pageSize=()=>mobileQuery.matches?8:10' in list_js, "Long listing sets must progressively reveal cards"
assert 'pricePerSqm' in list_js and 'timeAgo' in list_js, "Sale cards need price per sqm and listing recency"
assert all('name="area"' in page for page in (sale,rent)), "Sale and rent filters need area controls"
assert all('name="sort"' not in page for page in (sale,rent)), "Public marketplace must not expose sorting that can override paid priority"
assert all('marketplace-list.js?v=20260903-tower-filter' in page for page in (sale,rent)), "Marketplace hubs must use the current list script cache key"
assert 'MARKETPLACE LIST SUPER UX 2026-08-29' in market_css, "Marketplace list must include the new responsive UX stylesheet"
assert 'grid-template-columns:minmax(360px,.96fr) minmax(0,1.22fr)' in market_css, "Desktop cards must use horizontal marketplace layout"
assert 'scroll-snap-type:x mandatory' in market_css and '.marketplace-toolbar.is-mobile-open' in market_css, "Mobile cards need swipe gallery and filter bottom sheet"
assert 'description,poster_name,contact_phone' in api and 'created_at,listing_images' in api, "Public list query must include rich-card metadata"
assert "/tin-dang-lumi-hanoi/?slug=" not in list_js, "Public listing cards must not use query-string detail URLs"
assert "sitemap-tin-dang.xml" in robots, "robots.txt must advertise marketplace sitemap"
assert "indexable(listing)" in seo_generator and "noindex,follow" in seo_generator, "Thin approved listings must be generated but excluded from index"
assert "schedule:" in seo_workflow and "*/5 * * * *" in seo_workflow, "Marketplace SEO sync must refresh every 5 minutes"
assert "generate_marketplace_seo.py" in seo_workflow and "git push origin HEAD:main" in seo_workflow
assert "<urlset" in marketplace_sitemap, "Marketplace sitemap must be a valid URL set"
assert "deleteListing" in api and 'body:{prefixes:imagePaths}' in api, "Admin deletion must clean Storage objects first"
assert "Xóa vĩnh viễn" in admin_js and "deleteAndReload" in admin_js, "Admin UI needs a confirmed permanent-delete action"
assert "service-role" in config.lower() and "supabasePublishableKey" in config
assert "service_role" not in config
assert home.index('href="/tong-quan-lumi-hanoi/">Tổng quan</a>') < home.index("<summary>Giao dịch</summary>") < home.index('href="/mat-bang-lumi-hanoi/">Mặt bằng</a>')
assert '<a class="btn" href="/giao-dich-lumi-hanoi/">Giao dịch</a>' in home
assert "20260829-hero-click" in home, "Homepage must bust the stale hero stylesheet cache"
assert ".home-hero-media,.home-hero:before,.home-hero:after{pointer-events:none}" in site_css
assert ".home-hero .container{z-index:2}" in site_css, "Hero actions must stay above decorative overlays"
assert 'href="/mua-ban-lumi-hanoi/"' in transaction_hub
assert 'href="/cho-thue-lumi-hanoi/"' in transaction_hub
assert 'href="/dang-tin-lumi-hanoi/"' in transaction_hub
assert '<h2><a class="transaction-path-link" href="/mua-ban-lumi-hanoi/">Tìm căn để mua</a></h2>' in transaction_hub
assert '<h2><a class="transaction-path-link" href="/cho-thue-lumi-hanoi/">Tìm căn để thuê</a></h2>' in transaction_hub
assert "Mua bán và cho thuê căn hộ Lumi Hanoi" in transaction_hub, "Transaction hub must keep the professional marketplace heading"
assert "hoặc anh/chị không có quyền xóa" in api and "hoặc anh không có quyền xóa" not in api
assert "Cẩm nang giao dịch" not in home
assert "overviewLink.after(transactionDropdown)" in site_js, "Every legacy page must prioritize the transaction dropdown after Overview"

print("Marketplace V1 QA passed: public lists, submission, detail, admin and RLS schema verified.")
