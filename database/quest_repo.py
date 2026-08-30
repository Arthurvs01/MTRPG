import logging
from typing import Dict, List, Optional
from core.json_loader import JsonLoader
from models.quest import Quest

logger = logging.getLogger(__name__)


class QuestRepository:
    """Repositório de Missões da Guilda de Aventureiros por Rank e Continente."""

    @classmethod
    def get_quest_by_id(cls, quest_id: str) -> Optional[Quest]:
        data = JsonLoader.load("quests.json")
        quests = data.get("quests", {})
        if quest_id in quests:
            q_data = quests[quest_id]
            q_data["id"] = quest_id
            return Quest.from_dict(q_data)
        return None

    @classmethod
    def get_available_quests(cls, player_rank: str, region: str = "all") -> List[Quest]:
        """Retorna missões disponíveis compatíveis com o Rank do Aventureiro."""
        data = JsonLoader.load("quests.json")
        quests_dict = data.get("quests", {})
        
        # Ordem dos Ranks
        rank_order = ["F", "E", "D", "C", "B", "A", "S"]
        try:
            player_rank_idx = rank_order.index(player_rank.upper())
        except ValueError:
            player_rank_idx = 0

        available = []
        for q_id, q_data in quests_dict.items():
            q_rank = q_data.get("rank", "F").upper()
            q_region = q_data.get("region", "all")

            q_rank_idx = rank_order.index(q_rank) if q_rank in rank_order else 0

            # O aventureiro pode pegar quests do seu rank ou ranks inferiores (ou até 1 rank acima na lore)
            if q_rank_idx <= player_rank_idx + 1:
                if region == "all" or q_region == "all" or q_region.lower() == region.lower():
                    q_data_copy = dict(q_data)
                    q_data_copy["id"] = q_id
                    available.append(Quest.from_dict(q_data_copy))

        return available
