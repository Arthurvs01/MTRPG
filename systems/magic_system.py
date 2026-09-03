import logging
from typing import Dict, List, Optional, Tuple
from models.player import Player
from models.skill import Spell
from core.json_loader import JsonLoader

logger = logging.getLogger(__name__)


class MagicSystem:
    """
    Sistema Canônico de Magia de Mushoku Tensei.
    Gerencia feitiços elementais (Fogo, Água, Terra, Vento), cura/desintoxicação,
    progressão de Ranks (Iniciante a Divino) e a mecânica de Conjuração Silenciosa.
    """

    RANKS = ["Iniciante", "Intermediário", "Avançado", "Santo", "Rei", "Imperial", "Divino"]

    @classmethod
    def get_spell(cls, spell_id: str) -> Optional[Spell]:
        data = JsonLoader.load("spells.json")
        spells = data.get("spells", {})
        if spell_id in spells:
            s_data = dict(spells[spell_id])
            s_data["id"] = spell_id
            return Spell.from_dict(s_data)
        return None

    @classmethod
    def get_all_spells(cls) -> Dict[str, Spell]:
        data = JsonLoader.load("spells.json")
        spells_dict = data.get("spells", {})
        result = {}
        for s_id, s_data in spells_dict.items():
            s_copy = dict(s_data)
            s_copy["id"] = s_id
            result[s_id] = Spell.from_dict(s_copy)
        return result

    @classmethod
    def can_learn_spell(cls, player: Player, spell: Spell) -> Tuple[bool, str]:
        """Verifica se o jogador atende aos requisitos de rank e afinidade elemental."""
        player_rank = player.magic_schools.get(spell.element, "Nenhum")
        if player_rank == "Nenhum":
            return False, f"Você não possui aptidão na escola de magia de {spell.element}."

        try:
            player_idx = cls.RANKS.index(player_rank)
            spell_idx = cls.RANKS.index(spell.rank)
            if player_idx < spell_idx:
                return False, f"Seu rank em {spell.element} ({player_rank}) é inferior ao necessário ({spell.rank})."
        except ValueError:
            return False, "Rank inválido."

        if spell.id in player.known_spells:
            return False, "Você já domina este feitiço."

        return True, "Apto para aprender o feitiço."

    @classmethod
    def learn_spell(cls, player: Player, spell_id: str) -> Tuple[bool, str]:
        spell = cls.get_spell(spell_id)
        if not spell:
            return False, "Feitiço não encontrado."

        can_learn, msg = cls.can_learn_spell(player, spell)
        if not can_learn:
            return False, msg

        player.known_spells.append(spell_id)
        return True, f"Parabéns! Você aprendeu o feitiço [{spell.name}] de rank {spell.rank}!"
