-- =========================
-- tables
-- =========================

create table if not exists statuses (
  id_status int generated always as identity primary key,
  code varchar(50) not null,
  name varchar(50) not null,
  created_at timestamptz not null default current_timestamp,
  constraint uk_status_code unique (code)
);

insert into statuses (code, name)
values
  ('new','new'),
  ('selected','selected'),
  ('contacted','contacted'),
  ('negotiation','negotiation'),
  ('archived','archived')
on conflict (code) do nothing;


create table if not exists public."role" (
  id_role int generated always as identity primary key,
  code varchar(50) not null,
  name_role varchar(50) not null,
  created_at timestamptz not null default current_timestamp,
  constraint uk_role_code unique (code)
);

insert into public."role" (code, name_role)
values
  ('admin','admin'),
  ('user','user')
on conflict (code) do nothing;


create table if not exists users (
  id_user int generated always as identity primary key,
  full_name varchar(100),
  doc_num varchar(100) not null,
  user_name varchar(100) not null,
  password_hash varchar(250) not null,
  email varchar(150) not null,
  id_role int not null,
  profile_picture varchar(255),

  created_at timestamptz not null default current_timestamp,
  updated_at timestamptz not null default current_timestamp,
  last_login_at timestamptz,

  constraint uk_user_doc unique (doc_num),
  constraint uk_user_email unique (email),
  constraint uk_user_username unique (user_name),

  constraint fk_users_role
    foreign key (id_role)
    references public."role"(id_role)
    on update cascade
    on delete restrict
);


create table if not exists technologies (
  id_tech int generated always as identity primary key,
  name_tech varchar(100) not null,
  name_normalization varchar(100) not null,
  created_at timestamptz not null default current_timestamp,
  constraint uk_tech_norm unique (name_normalization)
);


create table if not exists company (
  id_company int generated always as identity primary key,
  nit varchar(100),
  name varchar(150) not null,
  sector varchar(100),
  email varchar(100),
  phone varchar(20),
  address varchar(150),
  url varchar(500),
  country varchar(100),
  description text,
  category varchar(100),

  score smallint,
  id_status int,

  created_at timestamptz not null default current_timestamp,
  updated_at timestamptz not null default current_timestamp,
  status_changed_at timestamptz not null default current_timestamp,

  updated_by int,

  constraint chk_company_score check (score between 1 and 3),

  constraint fk_company_status
    foreign key (id_status)
    references statuses(id_status)
    on update cascade
    on delete restrict,

  constraint fk_company_updated_by
    foreign key (updated_by)
    references users(id_user)
    on update cascade
    on delete restrict
);

update company c
set id_status = s.id_status
from statuses s
where c.id_status is null
  and s.code = 'new';

alter table company
alter column id_status set not null;

alter table company
add column if not exists name_normalization varchar(150);

update company
set name_normalization = lower(regexp_replace(trim(name), '\s+', '', 'g'))
where name_normalization is null;

alter table company
alter column name_normalization set not null;

create unique index if not exists uk_company_country_name_norm
on company (country, name_normalization);


create table if not exists refresh_tokens (
  id_refresh int generated always as identity primary key,
  id_user int not null,
  token_hash varchar(255) not null,
  expires_at timestamptz not null,
  created_at timestamptz not null default current_timestamp,
  revoked_at timestamptz,
  constraint fk_refresh_user foreign key (id_user) references users(id_user) on update cascade on delete cascade
);
create index if not exists idx_refresh_tokens_id_user on refresh_tokens (id_user);
create index if not exists idx_refresh_tokens_expires_at on refresh_tokens (expires_at);


create table if not exists company_technologies (
  id_company int not null,
  id_tech int not null,
  created_at timestamptz not null default current_timestamp,

  primary key (id_company, id_tech),

  constraint fk_company
    foreign key (id_company)
    references company(id_company)
    on update cascade
    on delete restrict,

  constraint fk_technology
    foreign key (id_tech)
    references technologies(id_tech)
    on update cascade
    on delete restrict
);


create table if not exists scraping_logs (
  id_scraping int generated always as identity primary key,
  id_user int not null,
  source varchar(150),
  parameters jsonb,

  total_found int not null default 0,
  total_new int not null default 0,
  total_updated int not null default 0,
  total_failed int not null default 0,

  duration_second int,
  execution_status varchar(50) not null,
  error_message text,
  executed_at timestamptz not null default current_timestamp,

  constraint fk_scraping_log
    foreign key (id_user)
    references users(id_user)
    on update cascade
    on delete restrict
);


create table if not exists emails (
  id_email int generated always as identity primary key,
  id_company int not null,
  id_user int,

  subject varchar(255) not null,
  body_html text not null,
  recipient_email varchar(150) not null,

  send_status varchar(50) not null,
  error_message text,

  status varchar(50) not null,
  sent_at timestamptz,

  created_at timestamptz not null default current_timestamp,
  updated_at timestamptz not null default current_timestamp,

  constraint fk_company_email
    foreign key (id_company)
    references company(id_company)
    on update cascade
    on delete restrict,

  constraint fk_email_user
    foreign key (id_user)
    references users(id_user)
    on update cascade
    on delete set null
);


create table if not exists email_events (
  id_event int generated always as identity primary key,
  id_email int not null,
  event_type varchar(50) not null,
  details text,
  created_at timestamptz not null default current_timestamp,

  constraint fk_event_email
    foreign key (id_email)
    references emails(id_email)
    on delete cascade
);

-- =========================
-- functions and triggers
-- =========================

create or replace function set_updated_at()
returns trigger as $$
begin
  new.updated_at = current_timestamp;
  return new;
end;
$$ language plpgsql;

create or replace function set_company_status_changed_at()
returns trigger as $$
begin
  if new.id_status is distinct from old.id_status then
    new.status_changed_at = current_timestamp;
  end if;
  return new;
end;
$$ language plpgsql;

create or replace function set_company_default_status()
returns trigger as $$
begin
  if new.id_status is null then
    select id_status into new.id_status
    from statuses
    where code = 'new';
  end if;

  if new.id_status is null then
    raise exception 'no existe status con code=new en statuses';
  end if;

  return new;
end;
$$ language plpgsql;

drop trigger if exists trg_users_updated_at on users;
create trigger trg_users_updated_at
before update on users
for each row
execute function set_updated_at();

drop trigger if exists trg_company_updated_at on company;
create trigger trg_company_updated_at
before update on company
for each row
execute function set_updated_at();

drop trigger if exists trg_emails_updated_at on emails;
create trigger trg_emails_updated_at
before update on emails
for each row
execute function set_updated_at();

drop trigger if exists trg_company_status_changed_at on company;
create trigger trg_company_status_changed_at
before update on company
for each row
execute function set_company_status_changed_at();

drop trigger if exists trg_company_default_status on company;
create trigger trg_company_default_status
before insert on company
for each row
execute function set_company_default_status();

-- =========================
-- indexes
-- =========================

create index if not exists idx_company_country on company (country);
create index if not exists idx_company_sector on company (sector);
create index if not exists idx_company_status on company (id_status);
create index if not exists idx_company_tech_company on company_technologies (id_tech, id_company);