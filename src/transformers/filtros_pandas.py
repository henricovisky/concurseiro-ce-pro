"""
filtros_pandas.py
-----------------
Camada de Transformação (T) do ETL — Limpeza e padronização dos dados.
Responsável por:
  - Converter a lista de editais brutos em DataFrame
  - Normalizar campos (datas, texto, URLs)
  - Remover duplicatas locais
  - Gerar o hash_identificador para cada edital (chave de idempotência)
"""
import re
from datetime import datetime
from typing import Optional

import pandas as pd

from src.utils.hash_generator import gerar_hash
from src.utils.logger_config import get_logger

logger = get_logger(__name__)


def _normalizar_texto(texto: Optional[str]) -> Optional[str]:
    """Remove espaços extras e normaliza quebras de linha."""
    if not texto:
        return None
    return re.sub(r"\s+", " ", str(texto)).strip()


def _normalizar_url(url: Optional[str]) -> Optional[str]:
    """Garante que a URL não possui espaços ou caracteres inválidos."""
    if not url:
        return None
    return str(url).strip()


def processar(editais_brutos: list[dict]) -> pd.DataFrame:
    """
    Recebe a lista de editais brutos do extrator e retorna um DataFrame
    limpo, normalizado e com o hash_identificador gerado.

    Args:
        editais_brutos: Lista de dicionários retornada por rss_concursos.extrair().

    Returns:
        pd.DataFrame com colunas normalizadas e hash_identificador.
        Retorna DataFrame vazio se a entrada for inválida ou vazia.
    """
    if not editais_brutos:
        logger.warning("Nenhum edital recebido para processamento.")
        return pd.DataFrame()

    df = pd.DataFrame(editais_brutos)
    logger.info(f"Processando {len(df)} edital(is) brutos.")

    # ── Normalizar campos de texto ──────────────────────────────────────────
    if "titulo" in df.columns:
        df["titulo"] = df["titulo"].apply(_normalizar_texto)

    if "link_original" in df.columns:
        df["link_original"] = df["link_original"].apply(_normalizar_url)

    # ── Remover linhas sem link (campo obrigatório) ─────────────────────────
    antes = len(df)
    df = df.dropna(subset=["link_original"])
    df = df[df["link_original"].str.strip() != ""]
    if len(df) < antes:
        logger.warning(f"{antes - len(df)} edital(is) removidos por falta de link.")

    # ── Gerar hash_identificador (prioriza URL, fallback para título) ─────
    def _gerar_hash_row(row: pd.Series) -> Optional[str]:
        base = row.get("link_original") or row.get("titulo")
        if not base:
            return None
        return gerar_hash(base)

    df["hash_identificador"] = df.apply(_gerar_hash_row, axis=1)

    # ── Remover linhas sem hash ─────────────────────────────────────────────
    df = df.dropna(subset=["hash_identificador"])

    # ── Deduplicar localmente por hash ──────────────────────────────────────
    antes = len(df)
    df = df.drop_duplicates(subset=["hash_identificador"])
    if len(df) < antes:
        logger.info(f"{antes - len(df)} duplicata(s) local removida(s).")

    # ── Garantir coluna extraido_em ─────────────────────────────────────────
    if "extraido_em" not in df.columns:
        df["extraido_em"] = datetime.utcnow().isoformat()

    # ── Campos que serão preenchidos pelo gemini_nlp ────────────────────────
    for campo in ["orgao_banca", "cargo_principal", "remuneracao_maxima",
                  "data_prova", "resumo_ia"]:
        if campo not in df.columns:
            df[campo] = None

    df = df.where(pd.notnull(df), None)
    df = df.reset_index(drop=True)
    logger.info(f"{len(df)} edital(is) prontos para enriquecimento com IA.")
    return df
