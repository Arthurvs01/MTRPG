import logging
from typing import Tuple, List
from models.player import Player
from systems.energy_system import EnergySystem
from systems.progression_system import ProgressionSystem

logger = logging.getLogger(__name__)


class TrainingSystem:
    """
    Sistema Canônico de Treinamento e Especialização de Mushoku Tensei.
    O rendimento do treino é estritamente condicionado pela Vocação/Classe do personagem:
    - Espadachim: Rendimento máximo em Artes da Lâmina e Touki. Rendimento reduzido em Magia.
    - Mago: Rendimento máximo em Controle e Poder Mágico. Rendimento reduzido em Treino de Espadas.
    - Híbrido: Rendimento equilibrado em ambas as vertentes.
    Limite: 2 treinos por dia. Concede apenas XP.
    """

    @classmethod
    def train_sword_dojo(cls, player: Player) -> Tuple[bool, str, List[str]]:
        if not player.can_train():
            return False, "🚫 Você já treinou 2 vezes hoje! Retorne amanhã.", []

        can_act, err_msg = EnergySystem.can_perform_action(player, EnergySystem.TRAINING_ENERGY_COST)
        if not can_act:
            return False, err_msg, []

        EnergySystem.consume(player, EnergySystem.TRAINING_ENERGY_COST)

        xp_logs = ProgressionSystem.add_xp(player, 65)
        player.increment_training_use()

        logs = [
            "⚔️ <b>Dojo de Espadas</b> - Você completou 1000 golpes de treino!",
            f"✨ <b>Experiência ganha:</b> +65 XP",
        ] + xp_logs

        return True, "Treino no Dojo concluído!", logs

    @classmethod
    def train_magic_tower(cls, player: Player) -> Tuple[bool, str, List[str]]:
        if not player.can_train():
            return False, "🚫 Você já treinou 2 vezes hoje! Retorne amanhã.", []

        can_act, err_msg = EnergySystem.can_perform_action(player, EnergySystem.TRAINING_ENERGY_COST)
        if not can_act:
            return False, err_msg, []

        EnergySystem.consume(player, EnergySystem.TRAINING_ENERGY_COST)

        xp_logs = ProgressionSystem.add_xp(player, 65)
        player.increment_training_use()

        logs = [
            "🔮 <b>Torre de Magia</b> - Você meditou refinando seu controle de mana!",
            f"✨ <b>Experiência ganha:</b> +65 XP",
        ] + xp_logs

        return True, "Meditação Mágica concluída!", logs

    @classmethod
    def train_touki_conditioning(cls, player: Player) -> Tuple[bool, str, List[str]]:
        if not player.can_train():
            return False, "🚫 Você já treinou 2 vezes hoje! Retorne amanhã.", []

        can_act, err_msg = EnergySystem.can_perform_action(player, EnergySystem.TRAINING_ENERGY_COST)
        if not can_act:
            return False, err_msg, []

        EnergySystem.consume(player, EnergySystem.TRAINING_ENERGY_COST)

        xp_logs = ProgressionSystem.add_xp(player, 65)
        player.increment_training_use()

        logs = [
            "🥋 <b>Condicionamento de Touki</b> - Você revestiu seu corpo com aura de batalha!",
            f"✨ <b>Experiência ganha:</b> +65 XP",
        ] + xp_logs

        return True, "Condicionamento concluído!", logs
