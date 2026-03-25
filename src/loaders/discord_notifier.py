"""
discord_notifier.py
-------------------
Camada de Carga (L) do ETL — Envio de notificações via Discord Webhook.
Responsável por formatar e enviar embeds ricos no Discord para cada novo
edital encontrado pelo pipeline.
"""
import os
from datetime import datetime
from typing import Optional

import requests
from dotenv import load_dotenv

from src.utils.logger_config import get_logger

load_dotenv()

logger = get_logger(__name__)

REQUEST_TIMEOUT = 10  # segundos


def _get_webhook_url() -> str:
    """Retorna a URL do webhook Discord a partir das variáveis de ambiente."""
    url = os.getenv("DISCORD_WEBHOOK_URL")
    if not url:
        raise EnvironmentError(
            "Variável de ambiente DISCORD_WEBHOOK_URL é obrigatória."
        )
    if "api/webhooks/..." in url or url.endswith("..."):
        raise ValueError(
            "ERRO: A URL do Discord Webhook no seu arquivo .env ainda contém o placeholder '...'. "
            "Por favor, substitua pelo link real completo gerado no seu canal do Discord."
        )
    return url


def _formatar_remuneracao(valor: Optional[float]) -> str:
    """Formata o valor de remuneração em R$ ou retorna 'Não informado'."""
    if valor is None:
        return "Não informado"
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return "Não informado"


def _formatar_data(data_str: Optional[str]) -> str:
    """Converte data YYYY-MM-DD para formato brasileiro DD/MM/YYYY."""
    if not data_str:
        return "Não informado"
    try:
        dt = datetime.strptime(str(data_str), "%Y-%m-%d")
        return dt.strftime("%d/%m/%Y")
    except ValueError:
        return str(data_str)


def _construir_payload(edital: dict) -> dict:
    """
    Constrói o payload JSON do webhook Discord com embed formatado.

    Args:
        edital: Dicionário com os dados do edital.

    Returns:
        Payload formatado para a API do Discord.
    """
    titulo = edital.get("titulo", "Novo Edital")
    instituicao = edital.get("instituicao", "Não identificado")
    informacoes = edital.get("informacoes", "Não informado")
    escolaridade = edital.get("escolaridade", "Não informada")
    inscricao_ate = edital.get("inscricao_ate", "Não informado")
    link = edital.get("link_original", "")

    embed = {
        "title": f"📋 {titulo[:250]}",  # Discord limita título em 256 chars
        "url": link,
        "color": 0x1E90FF,  # Azul dodger
        "fields": [
            {
                "name": "🏛️ Instituição",
                "value": instituicao or "Não identificado",
                "inline": False,
            },
            {
                "name": "ℹ️ Informações",
                "value": informacoes or "Não informado",
                "inline": False,
            },
            {
                "name": "🎓 Escolaridade",
                "value": escolaridade or "Não informada",
                "inline": True,
            },
            {
                "name": "📅 Inscrição até",
                "value": inscricao_ate or "Não informado",
                "inline": True,
            },
            {
                "name": "🔗 Edital Completo",
                "value": f"[Clique aqui para acessar]({link})" if link else "—",
                "inline": False,
            },
        ],
        "footer": {
            "text": "🤖 Radar CE Pro",
        },
        "timestamp": datetime.utcnow().isoformat(),
    }

    return {
        "username": "Radar CE Pro",
        "avatar_url": "https://cdn-icons-png.flaticon.com/512/3281/3281307.png",
        "embeds": [embed],
    }


def notificar(edital: dict) -> bool:
    """
    Envia a notificação de um edital para o canal Discord configurado.

    Args:
        edital: Dicionário com os dados completos do edital.

    Returns:
        True se o webhook foi enviado com sucesso (HTTP 204), False caso contrário.
    """
    try:
        webhook_url = _get_webhook_url()
    except EnvironmentError as e:
        logger.error(str(e))
        return False

    payload = _construir_payload(edital)
    titulo_curto = edital.get("titulo", "?")[:60]

    try:
        response = requests.post(
            webhook_url,
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )

        if response.status_code == 204:
            logger.info(f"✅ Notificação enviada: {titulo_curto}")
            return True
        else:
            logger.error(
                f"❌ Falha no Discord (HTTP {response.status_code}): {titulo_curto}"
                f" — {response.text[:200]}"
            )
            return False

    except requests.Timeout:
        logger.error(f"Timeout ao notificar Discord: {titulo_curto}")
        return False
    except requests.RequestException as e:
        logger.error(f"Erro na requisição ao Discord: {e}")
        return False


def notificar_resumo(total_novos: int, total_processados: int) -> None:
    """
    Envia uma mensagem de resumo da execução do pipeline ao Discord.
    Útil para monitorar a saúde do pipeline diário.

    Args:
        total_novos: Quantidade de editais novos encontrados.
        total_processados: Total de editais analisados pelo pipeline.
    """
    try:
        webhook_url = _get_webhook_url()
    except EnvironmentError:
        return

    emoji = "🟢" if total_novos > 0 else "🔵"
    mensagem = (
        f"{emoji} **Pipeline Concluído** — "
        f"`{total_novos}` edital(is) novo(s) de `{total_processados}` analisado(s)."
    )

    try:
        requests.post(
            webhook_url,
            json={"content": mensagem, "username": "Radar CE Pro"},
            timeout=REQUEST_TIMEOUT,
        )
    except Exception as e:
        logger.warning(f"Falha ao enviar resumo ao Discord: {e}")
