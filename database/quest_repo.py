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
    def normalize_region(cls, region: str) -> str:
        """Normaliza nomes de continentes e regiões para 'fittoa' ou 'rikarisu'."""
        r = region.lower().strip()
        if "fittoa" in r or "central" in r or "buena" in r:
            return "fittoa"
        if "rikarisu" in r or "demon" in r:
            return "rikarisu"
        return r

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

        target_region = cls.normalize_region(region) if region != "all" else "all"

        available = []
        for q_id, q_data in quests_dict.items():
            q_rank = q_data.get("rank", "F").upper()
            raw_q_region = q_data.get("region", "all")
            q_region = cls.normalize_region(raw_q_region) if raw_q_region != "all" else "all"

            q_rank_idx = rank_order.index(q_rank) if q_rank in rank_order else 0

            # O aventureiro pode pegar quests do seu rank ou ranks inferiores (ou até 1 rank acima na lore)
            if q_rank_idx <= player_rank_idx + 1:
                if target_region == "all" or q_region == "all" or q_region == target_region:
                    q_data_copy = dict(q_data)
                    q_data_copy["id"] = q_id
                    available.append(Quest.from_dict(q_data_copy))

        return available

    @classmethod
    def get_daily_board_quests(cls, player, region: str = "fittoa") -> List[Quest]:
        """
        Retorna 4 missões sorteadas para o dia atual para o jogador na região especificada.
        Se já houver sorteio válido para hoje na região, retorna as mesmas 4 missões.
        Caso contrário, sorteia 4 missões aleatoriamente dentre as 20 da região.
        """
        import random
        norm_region = cls.normalize_region(region)
        today = player.get_today_str()

        board_data = getattr(player, "daily_quests_board", {})
        if not isinstance(board_data, dict):
            board_data = {}
            player.daily_quests_board = board_data

        board_date = board_data.get("date")
        cached_ids = board_data.get(norm_region, [])

        # Se mudou de dia, reseta todo o board
        if board_date != today:
            board_data.clear()
            board_data["date"] = today
            cached_ids = []

        valid_quests = []
        if cached_ids and len(cached_ids) == 4:
            for q_id in cached_ids:
                q = cls.get_quest_by_id(q_id)
                if q:
                    valid_quests.append(q)

        # Se já tiver as 4 válidas, retorna elas
        if len(valid_quests) == 4:
            return valid_quests

        # Caso contrário, sorteia 4 missões da região
        available = cls.get_available_quests(player.adventurer_rank, region=norm_region)
        if len(available) < 4:
            # Fallback: pega todas as missões da região para completar 4
            all_region_quests = []
            data = JsonLoader.load("quests.json")
            for q_id, q_data in data.get("quests", {}).items():
                if cls.normalize_region(q_data.get("region", "")) == norm_region:
                    q_copy = dict(q_data)
                    q_copy["id"] = q_id
                    all_region_quests.append(Quest.from_dict(q_copy))
            available = all_region_quests

        if len(available) >= 4:
            selected = random.sample(available, 4)
        else:
            selected = available

        board_data[norm_region] = [q.id for q in selected]
        board_data["date"] = today
        return selected
