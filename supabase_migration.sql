-- Migration para ajustar as colunas da tabela radar_editais
-- devido a mudança do pipeline de IA para webscraping inteligente direto do HTML

ALTER TABLE radar_editais 
DROP COLUMN IF EXISTS orgao_banca,
DROP COLUMN IF EXISTS cargo_principal,
DROP COLUMN IF EXISTS remuneracao_maxima,
DROP COLUMN IF EXISTS data_prova,
DROP COLUMN IF EXISTS resumo_ia;

ALTER TABLE radar_editais 
ADD COLUMN IF NOT EXISTS titulo TEXT,
ADD COLUMN IF NOT EXISTS instituicao TEXT,
ADD COLUMN IF NOT EXISTS informacoes TEXT,
ADD COLUMN IF NOT EXISTS escolaridade TEXT,
ADD COLUMN IF NOT EXISTS inscricao_ate TEXT;
