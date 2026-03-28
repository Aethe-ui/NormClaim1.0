-- NormClaim Supabase schema bootstrap (idempotent)
-- Run this in Supabase SQL Editor.

create extension if not exists pgcrypto;

create table if not exists public.documents (
    id text primary key,
    filename text not null,
    storage_path text,
    status text default 'uploaded',
    consent_obtained boolean default false,
    created_at timestamptz not null default now()
);

create table if not exists public.extractions (
    id uuid primary key default gen_random_uuid(),
    document_id text not null,
    result_json jsonb not null,
    created_at timestamptz not null default now()
);
create index if not exists idx_extractions_document_id on public.extractions(document_id);

create table if not exists public.fhir_bundles (
    id uuid primary key default gen_random_uuid(),
    document_id text not null,
    bundle_json jsonb not null,
    created_at timestamptz not null default now()
);
create index if not exists idx_fhir_bundles_document_id on public.fhir_bundles(document_id);

create table if not exists public.reconciliations (
    id uuid primary key default gen_random_uuid(),
    document_id text not null,
    report_json jsonb not null,
    delta_inr numeric(12,2) default 0,
    created_at timestamptz not null default now()
);
create index if not exists idx_reconciliations_document_id on public.reconciliations(document_id);

create table if not exists public.human_reviews (
    id uuid primary key default gen_random_uuid(),
    document_id text not null,
    reviewer_notes text,
    corrections_json jsonb not null default '[]'::jsonb,
    reviewed_at text,
    created_at timestamptz not null default now()
);
create index if not exists idx_human_reviews_document_id on public.human_reviews(document_id);

create table if not exists public.feedback (
    id uuid primary key default gen_random_uuid(),
    document_id text not null,
    was_correct boolean not null,
    correction_type text,
    details text,
    created_at timestamptz not null default now()
);
create index if not exists idx_feedback_document_id on public.feedback(document_id);
