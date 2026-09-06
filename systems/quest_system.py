import logging
from typing import Dict, Any, Tuple, List
from models.player import Player
from database.quest_repo import QuestRepository
from systems.progression_system import ProgressionSystem

logger = logging.getLogger(__name__)


class QuestSystem:
    """
    Sistema de Gestão de Missões da Guilda de Aventureiros.
    Controla aceitação de contratos, atualização de progresso e resgate de recompensas.
    Limite: 1 missão ativa por vez, 3 missões diárias.
    """

    @classmethod
    def accept_quest(cls, player: Player, quest_id: str) -> Tuple[bool, str]:
        # Verifica se já atingiu o limite diário de conclusões
        if player.get_daily_quests_completed() >= 3:
            return False, "🚫 Você já concluiu o limite de 3 missões diárias hoje! Retorne amanhã para pegar novos contratos."

        quest = QuestRepository.get_quest_by_id(quest_id)
        if not quest:
            return False, "Missão não encontrada no quadro da Guilda."

        # Verifica se já está com a missão ativa
        for q in player.active_quests:
            if q.get("id") == quest_id:
                return False, "Você já aceitou este contrato."

        # Limite de 1 missão ativa por vez
        if len(player.active_quests) >= 1:
            return False, "Você só pode ter 1 missão ativa por vez. Complete ou abandone a atual primeiro."

        player.active_quests.append({
            "id": quest_id,
            "title": quest.title,
            "target_id": quest.target_id,
            "current_count": 0,
            "required_count": quest.required_count,
            "completed": False
        })
        return True, f"Contrato aceito: [{quest.title}]! Cumpra o objetivo e retorne à Guilda."

    @classmethod
    def update_kill_progress(cls, player: Player, monster_id: str) -> List[str]:
        """Atualiza o contador de abates das missões ativas."""
        logs = []
        for q in player.active_quests:
            if q.get("target_id") == monster_id and not q.get("completed", False):
                q["current_count"] = q.get("current_count", 0) + 1
                logs.append(f"📜 <b>Progresso do Contrato:</b> {q['title']} ({q['current_count']}/{q['required_count']})")
                if q["current_count"] >= q["required_count"]:
                    q["completed"] = True
                    logs.append(f"✅ <b>MISSÃO CONCLUÍDA:</b> [{q['title']}]! Retorne à Guilda de Aventureiros para receber sua recompensa!")
        return logs

    @classmethod
    def claim_rewards(cls, player: Player, quest_id: str) -> Tuple[bool, str]:
        if player.get_daily_quests_completed() >= 3:
            return False, "🚫 Você já concluiu o limite máximo de 3 missões diárias hoje! Retorne amanhã para resgatar mais recompensas."

        target_q = None
        for q in player.active_quests:
            if q.get("id") == quest_id:
                target_q = q
                break

        if not target_q:
            return False, "Missão não encontrada em seus registros."

        if not target_q.get("completed", False):
            return False, f"Objetivo ainda incompleto ({target_q.get('current_count', 0)}/{target_q.get('required_count', 1)})."

        quest_data = QuestRepository.get_quest_by_id(quest_id)
        if not quest_data:
            return False, "Dados da missão não encontrados."

        # Incrementa o contador de missões concluídas no dia
        player.increment_daily_quests_completed()

        # Entrega as recompensas
        player.iron_coins += quest_data.reward_iron_coins
        xp_logs = ProgressionSystem.add_xp(player, quest_data.reward_xp)
        guild_logs = ProgressionSystem.add_guild_points(player, quest_data.reward_guild_points)

        for item_id in quest_data.reward_items:
            consumables = player.inventory.setdefault("consumables", {})
            consumables[item_id] = consumables.get(item_id, 0) + 1

        # Remove da lista de ativas
        player.active_quests = [q for q in player.active_quests if q.get("id") != quest_id]

        reward_msg = (
            f"🎉 <b>Recompensa Resgatada com Sucesso!</b>\n"
            f"💰 +{quest_data.reward_iron_coins} Moedas de Ferro\n"
            + "\n".join(xp_logs) + "\n"
            + "\n".join(guild_logs) + "\n"
            f"📅 <b>Missões Concluídas Hoje:</b> {player.get_daily_quests_completed()}/3"
        )
        return True, reward_msg
