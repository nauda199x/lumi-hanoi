import { test } from 'node:test';
import assert from 'node:assert/strict';
import { localDate, matchListings, parseNeeds, validateLead } from '../supabase/functions/lumi-rental-agent/agent.mjs';

const today = '2026-11-16';
test('extracts Vietnamese criteria and Hanoi dates', () => {
  assert.deepEqual(parseNeeds('2 ngủ full nội thất, tối đa 12,5 triệu, có chỗ ô tô, vào ở 1/12', today), {
    unit_type: '2PN', budget_vnd: 12_500_000, furnishing: 'Full nội thất', parking: true, move_in: '2026-12-01',
  });
  assert.equal(parseNeeds('3PN 10–12tr, không cần parking, vào 1/1', today).move_in, '2027-01-01');
  assert.equal(parseNeeds('3PN 74m²', today).budget_vnd, null);
  assert.equal(localDate(Date.parse('2026-11-15T17:00:00Z')), today);
});
test('requires consent and prioritizes a viewing request', () => {
  const sample = { id: '50ed7d9b-05e1-4b7f-a164-ef91f3e1be20', consent: true, phone: '+84 977 923 284', budget_vnd: 12e6 };
  assert.throws(() => validateLead({ ...sample, consent: false }, today), /đồng ý/);
  assert.throws(() => validateLead({ ...sample, viewing_date: '2026-11-18' }, today), /Chọn cả/);
  const lead = validateLead({ ...sample, viewing_date: '2026-11-18', viewing_period: 'afternoon', attribution: { utm_source: 'facebook', phone: 'private' } }, today);
  assert.equal(lead.priority, 'hot');
  assert.equal(lead.phone, '0977923284');
  assert.deepEqual(lead.attribution, { utm_source: 'facebook' });
});
test('only ranks explicit parking mentions when requested', () => {
  const rows = [
    { slug: 'unknown', title: '2PN', description: 'Chỗ ô tô cần xác minh', price_vnd: 8e6 },
    { slug: 'dated', title: '2PN', description: 'Có slot xe hầm', price_vnd: 10e6, available_from: today },
    { slug: 'no', title: '2PN', description: 'Không có chỗ ô tô', price_vnd: 7e6 },
    { slug: 'undated', title: '2PN', description: 'Có chỗ ô tô', price_vnd: 9e6 },
  ];
  assert.deepEqual(matchListings(rows, { parking: true, move_in: today }).map(row => row.slug), ['dated', 'undated']);
});
