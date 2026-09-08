-- Lumi Hanoi marketplace: privacy-preserving listing view counts.
-- Production migration names: add_listing_view_count + fix_listing_view_count_rpc.

alter table public.listings
  add column if not exists view_count bigint not null default 0
  check (view_count >= 0);

create table if not exists private.listing_view_visitors (
  listing_id uuid not null references public.listings(id) on delete cascade,
  visitor_hash text not null check (char_length(visitor_hash) = 64),
  last_viewed_at timestamptz not null default now(),
  primary key (listing_id, visitor_hash)
);

revoke all on table private.listing_view_visitors from public, anon, authenticated;

-- A view must not make the listing look freshly edited in admin/SEO metadata.
create or replace function private.set_updated_at()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  if (to_jsonb(new) - 'updated_at' - 'view_count') is distinct from
     (to_jsonb(old) - 'updated_at' - 'view_count') then
    new.updated_at = now();
  else
    new.updated_at = old.updated_at;
  end if;
  return new;
end;
$$;

-- Intentional anonymous RPC. It can only increment the counter of a currently
-- public listing. Raw IP addresses are never stored. The digest includes the
-- listing id so visitors cannot be correlated across different listings.
create or replace function public.record_listing_view(target_listing_id uuid)
returns bigint
language plpgsql
security definer
set search_path = ''
as $$
declare
  request_headers jsonb := '{}'::jsonb;
  user_agent text := '';
  client_ip text := '';
  visitor_fingerprint text := '';
  current_count bigint;
  should_increment boolean := false;
begin
  select l.view_count
    into current_count
  from public.listings l
  where l.id = target_listing_id
    and l.status = 'approved'
    and l.contact_public
    and (l.expires_at is null or l.expires_at > now());

  if not found then
    return null;
  end if;

  begin
    request_headers := coalesce(nullif(current_setting('request.headers', true), '')::jsonb, '{}'::jsonb);
  exception when others then
    request_headers := '{}'::jsonb;
  end;

  user_agent := lower(coalesce(request_headers ->> 'user-agent', ''));
  client_ip := coalesce(
    nullif(btrim(split_part(coalesce(request_headers ->> 'x-forwarded-for', ''), ',', 1)), ''),
    nullif(btrim(coalesce(request_headers ->> 'cf-connecting-ip', '')), ''),
    nullif(btrim(coalesce(request_headers ->> 'x-real-ip', '')), ''),
    ''
  );

  if user_agent = ''
     or client_ip = ''
     or user_agent ~ '(bot|crawler|spider|slurp|preview|headless|lighthouse|pagespeed|curl|wget)' then
    return current_count;
  end if;

  visitor_fingerprint := encode(
    extensions.digest(target_listing_id::text || '|' || client_ip || '|' || user_agent, 'sha256'),
    'hex'
  );

  insert into private.listing_view_visitors as v (listing_id, visitor_hash, last_viewed_at)
  values (target_listing_id, visitor_fingerprint, now())
  on conflict (listing_id, visitor_hash) do update
    set last_viewed_at = excluded.last_viewed_at
    where v.last_viewed_at <= now() - interval '1 hour'
  returning true into should_increment;

  if coalesce(should_increment, false) then
    update public.listings l
      set view_count = l.view_count + 1
    where l.id = target_listing_id
      and l.status = 'approved'
      and l.contact_public
      and (l.expires_at is null or l.expires_at > now())
    returning l.view_count into current_count;
  end if;

  return current_count;
end;
$$;

comment on function public.record_listing_view(uuid) is
  'Intentional anonymous RPC for deduplicated marketplace listing view counts. Stores only a per-listing SHA-256 fingerprint; no raw IP address.';

revoke all on function public.record_listing_view(uuid) from public, anon, authenticated;
grant execute on function public.record_listing_view(uuid) to anon, authenticated;

notify pgrst, 'reload schema';
