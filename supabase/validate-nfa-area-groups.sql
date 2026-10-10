-- Enforce canonical NFA market groups only for NEW entries and CHANGED area/unit.
-- Existing legacy listings remain untouched and may be edited without rewriting
-- their area. This protects data from old browser tabs or direct REST API writes.
-- Shop chân đế has no fixed apartment layout, so numeric NFA remains permitted.
CREATE OR REPLACE FUNCTION public.lumi_validate_market_area_group()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
  accepted numeric[];
BEGIN
  CASE NEW.unit_type
    WHEN '1PN' THEN accepted := ARRAY[43,47,54]::numeric[];
    WHEN '2PN' THEN accepted := ARRAY[54,62,74,85,97]::numeric[];
    WHEN '3PN' THEN accepted := ARRAY[85,95,101,107,112,117,130,137]::numeric[];
    WHEN '4PN' THEN accepted := ARRAY[128,136]::numeric[];
    WHEN 'Duplex' THEN accepted := ARRAY[115,134,143,194,200,212]::numeric[];
    WHEN 'Penthouse' THEN accepted := ARRAY[346,368,377,402]::numeric[];
    WHEN 'Shop chân đế' THEN RETURN NEW;
    ELSE RAISE EXCEPTION 'Loại căn không hợp lệ: %', NEW.unit_type
      USING ERRCODE = '23514';
  END CASE;

  IF NOT NEW.area_sqm = ANY(accepted) THEN
    RAISE EXCEPTION 'Diện tích % m² không nằm trong nhóm thông thủy đã chuẩn hóa cho loại căn %', NEW.area_sqm, NEW.unit_type
      USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS listings_validate_area_group_insert ON public.listings;
CREATE TRIGGER listings_validate_area_group_insert
BEFORE INSERT ON public.listings
FOR EACH ROW EXECUTE FUNCTION public.lumi_validate_market_area_group();

DROP TRIGGER IF EXISTS listings_validate_area_group_update ON public.listings;
CREATE TRIGGER listings_validate_area_group_update
BEFORE UPDATE OF unit_type, area_sqm ON public.listings
FOR EACH ROW
WHEN ((NEW.unit_type IS DISTINCT FROM OLD.unit_type)
   OR (NEW.area_sqm IS DISTINCT FROM OLD.area_sqm))
EXECUTE FUNCTION public.lumi_validate_market_area_group();
