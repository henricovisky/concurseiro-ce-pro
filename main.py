"""
main.py
-------
Ponto de entrada do pipeline ETL — Concurseiro CE Pro (Módulo 1: Radar de Editais).
Orquestra as três camadas: Extração → Transformação → Carga.

Uso:
    python main.py                     # Execução padrão
    python main.py --com-noticias      # Inclui extração da página de notícias

GitHub Actions executa este script via CRON diário.
"""
import argparse
import sys

from dotenv import load_dotenv

from src.extractors import rss_concursos
from src.transformers import filtros_pandas
from src.loaders import supabase_client, discord_notifier
from src.utils.logger_config import get_logger

load_dotenv()

logger = get_logger(__name__)

def _limpar_nan_dict(d: dict) -> dict:
    """Converte valores NaN do Pandas para None do Python (necessário para JSON)."""
    import pandas as pd
    return {k: (None if pd.isna(v) else v) for k, v in d.items()}


def executar_pipeline(incluir_noticias: bool = False) -> None:
    """
    Executa o pipeline ETL completo do Radar de Editais.

    Args:
        incluir_noticias: Se True, inclui extração da página de notícias do PCI.
    """
    logger.info("=" * 60)
    logger.info("🚀 Iniciando Pipeline — Radar de Editais CE Pro")
    logger.info("=" * 60)

    total_processados = 0
    total_novos = 0

    # ── ETAPA 1: EXTRAÇÃO ─────────────────────────────────────────────────────
    logger.info("📡 [E] Extração: buscando editais no PCI Concursos...")
    editais_brutos = rss_concursos.extrair(incluir_noticias=incluir_noticias)

    if not editais_brutos:
        logger.warning("Nenhum edital encontrado na extração. Pipeline encerrado.")
        discord_notifier.notificar_resumo(0, 0)
        return

    total_processados = len(editais_brutos)
    logger.info(f"✅ {total_processados} edital(is) extraído(s).")

    # ── ETAPA 2: TRANSFORMAÇÃO ────────────────────────────────────────────────
    logger.info("🔧 [T] Transformação: limpando e normalizando dados...")
    df = filtros_pandas.processar(editais_brutos)

    if df.empty:
        logger.warning("DataFrame vazio após transformação. Pipeline encerrado.")
        discord_notifier.notificar_resumo(0, total_processados)
        return

    # ── ETAPA 3: VERIFICAR IDEMPOTÊNCIA ───────────────────────────────────────
    logger.info("🛡️ [L] Verificando idempotência no Supabase...")
    df_novos = df[
        ~df["hash_identificador"].apply(supabase_client.hash_ja_existe)
    ].copy()

    if df_novos.empty:
        logger.info("✅ Sem novidades — todos os editais já foram processados.")
        discord_notifier.notificar_resumo(0, total_processados)
        return

    logger.info(f"🆕 {len(df_novos)} edital(is) novo(s) para processar.")

    # ── ETAPA 4: CARGA E NOTIFICAÇÃO ──────────────────────────────────────────
    logger.info("💾 [L] Carga: persistindo no Supabase e notificando Discord...")

    for _, row in df_novos.iterrows():
        # Limpa NaN para evitar erros de serialização JSON
        edital = _limpar_nan_dict(row.to_dict())
        hash_id = edital.get("hash_identificador")

        # Prepara o payload para o Supabase (remove campos do DataFrame)
        payload_supabase = {
            "hash_identificador": hash_id,
            "titulo": edital.get("titulo"),
            "instituicao": edital.get("instituicao"),
            "informacoes": edital.get("informacoes"),
            "escolaridade": edital.get("escolaridade"),
            "inscricao_ate": edital.get("inscricao_ate"),
            "link_original": edital.get("link_original"),
            "notificado_discord": False,
        }

        # Inserir no Supabase
        inserido = supabase_client.inserir_edital(payload_supabase)

        if inserido:
            total_novos += 1
            # Notificar no Discord
            notificado = discord_notifier.notificar(edital)
            if notificado:
                supabase_client.marcar_como_notificado(hash_id)

    # ── RESUMO FINAL ──────────────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info(
        f"🏁 Pipeline concluído — "
        f"{total_novos} novo(s) de {total_processados} analisado(s)."
    )
    logger.info("=" * 60)

    discord_notifier.notificar_resumo(total_novos, total_processados)


def main():
    parser = argparse.ArgumentParser(
        description="Concurseiro CE Pro — Radar de Editais (Pipeline ETL)"
    )
    parser.add_argument(
        "--com-noticias",
        action="store_true",
        help="Incluir extração da página de notícias do PCI Concursos",
    )
    args = parser.parse_args()

    try:
        executar_pipeline(incluir_noticias=args.com_noticias)
    except KeyboardInterrupt:
        logger.warning("Pipeline interrompido pelo usuário.")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Erro crítico não tratado no pipeline: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
