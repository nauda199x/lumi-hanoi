const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");

const read = path => fs.readFileSync(path, "utf8");

test("new submissions receive a private fragment management link", () => {
  const api = read("assets/js/marketplace-api.js");
  const form = read("assets/js/marketplace-form.js");
  assert.match(api, /randomManagementToken/);
  assert.match(api, /sha256Hex/);
  assert.match(api, /edit_token_hash/);
  assert.match(api, /management_token/);
  assert.match(form, /\/quan-ly-tin-lumi-hanoi\/#token=/);
  assert.match(form, /Sao chép link/);
});

test("management page is private, noindex and uses the token edge function", () => {
  const html = read("quan-ly-tin-lumi-hanoi/index.html");
  const js = read("assets/js/listing-manage.js");
  assert.match(html, /noindex,nofollow,noarchive/);
  assert.match(html, /name="referrer" content="no-referrer"/);
  assert.match(html, /data-manage-form/);
  assert.match(js, /manageListing\("get",token\)/);
  assert.match(js, /manageListing\("update",token/);
  assert.doesNotMatch(js, /SERVICE_ROLE/i);
});

test("edge function validates a high-entropy token and never returns its hash", () => {
  const edge = read("supabase/functions/manage-listing/index.ts");
  assert.match(edge, /SUPABASE_SERVICE_ROLE_KEY/);
  assert.match(edge, /SHA-256/);
  assert.match(edge, /tokenPattern/);
  assert.match(edge, /safeListing/);
  assert.match(edge, /edit_token_hash: _secret/);
  assert.match(edge, /status = "pending"|patch\.status = "pending"/);
});

test("database schema stores only the token hash without exposing it through anon select grants", () => {
  const schema = read("supabase/marketplace-schema.sql");
  assert.match(schema, /edit_token_hash text/);
  assert.match(schema, /listings_edit_token_hash_uidx/);
  assert.match(schema, /contact_public,edit_token_hash\s*\n\) on public\.listings to anon;/);
  const selectGrant = schema.match(/grant select \([\s\S]*?\) on public\.listings to anon;/)?.[0] || "";
  assert.doesNotMatch(selectGrant, /edit_token_hash/);
});
