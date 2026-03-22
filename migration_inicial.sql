-- =============================================
-- Concurseiro CE Pro — Migration Inicial
-- Execute este SQL no Supabase SQL Editor
-- (https://supabase.com/dashboard > SQL Editor)
-- =============================================

-- Extensão para gerar UUIDs automaticamente
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─── Módulo 1: Radar de Editais ──────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS radar_editais (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hash_identificador  TEXT UNIQUE NOT NULL,       -- Hash MD5 da URL (garante unicidade)
    orgao_banca         TEXT NOT NULL,
    cargo_principal     TEXT,
    remuneracao_maxima  NUMERIC(10, 2),
    data_prova          DATE,
    link_original       TEXT NOT NULL,
    resumo_ia           TEXT,
    notificado_discord  BOOLEAN DEFAULT FALSE,
    criado_em           TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index para busca rápida na verificação de duplicatas (idempotência)
CREATE INDEX IF NOT EXISTS idx_radar_hash ON radar_editais(hash_identificador);

-- Desativar RLS para permitir inserções via API (ou configure polices específicas)
ALTER TABLE radar_editais DISABLE ROW LEVEL SECURITY;

-- ─── Módulo 2: Vigilante de Diários Oficiais (futuro) ────────────────────────

CREATE TABLE IF NOT EXISTS vigilante_dou (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hash_identificador  TEXT UNIQUE NOT NULL,       -- Hash MD5 do texto + data
    data_publicacao     DATE NOT NULL,
    termo_monitorado    TEXT NOT NULL,              -- Ex: CPF ou Nome Completo
    caderno_secao       TEXT,
    trecho_encontrado   TEXT,
    analise_ia          TEXT,                       -- Ex: "Convocação para posse"
    notificado_discord  BOOLEAN DEFAULT FALSE,
    criado_em           TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index para otimizar a busca diária
CREATE INDEX IF NOT EXISTS idx_vigilante_hash ON vigilante_dou(hash_identificador);
