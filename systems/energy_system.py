import time
import logging
from typing import Tuple
from models.player import Player

logger = logging.getLogger(__name__)


class EnergySystem:
    """
    Sistema Central de Energia e Vigor de Ação.
    Controla os custos de expedições/caçadas, treinos e os métodos de recuperação na Estalagem.
    """

    HUNT_ENERGY_COST = 15
    TRAINING_ENERGY_COST = 20

    @classmethod
    def can_perform_action(cls, player: Player, cost: int) -> Tuple[bool, str]:
        """Verifica se o jogador possui energia suficiente."""
        player.regen_energy_passively()
        if player.energy >= cost:
            return True, "Energia suficiente."
        return False, f"Energia insuficiente ({player.energy}/{cost}). Descanse na Estalagem ou aguarde a regeneração."

    @classmethod
    def consume(cls, player: Player, cost: int) -> bool:
        """Consome a energia se disponível."""
        return player.consume_energy(cost)

    @classmethod
    def rest_inn_simple(cls, player: Player) -> Tuple[bool, str]:
        """Descanso em quarto simples - Recupera apenas energia (Custo: 20 moedas de ferro)."""
        if not player.can_use_inn():
            return False, "🚫 Você já usou a Estalagem 2 vezes hoje! Retorne amanhã."

        cost = 20
        if player.iron_coins < cost:
            return False, f"Moedas insuficientes ({player.iron_coins}/{cost} Ferros)."

        player.iron_coins -= cost
        player.energy = min(player.max_energy, player.energy + 50)
        player.increment_inn_use()
        return True, "Você descansou no quarto simples! Energia recuperada: +50 ⚡"

    @classmethod
    def rest_inn_luxury(cls, player: Player) -> Tuple[bool, str]:
        """Descanso em suíte nobre - Recupera energia total (Custo: 50 moedas de ferro)."""
        if not player.can_use_inn():
            return False, "🚫 Você já usou a Estalagem 2 vezes hoje! Retorne amanhã."

        cost = 50
        if player.iron_coins < cost:
            return False, f"Moedas insuficientes ({player.iron_coins}/{cost} Ferros)."

        player.iron_coins -= cost
        player.energy = player.max_energy
        player.increment_inn_use()
        return True, "Você desfrutou da suíte nobre! Energia de Ação 100% restaurada!"

    @classmethod
    def recharge_with_diamonds(cls, player: Player) -> Tuple[bool, str]:
        """Restauração instantânea de energia com Diamantes (Custo: 10 diamantes)."""
        cost = 10
        if player.diamonds < cost:
            return False, f"Diamantes insuficientes ({player.diamonds}/{cost} 💎)."

        player.diamonds -= cost
        player.energy = player.max_energy
        return True, "Um elixir divino revigorou suas forças instantaneamente! Energia 100% recarregada!"
