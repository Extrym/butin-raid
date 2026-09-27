-- Butin de Raid : schéma Supabase.
-- Les données du site (joueurs, personnages, loots, objets ajoutés, réglages) sont des documents JSON
-- rangés par collection, comme dans la version claude.ai. Les accès sont décidés par la table `access`.

create table if not exists public.docs (
  collection text not null,
  id text not null,
  data jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now(),
  primary key (collection, id)
);

-- Qui a accès : pseudo Discord (et identifiant Discord une fois connu) -> niveau.
create table if not exists public.access (
  handle text primary key,               -- pseudo Discord, en minuscules
  discord_id text unique,                -- rempli automatiquement à la première connexion
  level text not null check (level in ('membre', 'officier', 'admin')),
  added_at timestamptz not null default now()
);

-- Niveau de la personne connectée. Lit l'identité Discord fournie par Supabase (auth.identities),
-- que l'utilisateur ne peut pas modifier, contrairement à user_metadata.
create or replace function public.my_level() returns text
language sql stable security definer set search_path = public, auth as $$
  select a.level
  from public.access a
  join auth.identities i on i.user_id = auth.uid() and i.provider = 'discord'
  where a.discord_id = i.provider_id
     or (a.discord_id is null and a.handle = lower(i.identity_data->>'full_name'))
  limit 1
$$;

-- Pseudo Discord de la personne connectée (pour « noté par » et l'écran d'accès refusé).
create or replace function public.my_handle() returns text
language sql stable security definer set search_path = public, auth as $$
  select lower(i.identity_data->>'full_name') from auth.identities i
  where i.user_id = auth.uid() and i.provider = 'discord' limit 1
$$;

-- À la connexion, fige l'identifiant Discord sur la ligne d'accès correspondant au pseudo.
create or replace function public.claim_access() returns text
language plpgsql security definer set search_path = public, auth as $$
declare pid text; h text;
begin
  select i.provider_id, lower(i.identity_data->>'full_name') into pid, h
  from auth.identities i where i.user_id = auth.uid() and i.provider = 'discord' limit 1;
  if pid is null then return null; end if;
  update public.access set discord_id = pid where handle = h and discord_id is null;
  return public.my_level();
end $$;

revoke all on function public.my_level(), public.my_handle(), public.claim_access() from public, anon;
grant execute on function public.my_level(), public.my_handle(), public.claim_access() to authenticated;

alter table public.docs enable row level security;
alter table public.access enable row level security;

drop policy if exists docs_read on public.docs;
drop policy if exists docs_write on public.docs;
create policy docs_read on public.docs for select to authenticated
  using (public.my_level() in ('membre', 'officier', 'admin'));
create policy docs_write on public.docs for all to authenticated
  using (public.my_level() in ('officier', 'admin'))
  with check (public.my_level() in ('officier', 'admin'));

drop policy if exists access_read on public.access;
drop policy if exists access_write on public.access;
create policy access_read on public.access for select to authenticated
  using (public.my_level() = 'admin');
create policy access_write on public.access for all to authenticated
  using (public.my_level() = 'admin') with check (public.my_level() = 'admin');

revoke all on public.docs, public.access from anon;
grant select, insert, update, delete on public.docs, public.access to authenticated;

-- Mises à jour en direct pour les autres officiers.
do $$ begin
  alter publication supabase_realtime add table public.docs;
exception when duplicate_object then null; end $$;
