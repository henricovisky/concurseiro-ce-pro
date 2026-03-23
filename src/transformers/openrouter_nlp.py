"""
openrouter_nlp.py
-----------------
Camada de Transformação (T) do ETL — Enriquecimento com IA via OpenRouter.
Substitui o Gemini direto para evitar limites de tokens e permitir troca de modelos.
Extrai entidades estruturadas de cada edital e gera um resumo conciso.
"""
import json
import os
import time
from typing import Optional, List

import requests
import pandas as pd
from dotenv import load_dotenv

from src.utils.logger_config import get_logger

load_dotenv()

logger = get_logger(__name__)

# ─── Configuração do OpenRouter ───────────────────────────────────────────────
# Lista de modelos gratuitos em ordem de preferência para fallback
_MODELOS_FALLBACK = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "stepfun/step-3.5-flash:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "google/gemma-3-4b-it:free"
]

_MAX_RETRIES = 2
_DELAY_ENTRE_CHAMADAS = 20  # Respeita o limite do OpenRouter Free Tier (especialmente para modelos densos)

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


def _chamar_openrouter(titulo: str) -> Optional[dict]:
    """
    Chama a API do OpenRouter e tenta fazer parse do JSON retornado, com fallback de modelos.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        logger.error("Variável de ambiente OPENROUTER_API_KEY não encontrada.")
        return None

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://github.com/henricovisky/concurseiro-ce-pro",
        "X-OpenRouter-Title": "Concurseiro CE Pro",
        "Content-Type": "application/json"
    }
    
    prompt = _PROMPT_TEMPLATE.format(titulo=titulo)
    
    for modelo in _MODELOS_FALLBACK:
        logger.debug(f"Tentando modelo: {modelo}")
        payload = {
            "model": modelo,
            "messages": [
                {"role": "user", "content": prompt}
            ]
            # Removido response_format pois nem todos os modelos free suportam e pode causar erro 400/404
        }

        for tentativa in range(1, _MAX_RETRIES + 1):
            try:
                response = requests.post(
                    url=url, 
                    headers=headers, 
                    data=json.dumps(payload), 
                    timeout=35
                )
                
                if response.status_code == 404:
                    # Tenta o próximo modelo da lista
                    logger.warning(f"Modelo {modelo} não disponível (404). Indo para fallback...")
                    break 

                response.raise_for_status()
                
                result = response.json()
                if "choices" not in result or not result["choices"]:
                    logger.warning(f"Resposta vazia do OpenRouter ({modelo}): {result}")
                    continue
                    
                texto = result["choices"][0]["message"]["content"].strip()

                # Limpeza de markdown se presente
                if texto.startswith("```"):
                    parts = texto.split("```")
                    if len(parts) >= 2:
                        texto = parts[1]
                        if texto.startswith("json"):
                            texto = texto[4:]

                dados = json.loads(texto.strip())
                return dados

            except requests.exceptions.RequestException as e:
                logger.warning(f"[Tentativa {tentativa}/{_MAX_RETRIES}] Erro na API ({modelo}): {e}")
                if tentativa < _MAX_RETRIES:
                    time.sleep(2 ** tentativa)
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"[Tentativa {tentativa}/{_MAX_RETRIES}] JSON inválido ({modelo}): {e}")
                if tentativa < _MAX_RETRIES:
                    time.sleep(1)
        
        # Se saiu do loop de tentativas e não retornou, tenta o próximo modelo

    return None


def enriquecer(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enriquece o DataFrame de editais com dados extraídos pelo OpenRouter.
    """
    if df.empty:
        logger.warning("DataFrame vazio recebido para enriquecimento.")
        return df

    total = len(df)
    logger.info(f"Iniciando enriquecimento com OpenRouter (Fallback de modelos free) para {total} edital(is).")

    contador = 0
    for idx, row in df.iterrows():
        contador += 1
        titulo = row.get("titulo") or ""
        if not titulo:
            continue

        logger.info(f"[{contador}/{total}] Processando: {titulo[:80]}...")
        dados_ia = _chamar_openrouter(titulo)

        if dados_ia:
            df.at[idx, "orgao_banca"] = dados_ia.get("orgao_banca")
            df.at[idx, "cargo_principal"] = dados_ia.get("cargo_principal")
            
            # Normalização de remuneração
            remun = dados_ia.get("remuneracao_maxima")
            if remun is not None:
                try:
                    df.at[idx, "remuneracao_maxima"] = float(remun)
                except (ValueError, TypeError):
                    df.at[idx, "remuneracao_maxima"] = None
            
            df.at[idx, "data_prova"] = dados_ia.get("data_prova")
            df.at[idx, "resumo_ia"] = dados_ia.get("resumo")
        else:
            logger.warning(f"Enriquecimento falhou definitivamente para: {titulo[:80]}")

        # Respeitar rate limit do OpenRouter (especialmente gratuito)
        if contador < total:
            time.sleep(_DELAY_ENTRE_CHAMADAS)

    # Converter NaN para None
    df = df.where(pd.notnull(df), None)
    logger.info("Enriquecimento com OpenRouter concluído.")
    return df
