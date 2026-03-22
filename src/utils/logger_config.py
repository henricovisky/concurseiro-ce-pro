"""
logger_config.py
----------------
Configura um logger padronizado para saída no GitHub Actions.
As mensagens são formatadas em texto simples para aparecerem
corretamente nos logs do Actions (sem ANSI colors).
"""
import logging
import sys


def get_logger(name: str) -> logging.Logger:
    """
    Retorna um logger configurado para o módulo informado.

    Args:
        name: Nome do módulo/logger (use __name__ ao chamar).

    Returns:
        Instância de logging.Logger configurada.
    """
    logger = logging.getLogger(name)

    # Evita adicionar handlers duplicados em re-importações
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)

    # Formato compatível com GitHub Actions
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
