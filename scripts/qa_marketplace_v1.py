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
    "giao-dich-lumi-hanoi/index.html",
    "dang-tin-lumi-hanoi/index.html",
    "tin-dang-lumi-hanoi/index.html",
    "admin/index.html",
    "supabase/marketplace-schema.sql",
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
form_js = (ROOT / "assets/js/marketplace-form.js").read_text(encoding="utf-8")
detail_js = (ROOT / "assets/js/marketplace-detail.js").read_text(encoding="utf-8")
admin_js = (ROOT / "assets/js/marketplace-admin.js").read_text(encoding="utf-8")
market_css = (ROOT / "assets/css/marketplace.css").read_text(encoding="utf-8")
site_css = (ROOT / "assets/css/site.css").read_text(encoding="utf-8")
home = (ROOT / "index.html").read_text(encoding="utf-8")
transaction_hub = (ROOT / "giao-dich-lumi-hanoi/index.html").read_text(encoding="utf-8")
site_js = (ROOT / "assets/js/site.js").read_text(encoding="utf-8")

assert 'data-listing-type="sale"' in sale and 'marketplace-list.js' in sale
assert 'data-listing-type="rent"' in rent and 'marketplace-list.js' in rent
assert 'data-marketplace-submit' in submit and 'name="contact_public"' in submit
assert 'name="website"' in submit, "Submission form needs a honeypot"
assert all('Shop chân đế' in page for page in (submit, sale, rent, admin)), "Shop listings must work in form, filters and admin"
assert all(f'<option>{floor}</option>' in submit for floor in ("Thấp", "Trung", "Cao")), "Floor must use three privacy-safe bands"
for removed_name in ("unit_code", "direction", "view_text", "poster_type", "contact_zalo", "contact_email"):
    assert f'name="{removed_name}"' not in submit, f"Submission form must not collect {removed_name}"
    assert f'value("{removed_name}")' not in form_js, f"Submission payload must not send {removed_name}"
assert 'Số điện thoại (Zalo) *' in submit
assert 'data-legal-field' in submit and '.field[hidden]{display:none}' in market_css, "Rental legal status must really stay hidden"
assert 'data-marketplace-admin' in admin and 'noindex,nofollow' in admin
assert 'data-listing-detail' in detail and 'noindex,follow' in detail
assert 'data-detail-direction' not in detail and 'data-detail-poster' not in detail
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
assert "Anh/chị đang muốn mua hay thuê?" in transaction_hub and "Anh đang muốn mua hay thuê?" not in transaction_hub
assert "hoặc anh/chị không có quyền xóa" in api and "hoặc anh không có quyền xóa" not in api
assert "Cẩm nang giao dịch" not in home
assert "overviewLink.after(transactionDropdown)" in site_js, "Every legacy page must prioritize the transaction dropdown after Overview"

print("Marketplace V1 QA passed: public lists, submission, detail, admin and RLS schema verified.")
