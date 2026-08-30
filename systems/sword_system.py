import logging
from typing import Dict, List, Optional, Tuple
from models.player import Player
from models.skill import SwordSkill
from core.json_loader import JsonLoader

logger = logging.getLogger(__name__)


class SwordSystem:
    """
    Sistema Canônico dos 3 Grandes Estilos de Espada:
    - Estilo Deus da Espada (Sword God Style)
    - Estilo Deus da Água (Water God Style)
    - Estilo Deus do Norte (North God Style)
    """

    RANKS = ["Iniciante", "Intermediário", "Avançado", "Santo", "Rei", "Imperial", "Divino"]

    @classmethod
    def get_sword_skill(cls, skill_id: str) -> Optional[SwordSkill]:
        data = JsonLoader.load("sword_skills.json")
        skills = data.get("sword_skills", {})
        if skill_id in skills:
            s_data = dict(skills[skill_id])
            s_data["id"] = skill_id
            return SwordSkill.from_dict(s_data)
        return None

    @classmethod
    def can_learn_skill(cls, player: Player, skill: SwordSkill) -> Tuple[bool, str]:
        player_rank = player.sword_styles.get(skill.style, "Nenhum")
        if player_rank == "Nenhum":
            return False, f"Você não iniciou os treinos no estilo {skill.style}."

        try:
            player_idx = cls.RANKS.index(player_rank)
            skill_idx = cls.RANKS.index(skill.rank)
            if player_idx < skill_idx:
                return False, f"Seu rank no estilo {skill.style} ({player_rank}) é inferior ao necessário ({skill.rank})."
        except ValueError:
            return False, "Rank de espada inválido."

        if skill.id in player.known_sword_skills:
            return False, "Você já domina esta técnica de espada."

        return True, "Apto para aprender."

    @classmethod
    def learn_sword_skill(cls, player: Player, skill_id: str) -> Tuple[bool, str]:
        skill = cls.get_sword_skill(skill_id)
        if not skill:
            return False, "Técnica de espada não encontrada."

        can_learn, msg = cls.can_learn_skill(player, skill)
        if not can_learn:
            return False, msg

        player.known_sword_skills.append(skill_id)
        return True, f"Você dominou a técnica [{skill.name}] do estilo {skill.style}!"
