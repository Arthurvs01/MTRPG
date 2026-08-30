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
    """

    @classmethod
    def _get_player_file(cls, chat_id: int) -> str:
        return os.path.join(PLAYERS_DIR, f"player_{chat_id}.json")

    @classmethod
    def player_exists(cls, chat_id: int) -> bool:
        """Verifica se existe registro de jogador para o chat_id."""
        return os.path.exists(cls._get_player_file(chat_id))

    @classmethod
    def save_player(cls, player: Player) -> bool:
        """
        Salva o jogador de forma atômica utilizando substituição segura de arquivo.
        """
        target_file = cls._get_player_file(player.chat_id)
        os.makedirs(os.path.dirname(target_file), exist_ok=True)

        try:
            # Escreve primeiro em arquivo temporário no mesmo diretório
            dir_name = os.path.dirname(target_file)
            with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, encoding="utf-8") as tf:
                json.dump(player.to_dict(), tf, indent=2, ensure_ascii=False)
                temp_name = tf.name

            # Substitui de forma atômica
            os.replace(temp_name, target_file)
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar jogador {player.chat_id}: {e}")
            return False

    @classmethod
    def get_player(cls, chat_id: int) -> Optional[Player]:
        """Carrega e retorna o objeto Player para o chat_id correspondente."""
        target_file = cls._get_player_file(chat_id)
        if not os.path.exists(target_file):
            return None

        try:
            with open(target_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return Player.from_dict(data)
        except Exception as e:
            logger.error(f"Erro ao carregar jogador {chat_id}: {e}")
            return None

    @classmethod
    def delete_player(cls, chat_id: int) -> bool:
        """Exclui o arquivo do jogador caso precise reiniciar o progresso."""
        target_file = cls._get_player_file(chat_id)
        if os.path.exists(target_file):
            try:
                os.remove(target_file)
                return True
            except Exception as e:
                logger.error(f"Erro ao deletar jogador {chat_id}: {e}")
        return False
