-- Execute este arquivo no SQL Editor do projeto Supabase antes de usar pets e avaliações.
-- A tabela public.usuarios é o perfil público ligado ao usuário do Supabase Auth.
create table if not exists public.usuarios (
  id uuid primary key references auth.users(id) on delete cascade,
  nome_completo text not null,
  tipo_usuario text not null default 'tutor' check (tipo_usuario in ('tutor', 'petshop')),
  is_cuidador boolean not null default false,
  genero text check (genero in ('masculino', 'feminino')),
  cidade text,
  estado text,
  idade integer check (idade >= 0),
  bio text,
  avatar_url text,
  created_at timestamptz not null default now()
);

-- Compatibilidade para projetos que já tinham a tabela usuarios criada.
alter table public.usuarios add column if not exists tipo_usuario text not null default 'tutor';
alter table public.usuarios add column if not exists is_cuidador boolean not null default false;
alter table public.usuarios add column if not exists genero text;
update public.usuarios set is_cuidador = false where is_cuidador is null;

-- Cria o perfil mesmo quando a confirmação de e-mail estiver habilitada.
create or replace function public.criar_perfil_usuario()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into public.usuarios (id, nome_completo, tipo_usuario, is_cuidador)
  values (
    new.id,
    coalesce(new.raw_user_meta_data ->> 'nome_completo', 'Novo usuário'),
    coalesce(new.raw_user_meta_data ->> 'tipo_usuario', 'tutor'),
    false
  )
  on conflict (id) do update set
    nome_completo = excluded.nome_completo,
    tipo_usuario = excluded.tipo_usuario;
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

create table if not exists public.produtos (
  id bigint generated always as identity primary key,
  vendedor_id uuid not null references public.usuarios(id) on delete cascade,
  nome text not null,
  descricao text,
  categoria text not null default 'Geral',
  preco numeric(10,2) not null check (preco >= 0),
  estoque integer not null default 0 check (estoque >= 0),
  foto_url text,
  ativo boolean not null default true,
  created_at timestamptz not null default now()
);

alter table public.usuarios enable row level security;
alter table public.pets enable row level security;
alter table public.avaliacoes enable row level security;
alter table public.produtos enable row level security;

create policy "perfis são públicos" on public.usuarios for select using (true);
create policy "usuário cria o próprio perfil" on public.usuarios for insert with check (auth.uid() = id);
create policy "usuário edita o próprio perfil" on public.usuarios for update using (auth.uid() = id) with check (auth.uid() = id);
create policy "pets são públicos" on public.pets for select using (true);
create policy "tutor cadastra pet" on public.pets for insert with check (auth.uid() = tutor_id);
create policy "tutor altera pet" on public.pets for update using (auth.uid() = tutor_id) with check (auth.uid() = tutor_id);
create policy "avaliações são públicas" on public.avaliacoes for select using (true);
create policy "autor cria avaliação" on public.avaliacoes for insert with check (auth.uid() = autor_id and autor_id <> avaliado_id);
create policy "autor altera avaliação" on public.avaliacoes for update using (auth.uid() = autor_id) with check (auth.uid() = autor_id and autor_id <> avaliado_id);
create policy "produtos são públicos" on public.produtos for select using (ativo = true);
create policy "petshop cadastra produtos" on public.produtos for insert with check (
  auth.uid() = vendedor_id and exists (
    select 1 from public.usuarios
    where id = auth.uid() and tipo_usuario = 'petshop'
  )
);
create policy "petshop altera produtos" on public.produtos for update using (auth.uid() = vendedor_id) with check (auth.uid() = vendedor_id);
