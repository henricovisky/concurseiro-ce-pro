"""
hash_generator.py
-----------------
Gerador de hashes MD5 para garantir idempotência no pipeline.
O hash é usado como identificador único de cada edital,
evitando duplicatas no Supabase e reenvios ao Discord.
"""
import hashlib


def gerar_hash(texto: str) -> str:
    """
    Gera um hash MD5 hexadecimal a partir de um texto.

    Utilizado para criar o `hash_identificador` de editais e
    publicações de diários oficiais. A URL ou título do edital
    é o input preferencial para garantir unicidade.

    Args:
        texto: String base para gerar o hash (URL ou título).

    Returns:
        Hash MD5 em formato hexadecimal (32 caracteres).

    Example:
        >>> gerar_hash("https://exemplo.com/edital-123")
        'a1b2c3d4e5f6...'
    """
    if not texto or not isinstance(texto, str):
        raise ValueError("O texto para gerar o hash não pode ser vazio ou nulo.")

    return hashlib.md5(texto.strip().encode("utf-8")).hexdigest()
