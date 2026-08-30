import logging
from typing import Dict, Any, List, Tuple
from models.player import Player

logger = logging.getLogger(__name__)


class ProgressionSystem:
    """
    Sistema de Progressão de Nível, Atributos, Touki e Ranks da Guilda de Aventureiros.
    Ranks da Guilda: F -> E -> D -> C -> B -> A -> S
    """

    GUILD_RANKS = ["F", "E", "D", "C", "B", "A", "S"]
    GUILD_RANK_THRESHOLDS = {
        "F": 0,
        "E": 100,
        "D": 300,
        "C": 700,
        "B": 1500,
        "A": 3000,
        "S": 7000
    }

    @classmethod
    def add_xp(cls, player: Player, xp_amount: int) -> List[str]:
        """Adiciona experiência ao jogador e calcula level up se aplicável."""
        logs = []
        player.xp += xp_amount
        logs.append(f"✨ <b>+{xp_amount} XP</b> recebidos!")

        while player.xp >= player.xp_next_level:
            player.xp -= player.xp_next_level
            player.level += 1
            player.status_points += 4

            # Incrementos de Atributos Base por Nível
            hp_gain = 15
            mana_gain = 10 if player.vocation == "Mago" else 4
            
            player.max_hp += hp_gain
            player.hp = player.max_hp
            player.max_mana += mana_gain
            player.mana = player.max_mana

            # Despertar de Touki a partir do nível 3 para guerreiros/híbridos
            if player.level >= 3 and not player.has_touki_awakened and player.vocation in ["Espadachim", "Híbrido"]:
                player.has_touki_awakened = True
                player.max_touki = 30
                player.touki = 30
                logs.append("🔥 <b>[DESPERTAR DE TOUKI]</b> Você sentiu o fluxo de mana percorrer seus músculos! Seu corpo agora é revestido pelo manto de mana (Touki)!")

            # Nova meta de XP
            player.xp_next_level = int(player.xp_next_level * 1.45)
            logs.append(f"🎉 <b>SUBIU DE NÍVEL!</b> Você agora é <b>Nível {player.level}</b> (+4 Pontos de Status disponíveis)!")

        return logs

    @classmethod
    def add_guild_points(cls, player: Player, points: int) -> List[str]:
        """Adiciona pontos de reputação de guilda e avalia promoção de Rank de Aventureiro."""
        logs = []
        player.guild_points += points
        logs.append(f"🎖️ <b>+{points} Pontos de Guilda</b> obtidos!")

        current_idx = cls.GUILD_RANKS.index(player.adventurer_rank)
        if current_idx < len(cls.GUILD_RANKS) - 1:
            next_rank = cls.GUILD_RANKS[current_idx + 1]
            req_points = cls.GUILD_RANK_THRESHOLDS[next_rank]
            if player.guild_points >= req_points:
                player.adventurer_rank = next_rank
                logs.append(f"🏆 <b>PROMOÇÃO NA GUILDA!</b> Seu cartão de aventureiro foi promovido para o <b>Rank {next_rank}</b>!")

        return logs

    @classmethod
    def distribute_stat(cls, player: Player, stat_name: str, amount: int = 1) -> Tuple[bool, str]:
        """Distribui pontos de status disponíveis."""
        if player.status_points < amount:
            return False, "Você não possui pontos de status suficientes."

        stat_name = stat_name.lower()
        if stat_name in ["strength", "forca", "str"]:
            player.strength += amount
        elif stat_name in ["defense", "defesa", "def"]:
            player.defense += amount
        elif stat_name in ["speed", "velocidade", "spd"]:
            player.speed += amount
        elif stat_name in ["magic", "magia", "int"]:
            player.magic_power += amount
            player.max_mana += (amount * 5)
            player.mana += (amount * 5)
        elif stat_name in ["hp", "vida"]:
            player.max_hp += (amount * 10)
            player.hp += (amount * 10)
        else:
            return False, "Atributo desconhecido."

        player.status_points -= amount
        return True, f"Ponto adicionado com sucesso! Restam {player.status_points} pontos."
