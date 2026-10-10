-- Lumi Hanoi marketplace only (project salsyqatlzapnzbcnnsr).
-- Normalize furnishing on all existing sale/rent listings (including shops).
-- Preserve NULL where the poster never supplied information: do not guess Full/Basic.
-- Safe to rerun, idempotent; do not rewrite UGC title, description, price or area.
BEGIN;

UPDATE public.listings
SET furnishing = CASE btrim(furnishing)
    WHEN 'Bàn giao nguyên bản' THEN 'Đồ cơ bản'
    WHEN 'Nội thất cơ bản' THEN 'Đồ cơ bản'
    WHEN 'Đầy đủ nội thất' THEN 'Full nội thất'
    ELSE furnishing
END
WHERE btrim(furnishing) IN (
    'Bàn giao nguyên bản', 'Nội thất cơ bản', 'Đầy đủ nội thất'
);

ALTER TABLE public.listings
    DROP CONSTRAINT IF EXISTS listings_furnishing_check;

ALTER TABLE public.listings
    ADD CONSTRAINT listings_furnishing_check
    CHECK (furnishing IS NULL OR furnishing IN ('Đồ cơ bản', 'Full nội thất'));

COMMIT;
