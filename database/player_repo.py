import asyncio
import json
import os
import tempfile
import logging
from typing import Optional, List
from config import PLAYERS_DIR
from models.player import Player

logger = logging.getLogger(__name__)


class PlayerRepository:
    """
    Repositório de Persistência para Jogadores (Aventureiros).
    Utiliza persistência atômica em arquivos JSON para evitar corrupção de dados.
    Operações de arquivo são assíncronas usando asyncio.to_thread para não bloquear o event loop.
    """

    @classmethod
    def _get_player_file(cls, chat_id: int) -> str:
        return os.path.join(PLAYERS_DIR, f"player_{chat_id}.json")

    @classmethod
    def player_exists(cls, chat_id: int) -> bool:
        """Verifica se existe registro de jogador para o chat_id."""
        return os.path.exists(cls._get_player_file(chat_id))

    @classmethod
    async def save_player(cls, player: Player) -> bool:
        """
        Salva o jogador de forma atômica em arquivo JSON.
        Executa em thread separado para não bloquear o event loop.
        """
        target_file = cls._get_player_file(player.chat_id)
        os.makedirs(os.path.dirname(target_file), exist_ok=True)

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                cls._save_player_sync,
                player,
                target_file,
            )
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar jogador {player.chat_id}: {e}")
            return False

    @classmethod
    def _save_player_sync(cls, player: Player, target_file: str) -> None:
        """Versão síncrona do salvamento (executada em thread separado)."""
        try:
            dir_name = os.path.dirname(target_file)
            with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, encoding="utf-8") as tf:
                json.dump(player.to_dict(), tf, indent=2, ensure_ascii=False)
                temp_name = tf.name
            os.replace(temp_name, target_file)
        except Exception as e:
            logger.error(f"Erro ao salvar jogador {player.chat_id} (sync): {e}")

    @classmethod
    async def get_player(cls, chat_id: int) -> Optional[Player]:
        """Carrega e retorna o objeto Player para o chat_id correspondente."""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, cls._get_player_sync, chat_id)
        except Exception as e:
            logger.error(f"Erro ao carregar jogador {chat_id}: {e}")
            return None

    @classmethod
    def _get_player_sync(cls, chat_id: int) -> Optional[Player]:
        """Versão síncrona do carregamento (executada em thread separado)."""
        target_file = cls._get_player_file(chat_id)
        if not os.path.exists(target_file):
            return None

        try:
            with open(target_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return Player.from_dict(data)
        except Exception as e:
            logger.error(f"Erro ao carregar jogador {chat_id} (sync): {e}")
            return None

    @classmethod
    async def delete_player(cls, chat_id: int) -> bool:
        """Exclui o arquivo do jogador caso precise reiniciar o progresso."""
        target_file = cls._get_player_file(chat_id)
        if os.path.exists(target_file):
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, cls._delete_player_sync, target_file)
                return True
            except Exception as e:
                logger.error(f"Erro ao deletar jogador {chat_id}: {e}")
        return False

    @classmethod
    def _delete_player_sync(cls, target_file: str) -> None:
        """Versão síncrona da exclusão (executada em thread separado)."""
        try:
            os.remove(target_file)
        except Exception as e:
            logger.error(f"Erro ao deletar arquivo {target_file} (sync): {e}")