"""
rss_concursos.py
----------------
Extrator de editais de concursos públicos do Ceará via PCI Concursos.
Estratégia: scraping HTML com requests + BeautifulSoup.

Fontes:
  1. /concursos/#CE -> página filtrada por estado, seletores .da e .na
  2. /noticias/     -> página geral de notícias, filtrada por palavras-chave do CE

Regras de resiliência (obrigatórias):
  - Timeout configurável em todas as requisições HTTP.
  - Retry com backoff exponencial via tenacity.
"""
import time
from datetime import datetime
from typing import Optional

import requests
from bs4 import BeautifulSoup
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from src.utils.logger_config import get_logger

logger = get_logger(__name__)

# ─── Configurações ────────────────────────────────────────────────────────────
BASE_URL = "https://www.pciconcursos.com.br"

URL_CONCURSOS_CE = f"{BASE_URL}/concursos/#CE"

REQUEST_TIMEOUT = 20  # segundos

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Foco apenas na extração estruturada (HTML)


# ─── Helpers ──────────────────────────────────────────────────────────────────

@retry(
    retry=retry_if_exception_type((requests.Timeout, requests.ConnectionError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    before_sleep=before_sleep_log(logger, 20),  # logging.WARNING = 20
)
def _fetch_html(url: str) -> str:
    """
    Faz requisição HTTP com retry e backoff exponencial.

    Args:
        url: URL a ser requisitada (o #CE é removido do request, pois é âncora JS).

    Returns:
        Conteúdo HTML da página como string.

    Raises:
        requests.HTTPError: Se a resposta retornar status >= 400.
    """
    # Âncoras (#CE) não são enviadas pelo browser ao servidor — removemos antes
    url_sem_ancora = url.split("#")[0]
    logger.info(f"Buscando URL: {url_sem_ancora}")
    response = requests.get(url_sem_ancora, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    response.encoding = "utf-8"
    return response.text


def _extrair_editais_concursos_ce(html: str) -> list[dict]:
    """
    Extrai editais da página /concursos/ do PCI Concursos.

    Estrutura identificada via análise do browser:
      - Cada concurso está em uma <div class="da"> (destaque) ou <div class="na"> (normal)
      - O link e título ficam em <div class="ca"><a href="...">Título</a></div>
      - O estado fica em <div class="cc">CE</div>
      - Os links apontam para /noticias/...

    Apenas items com estado "CE" são incluídos.
    """
    soup = BeautifulSoup(html, "lxml")
    editais = []

    # Busca todos os blocos de concurso (destaque e normal)
    blocos = soup.select("div.da, div.na, div.ea, div.ua")

    if not blocos:
        # Fallback mais amplo: procura qualquer div com link dentro de .ca
        blocos = soup.select("div.ca")
        logger.warning(f"Usando seletor fallback .ca — encontrou {len(blocos)} bloco(s).")

    logger.info(f"Blocos de concurso encontrados: {len(blocos)}")

    for bloco in blocos:
        # Verifica se é do Ceará — o estado EXATO fica na div.cc
        estado_div = bloco.select_one("div.cc")
        if not estado_div or estado_div.get_text(strip=True).upper() != "CE":
            continue

        # Extrai o link principal (dentro de div.ca)
        link_tag = bloco.select_one("div.ca a")
        if not link_tag:
            # Fallback: qualquer <a> dentro do bloco
            link_tag = bloco.select_one("a")

        if not link_tag:
            continue

        titulo = link_tag.get("title") or ""
        instituicao = link_tag.get_text(strip=True)
        href = link_tag.get("href", "")

        if not titulo or not href:
            continue

        url_edital = href if href.startswith("http") else f"{BASE_URL}{href}"

        # Extrai informações complementares de vagas/salário (div.cd)
        info_div = bloco.select_one("div.cd")
        if info_div:
            # Pegamos o primeiro nó de texto do div.cd para as informações principais
            informacoes = info_div.find(text=True, recursive=False)
            informacoes = informacoes.strip() if informacoes else ""
            
            # Pegamos a escolaridade do último span
            spans = info_div.select("span")
            escolaridade = spans[-1].get_text(strip=True) if spans else ""
        else:
            informacoes = ""
            escolaridade = ""

        # Extrai prazo de inscrição (div.ce)
        prazo_div = bloco.select_one("div.ce span")
        if not prazo_div:
            prazo_div = bloco.select_one("div.ce")
        inscricao_ate = prazo_div.get_text(strip=True) if prazo_div else ""

        editais.append({
            "titulo": titulo,
            "instituicao": instituicao,
            "link_original": url_edital,
            "informacoes": informacoes,
            "escolaridade": escolaridade,
            "inscricao_ate": inscricao_ate,
            "estado": "CE",
            "fonte": URL_CONCURSOS_CE,
            "extraido_em": datetime.utcnow().isoformat(),
        })

    logger.info(f"{len(editais)} edital(is) do Ceará extraídos de /concursos/.")
    return editais


# Funções _extrair_noticias e _filtrar_por_ceara removidas pós-refatoração estruturada.


def _deduplicar(editais: list[dict]) -> list[dict]:
    """Remove duplicatas por URL (prevenção local antes de consultar o banco)."""
    vistos = set()
    unicos = []
    for edital in editais:
        link = edital.get("link_original", "")
        if link and link not in vistos:
            vistos.add(link)
            unicos.append(edital)
    return unicos


# ─── Interface Pública ────────────────────────────────────────────────────────

def extrair(incluir_noticias: bool = True) -> list[dict]:
    """
    Busca editais de concursos do Ceará via duas fontes do PCI Concursos:
      1. /concursos/#CE  — lista filtrada por estado (seletores .da / .na)
      2. /noticias/      — lista geral filtrada por keywords do CE (opcional)

    Args:
        incluir_noticias: Se True (padrão), também busca na página de notícias.

    Returns:
        Lista de editais únicos relacionados ao Ceará.
    """
    todos_editais: list[dict] = []

    # ── Fonte 1: /concursos/#CE ──────────────────────────────────────────────
    try:
        logger.info("Extraindo fonte 1: /concursos/#CE")
        html = _fetch_html(URL_CONCURSOS_CE)
        editais_ce = _extrair_editais_concursos_ce(html)
        todos_editais.extend(editais_ce)
    except Exception as e:
        logger.error(f"Falha ao extrair /concursos/#CE: {e}")

    # (A fonte 2 via `/noticias/` foi desativada pois não contém 
    # a estrutura de campos rigorosos para o novo formato do Discord)

    # ── Deduplicação local ───────────────────────────────────────────────────
    unicos = _deduplicar(todos_editais)
    logger.info(f"Total de editais únicos extraídos: {len(unicos)}")
    return unicos
