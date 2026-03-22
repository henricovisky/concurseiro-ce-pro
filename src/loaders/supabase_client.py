"""
supabase_client.py
------------------
Camada de acesso ao banco de dados Supabase (PostgreSQL).
Responsável por:
  - Verificar idempotência (hash já processado?)
  - Inserir novos editais
  - Marcar editais como notificados no Discord
"""
import os
from typing import Optional

from supabase import create_client, Client
from dotenv import load_dotenv

from src.utils.logger_config import get_logger

load_dotenv()

logger = get_logger(__name__)

TABLE_RADAR = "radar_editais"


def _get_client() -> Client:
    """Cria e retorna um cliente Supabase autenticado."""
    url: Optional[str] = os.getenv("SUPABASE_URL")
    key: Optional[str] = os.getenv("SUPABASE_KEY")

    if not url or not key:
        raise EnvironmentError(
            "Variáveis de ambiente SUPABASE_URL e SUPABASE_KEY são obrigatórias."
        )

    return create_client(url, key)


def hash_ja_existe(hash_id: str) -> bool:
    """
    Verifica se um hash já foi processado anteriormente.
    Garante idempotência: o mesmo edital não será reprocessado.

    Args:
        hash_id: Hash MD5 do edital a verificar.

    Returns:
        True se já existe no banco, False caso contrário.
    """
    try:
        client = _get_client()
        response = (
            client.table(TABLE_RADAR)
            .select("hash_identificador")
            .eq("hash_identificador", hash_id)
            .limit(1)
            .execute()
        )
        existe = len(response.data) > 0
        logger.debug(f"Hash {'encontrado' if existe else 'não encontrado'}: {hash_id}")
        return existe
    except Exception as e:
        logger.error(f"Erro ao verificar hash no Supabase: {e}")
        # Em caso de erro, assume que não existe para não bloquear o pipeline
        return False


def inserir_edital(dados: dict) -> bool:
    """
    Insere um novo edital na tabela radar_editais.

    Args:
        dados: Dicionário com os campos do edital. Campos esperados:
               hash_identificador, orgao_banca, cargo_principal,
               remuneracao_maxima, data_prova, link_original, resumo_ia.

    Returns:
        True se inserção bem-sucedida, False caso contrário.
    """
    try:
        client = _get_client()
        client.table(TABLE_RADAR).insert(dados).execute()
        logger.info(f"Edital inserido: {dados.get('link_original', 'sem link')}")
        return True
    except Exception as e:
        logger.error(f"Erro ao inserir edital no Supabase: {e}")
        return False


def marcar_como_notificado(hash_id: str) -> bool:
    """
    Atualiza o flag notificado_discord para TRUE após envio no Discord.

    Args:
        hash_id: Hash MD5 do edital que foi notificado.

    Returns:
        True se atualização bem-sucedida, False caso contrário.
    """
    try:
        client = _get_client()
        client.table(TABLE_RADAR).update({"notificado_discord": True}).eq(
            "hash_identificador", hash_id
        ).execute()
        logger.info(f"Edital marcado como notificado: {hash_id}")
        return True
    except Exception as e:
        logger.error(f"Erro ao marcar edital como notificado: {e}")
        return False


def buscar_pendentes_notificacao() -> list[dict]:
    """
    Retorna editais já inseridos mas ainda não notificados no Discord.
    Útil para re-tentativas em caso de falha no envio anterior.

    Returns:
        Lista de dicionários com os editais pendentes.
    """
    try:
        client = _get_client()
        response = (
            client.table(TABLE_RADAR)
            .select("*")
            .eq("notificado_discord", False)
            .execute()
        )
        logger.info(f"{len(response.data)} edital(is) pendente(s) de notificação.")
        return response.data
    except Exception as e:
        logger.error(f"Erro ao buscar editais pendentes: {e}")
        return []
