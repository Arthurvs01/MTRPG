import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional
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
