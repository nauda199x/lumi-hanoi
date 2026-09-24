const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");

const read = path => fs.readFileSync(path, "utf8");

test("listing form prepares images ahead of submit and caps transfer size", () => {
  const config = read("assets/js/marketplace-config.js");
  const form = read("assets/js/marketplace-form.js");
  assert.match(config, /targetImageBytes:\s*1\.4 \* 1024 \* 1024/);
  assert.match(config, /targetImageMaxDimension:\s*1920/);
  assert.match(form, /prewarmSelectedImages/);
  assert.match(form, /getPreparedFiles\(selectedFiles\)/);
  assert.match(form, /targetImageBytes/);
});

test("listing images upload with bounded concurrency instead of a serial upload loop", () => {
  const config = read("assets/js/marketplace-config.js");
  const form = read("assets/js/marketplace-form.js");
  assert.match(config, /imageUploadConcurrency:\s*3/);
  assert.match(form, /mapWithConcurrency\(files,uploadConcurrency/);
  assert.match(form, /navigator\.connection\?\.saveData/);
  assert.doesNotMatch(form, /for\(let index=0;index<files\.length;index\+\+\)[\s\S]{0,300}uploadImage/);
});

test("image metadata is inserted in one batch with a safe sequential fallback", () => {
  const api = read("assets/js/marketplace-api.js");
  const form = read("assets/js/marketplace-form.js");
  assert.match(api, /const addListingImages=/);
  assert.match(api, /body:rows/);
  assert.match(form, /await api\.addListingImages\(listing\.id,successful\)/);
  assert.match(form, /Bulk image metadata insert failed; falling back/);
  assert.match(form, /await api\.addListingImage/);
});
