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
    """

    @classmethod
    def train_sword_dojo(cls, player: Player) -> Tuple[bool, str, List[str]]:
        can_act, err_msg = EnergySystem.can_perform_action(player, EnergySystem.TRAINING_ENERGY_COST)
        if not can_act:
            return False, err_msg, []

        EnergySystem.consume(player, EnergySystem.TRAINING_ENERGY_COST)

        logs = []
        if player.vocation == "Espadachim":
            player.strength += 1
            player.speed += 1
            xp_logs = ProgressionSystem.add_xp(player, 65)
            logs = [
                "⚔️ <b>[Foco de Espadachim]</b> Você completou 1000 golpes precisos no boneco de treino!",
                "💪 <b>Força +1</b> | 💨 <b>Agilidade +1</b> (Rendimento: 100%)",
            ] + xp_logs

        elif player.vocation == "Híbrido":
            player.strength += 1
            xp_logs = ProgressionSystem.add_xp(player, 50)
            logs = [
                "⚔️ <b>[Guerreiro Mágico]</b> Você treinou combinações de lâmina fluida!",
                "💪 <b>Força +1</b> (Rendimento Balanceado: 80%)",
            ] + xp_logs

        else:  # Mago
            xp_logs = ProgressionSystem.add_xp(player, 25)
            logs = [
                "⚠️ <b>[Treino Fora de Classe]</b> Seus braços de estudioso desacostumados à espada pesam rapidamente!",
                "💨 <i>Você adquiriu resistência leve, mas o rendimento de força foi mínimo.</i> (Rendimento: 40%)",
            ] + xp_logs

        return True, "Treino no Dojo concluído!", logs

    @classmethod
    def train_magic_tower(cls, player: Player) -> Tuple[bool, str, List[str]]:
        can_act, err_msg = EnergySystem.can_perform_action(player, EnergySystem.TRAINING_ENERGY_COST)
        if not can_act:
            return False, err_msg, []

        EnergySystem.consume(player, EnergySystem.TRAINING_ENERGY_COST)

        logs = []
        if player.vocation == "Mago":
            player.magic_power += 1
            player.max_mana += 6
            player.mana = min(player.max_mana, player.mana + 6)
            xp_logs = ProgressionSystem.add_xp(player, 65)
            logs = [
                "🔮 <b>[Foco de Mago]</b> Você meditou profundamente refinando seu canal e controle de partículas de mana!",
                "✨ <b>Poder Mágico +1</b> | 💧 <b>Mana Máxima +6</b> (Rendimento: 100%)",
            ] + xp_logs

        elif player.vocation == "Híbrido":
            player.magic_power += 1
            player.max_mana += 3
            player.mana = min(player.max_mana, player.mana + 3)
            xp_logs = ProgressionSystem.add_xp(player, 50)
            logs = [
                "🔮 <b>[Guerreiro Mágico]</b> Você praticou a canalização rápida de feitiços de apoio!",
                "✨ <b>Poder Mágico +1</b> | 💧 <b>Mana Máxima +3</b> (Rendimento Balanceado: 80%)",
            ] + xp_logs

        else:  # Espadachim
            player.max_mana += 2
            player.mana = min(player.max_mana, player.mana + 2)
            xp_logs = ProgressionSystem.add_xp(player, 25)
            logs = [
                "⚠️ <b>[Treino Fora de Classe]</b> Como guerreiro de lâminas, você tem grande dificuldade em sentir o fluxo sutil de mana!",
                "💧 <i>Você expandiu levemente sua reserva (+2 Mana), mas o ganho mágico foi limitado.</i> (Rendimento: 40%)",
            ] + xp_logs

        return True, "Meditação Mágica concluída!", logs

    @classmethod
    def train_touki_conditioning(cls, player: Player) -> Tuple[bool, str, List[str]]:
        can_act, err_msg = EnergySystem.can_perform_action(player, EnergySystem.TRAINING_ENERGY_COST)
        if not can_act:
            return False, err_msg, []

        EnergySystem.consume(player, EnergySystem.TRAINING_ENERGY_COST)

        logs = []
        if player.vocation in ["Espadachim", "Híbrido"]:
            player.defense += 1
            player.max_hp += 12
            player.hp = min(player.max_hp, player.hp + 12)
            if player.has_touki_awakened:
                player.max_touki += 5
                player.touki = min(player.max_touki, player.touki + 5)
            xp_logs = ProgressionSystem.add_xp(player, 65)
            logs = [
                "🥋 <b>[Condicionamento Físico de Touki]</b> Você revestiu seu corpo suportando impactos severos de rocha!",
                "🛡️ <b>Defesa +1</b> | ❤️ <b>Vida Máxima +12</b> | 🥋 <b>Touki +5</b> (Rendimento: 100%)",
            ] + xp_logs

        else:  # Mago
            player.max_hp += 5
            player.hp = min(player.max_hp, player.hp + 5)
            xp_logs = ProgressionSystem.add_xp(player, 25)
            logs = [
                "⚠️ <b>[Treino Fora de Classe]</b> Seu corpo sofre para absorver os impactos físicos rígidos!",
                "❤️ <i>Você ganhou um pouco de vigor (+5 HP), mas Magos se desenvolvem melhor com Barreiras Mágicas.</i> (Rendimento: 40%)",
            ] + xp_logs

        return True, "Condicionamento concluído!", logs
