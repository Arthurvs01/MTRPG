import asyncio
import json
import os
import tempfile
import logging
from typing import Optional, List, Dict, Any
from config import PARTIES_DIR
from models.party import Party

logger = logging.getLogger(__name__)


class PartyRepository:
    """
    Repositório de Persistência para Grupos de Aventureiros (Parties).
    Utiliza persistência atômica em arquivos JSON para evitar corrupção de dados.
    Operações de arquivo são assíncronas usando asyncio.to_thread para não bloquear o event loop.
    """

    @classmethod
    def _get_party_file(cls, party_id: str) -> str:
        return os.path.join(PARTIES_DIR, f"party_{party_id}.json")

    @classmethod
    def party_exists(cls, party_id: str) -> bool:
        """Verifica se existe registro de grupo para o party_id."""
        return os.path.exists(cls._get_party_file(party_id))

    @classmethod
    async def save_party(cls, party: Party) -> bool:
        """
        Salva o grupo de forma atômica em arquivo JSON.
        Executa em thread separado para não bloquear o event loop.
        """
        target_file = cls._get_party_file(party.party_id)
        os.makedirs(os.path.dirname(target_file), exist_ok=True)

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                cls._save_party_sync,
                party,
                target_file,
            )
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar grupo {party.party_id}: {e}")
            return False

    @classmethod
    def save_party_sync(cls, party: Party) -> bool:
        """Versão síncrona pública para salvar o grupo."""
        target_file = cls._get_party_file(party.party_id)
        os.makedirs(os.path.dirname(target_file), exist_ok=True)
        return cls._save_party_sync(party, target_file)

    @classmethod
    def _save_party_sync(cls, party: Party, target_file: str) -> bool:
        """Versão síncrona do salvamento (executada em thread separado)."""
        try:
            dir_name = os.path.dirname(target_file)
            with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, encoding="utf-8") as tf:
                json.dump(party.to_dict(), tf, indent=2, ensure_ascii=False)
                temp_name = tf.name
            os.replace(temp_name, target_file)
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar grupo {party.party_id} (sync): {e}")
            return False

    @classmethod
    async def save_party_async(cls, party: Party) -> bool:
        """Alias para compatibilidade assíncrona."""
        return await cls.save_party(party)

    @classmethod
    async def get_party_async(cls, party_id: str) -> Optional[Party]:
        """Alias para compatibilidade assíncrona."""
        return await cls.get_party(party_id)

    @classmethod
    async def get_party(cls, party_id: str) -> Optional[Party]:
        """Carrega e retorna o objeto Party para o party_id correspondente."""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, cls._get_party_sync, party_id)
        except Exception as e:
            logger.error(f"Erro ao carregar grupo {party_id}: {e}")
            return None

    @classmethod
    def _get_party_sync(cls, party_id: str) -> Optional[Party]:
        """Versão síncrona do carregamento (executada em thread separado)."""
        target_file = cls._get_party_file(party_id)
        if not os.path.exists(target_file):
            return None

        try:
            with open(target_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return Party.from_dict(data)
        except Exception as e:
            logger.error(f"Erro ao carregar grupo {party_id} (sync): {e}")
            return None

    @classmethod
    def get_party_sync(cls, party_id: str) -> Optional[Party]:
        """Versão síncrona pública para carregar o grupo."""
        return cls._get_party_sync(party_id)

    @classmethod
    async def delete_party(cls, party_id: str) -> bool:
        """Exclui o arquivo do grupo."""
        target_file = cls._get_party_file(party_id)
        if os.path.exists(target_file):
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, cls._delete_party_sync, target_file)
                return True
            except Exception as e:
                logger.error(f"Erro ao deletar grupo {party_id}: {e}")
        return False

    @classmethod
    def _delete_party_sync(cls, target_file: str) -> None:
        """Versão síncrona da exclusão (executada em thread separado)."""
        try:
            os.remove(target_file)
        except Exception as e:
            logger.error(f"Erro ao deletar arquivo {target_file} (sync): {e}")

    @classmethod
    async def load_all_parties(cls) -> List[Party]:
        """Carrega todos os grupos salvos em disco."""
        parties = []
        if not os.path.exists(PARTIES_DIR):
            return parties

        try:
            for filename in os.listdir(PARTIES_DIR):
                if filename.startswith("party_") and filename.endswith(".json"):
                    party_id = filename[6:-5]  # Remove "party_" e ".json"
                    party = await cls.get_party(party_id)
                    if party:
                        parties.append(party)
        except Exception as e:
            logger.error(f"Erro ao carregar todos os grupos: {e}")

        return parties

    @classmethod
    def load_all_parties_sync(cls) -> List[Party]:
        """Versão síncrona para carregar todos os grupos na inicialização."""
        parties = []
        if not os.path.exists(PARTIES_DIR):
            return parties

        try:
            for filename in os.listdir(PARTIES_DIR):
                if filename.startswith("party_") and filename.endswith(".json"):
                    party_id = filename[6:-5]
                    party = cls.get_party_sync(party_id)
                    if party:
                        parties.append(party)
        except Exception as e:
            logger.error(f"Erro ao carregar todos os grupos (sync): {e}")

        return parties