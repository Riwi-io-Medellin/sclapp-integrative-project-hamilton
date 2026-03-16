-- Refresh tokens table for HttpOnly cookie auth (MVP)
-- Run this after schema.sql if you already have the DB.

create table if not exists refresh_tokens (
  id_refresh int generated always as identity primary key,
  id_user int not null,
  token_hash varchar(255) not null,
  expires_at timestamptz not null,
  created_at timestamptz not null default current_timestamp,
  revoked_at timestamptz,

  constraint fk_refresh_user
    foreign key (id_user)
    references users(id_user)
    on update cascade
    on delete cascade
);

create index if not exists idx_refresh_tokens_id_user on refresh_tokens (id_user);
create index if not exists idx_refresh_tokens_token_hash on refresh_tokens (token_hash);
create index if not exists idx_refresh_tokens_expires_at on refresh_tokens (expires_at);
