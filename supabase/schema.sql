-- Execute este arquivo no SQL Editor do projeto Supabase antes de usar pets e avaliações.
-- A tabela public.usuarios é o perfil público ligado ao usuário do Supabase Auth.
create table if not exists public.usuarios (
  id uuid primary key references auth.users(id) on delete cascade,
  nome_completo text not null,
  cidade text,
  estado text,
  idade integer check (idade >= 0),
  bio text,
  avatar_url text,
  created_at timestamptz not null default now()
);

-- Cria o perfil mesmo quando a confirmação de e-mail estiver habilitada.
create or replace function public.criar_perfil_usuario()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into public.usuarios (id, nome_completo)
  values (new.id, coalesce(new.raw_user_meta_data ->> 'nome_completo', 'Novo usuário'))
  on conflict (id) do nothing;
  return new;
end;
$$;
drop trigger if exists ao_criar_usuario on auth.users;
create trigger ao_criar_usuario after insert on auth.users
for each row execute procedure public.criar_perfil_usuario();

create table if not exists public.pets (
  id bigint generated always as identity primary key,
  tutor_id uuid not null references public.usuarios(id) on delete cascade,
  nome text not null,
  especie text not null,
  raca text,
  sexo text,
  porte text,
  idade text,
  localizacao text not null,
  saude text,
  sobre text,
  foto_url text,
  disponivel boolean not null default true,
  created_at timestamptz not null default now()
);

create table if not exists public.avaliacoes (
  id bigint generated always as identity primary key,
  autor_id uuid not null references public.usuarios(id) on delete cascade,
  avaliado_id uuid not null references public.usuarios(id) on delete cascade,
  nota smallint not null check (nota between 1 and 5),
  comentario text not null check (char_length(trim(comentario)) > 0),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (autor_id, avaliado_id),
  check (autor_id <> avaliado_id)
);

alter table public.usuarios enable row level security;
alter table public.pets enable row level security;
alter table public.avaliacoes enable row level security;

create policy "perfis são públicos" on public.usuarios for select using (true);
create policy "usuário cria o próprio perfil" on public.usuarios for insert with check (auth.uid() = id);
create policy "usuário edita o próprio perfil" on public.usuarios for update using (auth.uid() = id) with check (auth.uid() = id);
create policy "pets são públicos" on public.pets for select using (true);
create policy "tutor cadastra pet" on public.pets for insert with check (auth.uid() = tutor_id);
create policy "tutor altera pet" on public.pets for update using (auth.uid() = tutor_id) with check (auth.uid() = tutor_id);
create policy "avaliações são públicas" on public.avaliacoes for select using (true);
create policy "autor cria avaliação" on public.avaliacoes for insert with check (auth.uid() = autor_id and autor_id <> avaliado_id);
create policy "autor altera avaliação" on public.avaliacoes for update using (auth.uid() = autor_id) with check (auth.uid() = autor_id and autor_id <> avaliado_id);
