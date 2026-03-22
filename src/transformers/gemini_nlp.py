"""
gemini_nlp.py
-------------
Camada de Transformação (T) do ETL — Enriquecimento com IA Generativa.
Usa o Google Gemini Flash para extrair entidades estruturadas de cada edital
e gerar um resumo conciso em português.

Contrato da IA:
  Input: título do edital
  Output: JSON com orgao_banca, cargo_principal, remuneracao_maxima,
          data_prova e resumo
"""
import json
import os
import time
from typing import Optional

import google.generativeai as genai
import pandas as pd
from dotenv import load_dotenv

from src.utils.logger_config import get_logger

load_dotenv()

logger = get_logger(__name__)

# ─── Configuração do Gemini ───────────────────────────────────────────────────
_MODELO = "gemini-3-flash-preview"  # Modelo estável e econômico
_MAX_RETRIES = 3
_DELAY_ENTRE_CHAMADAS = 16  # segundos — respeita limite de 5 requisições por minuto (Free Tier)

_PROMPT_TEMPLATE = """
Você é um assistente especialista em concursos públicos brasileiros.
Com base no título do edital abaixo, extraia as informações e retorne APENAS um JSON válido.
Se uma informação não estiver disponível, use null.

Título do edital: "{titulo}"

Retorne EXATAMENTE neste formato JSON (sem markdown, sem explicações):
{{
  "orgao_banca": "Nome do órgão ou banca organizadora",
  "cargo_principal": "Cargo de maior destaque ou mais cargos disponíveis",
  "remuneracao_maxima": 0.00,
  "data_prova": "YYYY-MM-DD ou null se não informado",
  "resumo": "Resumo conciso em 2-3 frases para o candidato entender a oportunidade"
}}
"""


def _configurar_gemini() -> genai.GenerativeModel:
    """Inicializa o cliente Gemini com a chave da API."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("Variável de ambiente GEMINI_API_KEY é obrigatória.")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(_MODELO)


def _chamar_gemini(model: genai.GenerativeModel, titulo: str) -> Optional[dict]:
    """
    Chama a API Gemini e tenta fazer parse do JSON retornado.

    Args:
        model: Instância do modelo Gemini.
        titulo: Título do edital a ser processado.

    Returns:
        Dicionário com os dados extraídos ou None em caso de falha.
    """
    prompt = _PROMPT_TEMPLATE.format(titulo=titulo)

    for tentativa in range(1, _MAX_RETRIES + 1):
        try:
            resposta = model.generate_content(prompt)
            texto = resposta.text.strip()

            # Remove possíveis blocos de markdown (```json ... ```)
            if texto.startswith("```"):
                texto = texto.split("```")[1]
                if texto.startswith("json"):
                    texto = texto[4:]

            dados = json.loads(texto.strip())
            return dados

        except json.JSONDecodeError as e:
            logger.warning(
                f"[Tentativa {tentativa}/{_MAX_RETRIES}] "
                f"JSON inválido retornado pelo Gemini: {e}"
            )
        except Exception as e:
            logger.warning(
                f"[Tentativa {tentativa}/{_MAX_RETRIES}] "
                f"Erro na chamada ao Gemini: {e}"
            )
            if tentativa < _MAX_RETRIES:
                time.sleep(2 ** tentativa)  # backoff exponencial

    return None


def enriquecer(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enriquece o DataFrame de editais com dados extraídos pelo Gemini.
    Processa cada edital individualmente e preenche as colunas:
    orgao_banca, cargo_principal, remuneracao_maxima, data_prova, resumo_ia.

    Editais onde a IA falhar serão mantidos no DataFrame com campos nulos,
    para não bloquear o pipeline.

    Args:
        df: DataFrame com os editais processados por filtros_pandas.

    Returns:
        DataFrame com as colunas de IA preenchidas.
    """
    if df.empty:
        logger.warning("DataFrame vazio recebido para enriquecimento.")
        return df

    try:
        model = _configurar_gemini()
    except EnvironmentError as e:
        logger.error(f"Gemini não configurado: {e}. Pulando enriquecimento.")
        return df

    total = len(df)
    logger.info(f"Iniciando enriquecimento com IA para {total} edital(is).")

    for idx, row in df.iterrows():
        titulo = row.get("titulo") or ""
        if not titulo:
            logger.warning(f"Edital sem título (idx={idx}), pulando enriquecimento.")
            continue

        logger.info(f"[{idx + 1}/{total}] Processando: {titulo[:80]}...")
        dados_ia = _chamar_gemini(model, titulo)

        if dados_ia:
            df.at[idx, "orgao_banca"] = dados_ia.get("orgao_banca")
            df.at[idx, "cargo_principal"] = dados_ia.get("cargo_principal")
            df.at[idx, "remuneracao_maxima"] = dados_ia.get("remuneracao_maxima")
            df.at[idx, "data_prova"] = dados_ia.get("data_prova")
            df.at[idx, "resumo_ia"] = dados_ia.get("resumo")
        else:
            logger.warning(f"Enriquecimento falhou para: {titulo[:80]}")

        # Respeitar rate limit da API Gemini (plano gratuito)
        if idx < total - 1:
            time.sleep(_DELAY_ENTRE_CHAMADAS)

    # Converter NaN para None para evitar erros de serialização JSON posterior
    df = df.where(pd.notnull(df), None)
    logger.info("Enriquecimento com IA concluído.")
    return df
