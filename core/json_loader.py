import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from config import DATA_DIR

logger = logging.getLogger(__name__)


class JsonLoader:
    """Carregador centralizado com cache de arquivos JSON de conteúdo."""

    _cache: Dict[str, Any] = {}

    @classmethod
    def load(cls, relative_path: str, force_reload: bool = False) -> Dict[str, Any]:
        """Carrega e retorna o conteúdo de um arquivo JSON dentro da pasta content/data/."""
        if not force_reload and relative_path in cls._cache:
            return cls._cache[relative_path]

        file_path = Path(DATA_DIR) / relative_path
        if not file_path.exists():
            logger.error(f"Arquivo JSON de conteúdo não encontrado: {file_path}")
            return {}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                cls._cache[relative_path] = data
                return data
        except Exception as e:
            logger.error(f"Erro ao ler JSON {file_path}: {e}")
            return {}

    @classmethod
    async def load_async(cls, relative_path: str, force_reload: bool = False) -> Dict[str, Any]:
        """Carrega JSON de forma assíncrona (não-blocking)."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            cls._load_sync,
            relative_path,
            force_reload,
        )

    @classmethod
    def _load_sync(cls, relative_path: str, force_reload: bool = False) -> Dict[str, Any]:
        """Versão síncrona do carregamento."""
        if not force_reload and relative_path in cls._cache:
            return cls._cache[relative_path]

        file_path = Path(DATA_DIR) / relative_path
        if not file_path.exists():
            logger.error(f"Arquivo JSON de conteúdo não encontrado: {file_path}")
            return {}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                cls._cache[relative_path] = data
                return data
        except Exception as e:
            logger.error(f"Erro ao ler JSON {file_path}: {e}")
            return {}


# Carrega o arquivo items.json uma única vez na inicialização do módulo
# Isso garante que Equipment.get_effective_stats() não precise ler do arquivo a cada chamada
_items_data_cache: Optional[Dict[str, Any]] = None


def _initialize_items_cache():
    """Carrega items.json uma vez ao importar o módulo."""
    global _items_data_cache
    if _items_data_cache is None:
        data = JsonLoader.load("items.json")
        _items_data_cache = data.get("items", {})
        logger.info(f"Items cache loaded: {len(_items_data_cache)} items")


# Inicializa o cache ao importar (executado quando o módulo é carregado)
_initialize_items_cache()


def get_items_data() -> Dict[str, Any]:
    """Retorna os dados de itens já carregados em memória."""
    return _items_data_cache or {}