import asyncio
import logging
from pathlib import Path
from typing import Dict, Any
from config import TEXTS_DIR

logger = logging.getLogger(__name__)


class TextLoader:
    """
    Carregador e formatador centralizado de arquivos de texto narrativo (.txt).
    Permite templates externos com placeholders {variavel} para edição fácil sem alterar código.
    """

    _cache: Dict[str, str] = {}

    @classmethod
    def load(cls, filename: str, force_reload: bool = False, **kwargs) -> str:
        """
        Lê um arquivo de texto dentro de content/texts/ e formata os argumentos fornecidos.
        Exemplo: TextLoader.load("welcome.txt", character_name="Rudeus")
        """
        # Garante a extensão .txt
        if not filename.endswith(".txt"):
            filename = f"{filename}.txt"

        content = cls._cache.get(filename)
        if force_reload or content is None:
            file_path = Path(TEXTS_DIR) / filename
            if not file_path.exists():
                logger.warning(f"Arquivo de texto de template não encontrado: {file_path}")
                return ""

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    cls._cache[filename] = content
            except Exception as e:
                logger.error(f"Erro ao ler arquivo de texto {file_path}: {e}")
                return ""

        if kwargs:
            try:
                return content.format(**kwargs)
            except KeyError as e:
                logger.warning(f"Chave de formatação não fornecida no template {filename}: {e}")
                return content
            except Exception as e:
                logger.error(f"Erro ao formatar template {filename}: {e}")
                return content

        return content

    @classmethod
    async def load_async(cls, filename: str, force_reload: bool = False, **kwargs) -> str:
        """
        Versão assíncrona do load - não bloqueia o event loop.
        Usa run_in_executor para I/O de arquivo em thread separada.
        """
        loop = asyncio.get_running_loop()
        content = await loop.run_in_executor(
            None,
            cls._load_sync,
            filename,
            force_reload,
        )
        
        if kwargs:
            try:
                return content.format(**kwargs)
            except KeyError as e:
                logger.warning(f"Chave de formatação não fornecida no template {filename}: {e}")
                return content
            except Exception as e:
                logger.error(f"Erro ao formatar template {filename}: {e}")
                return content
        
        return content

    @classmethod
    def _load_sync(cls, filename: str, force_reload: bool = False) -> str:
        """Versão síncrona interna do carregamento."""
        if not filename.endswith(".txt"):
            filename = f"{filename}.txt"

        content = cls._cache.get(filename)
        if force_reload or content is None:
            file_path = Path(TEXTS_DIR) / filename
            if not file_path.exists():
                logger.warning(f"Arquivo de texto de template não encontrado: {file_path}")
                return ""

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    cls._cache[filename] = content
            except Exception as e:
                logger.error(f"Erro ao ler arquivo de texto {file_path}: {e}")
                return ""

        return content
