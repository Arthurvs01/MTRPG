import random
import logging
from typing import Dict, Any, List, Tuple
from models.player import Player
from models.combatant import Combatant
from core.json_loader import JsonLoader

logger = logging.getLogger(__name__)


class CombatSystem:
    """
    Sistema Central de Combate com Fidelidade ao Universo de Mushoku Tensei.
    Processa confrontos em turnos integrando:
    - Os 3 Grandes Estilos de Espada (Deus da Espada, Deus da Água, Deus do Norte)
    - Magias elementais e de cura por Ranks
    - Conjuração Silenciosa (Voiceless Incantation)
    - Manto de Mana (Touki) e Olhos Demoníacos (Premonição)
    """

    @classmethod
    def get_monster(cls, monster_id: str) -> Combatant:
        """Instancia um monstro a partir dos dados do bestiário."""
        data = JsonLoader.load("monsters.json")
        monsters = data.get("monsters", {})
        if monster_id in monsters:
            m_data = dict(monsters[monster_id])
            m_data["id"] = monster_id
            return Combatant.from_dict(m_data)
        # Fallback de monstro genérico
        return Combatant(
            id="wild_beast",
            name="Fera Selvagem Desconhecida",
            level=1,
            hp=80,
            max_hp=80,
            attack=10,
            defense=5,
            speed=8,
            xp_reward=20,
            coins_reward=10
        )

    @classmethod
    async def get_monster_async(cls, monster_id: str) -> Combatant:
        """Versão assíncrona para não bloquear o event loop."""
        data = await JsonLoader.load_async("monsters.json")
        monsters = data.get("monsters", {})
        if monster_id in monsters:
            m_data = dict(monsters[monster_id])
            m_data["id"] = monster_id
            return Combatant.from_dict(m_data)
        # Fallback de monstro genérico
        return Combatant(
            id="wild_beast",
            name="Fera Selvagem Desconhecida",
            level=1,
            hp=80,
            max_hp=80,
            attack=10,
            defense=5,
            speed=8,
            xp_reward=20,
            coins_reward=10
        )

    @classmethod
    def execute_player_turn(
        cls,
        player: Player,
        enemy: Combatant,
        action_type: str = "auto"
    ) -> List[str]:
        """
        Processa o ataque do Jogador contra o Inimigo.
        Retorna logs narrativos da rodada.
        """
        logs = []
        player_atk = player.get_total_attack()
        player_mag = player.get_total_magic_power()
        player_spd = player.get_total_speed()

        # Determina o estilo principal
        sword_styles = player.sword_styles
        primary_style = "Deus da Espada"
        for style, rank in sword_styles.items():
            if rank != "Nenhum":
                primary_style = style
                break

        # Ação Mágica ou Espada
        if player.vocation == "Mago" and player.mana >= 8:
            # Magia Elemental
            mana_cost = 6 if player.has_voiceless_casting else 8
            player.mana = max(0, player.mana - mana_cost)
            
            magic_multiplier = 1.6
            raw_dmg = int((player_mag * magic_multiplier) - (enemy.defense * 0.4))
            damage = max(5, raw_dmg)

            if player.has_voiceless_casting:
                logs.append(f"⚡ <b>[Conjuração Silenciosa]</b> Você dispara um projétil comprimido instantâneo!")
            else:
                logs.append(f"✨ <i>'Ó chamas ardentes da purificação...'</i> Você conjura [Fireball]!")

            enemy.hp = max(0, enemy.hp - damage)
            logs.append(f"💥 <b>Dano Mágico:</b> Inimigo sofreu <b>{damage}</b> de dano elemental!")

        else:
            # Combate com Espada / Físico
            crit_chance = 15
            if primary_style == "Deus da Espada":
                crit_chance = 35  # Especialistas em finalização rápida
                logs.append(f"🗡️ <b>[Estilo Deus da Espada]</b> Você avança em alta velocidade com lâmina em riste!")
            elif primary_style == "Deus do Norte":
                logs.append(f"🪓 <b>[Estilo Deus do Norte]</b> Você utiliza o terreno e desfere um golpe imprevisível!")
            elif primary_style == "Deus da Água":
                logs.append(f"🌊 <b>[Estilo Deus da Água]</b> Você mantém a postura fluida da água serena!")

            # Cálculo de Dano Físico
            divisor = enemy.defense + 10
            reduction = min(0.7, enemy.defense / divisor)
            raw_dmg = int(player_atk * (1.0 - reduction))
            damage = max(4, raw_dmg)

            is_crit = random.randint(1, 100) <= crit_chance
            if is_crit:
                damage = int(damage * 1.6)
                logs.append(f"🔥 <b>GOLPE CRÍTICO!</b> A lâmina atingiu um ponto vital!")

            enemy.hp = max(0, enemy.hp - damage)
            logs.append(f"⚔️ Você causou <b>{damage}</b> de dano físico a <b>{enemy.name}</b>.")

        return logs

    @classmethod
    def execute_enemy_turn(
        cls,
        player: Player,
        enemy: Combatant
    ) -> List[str]:
        """
        Processa o ataque do Inimigo contra o Jogador.
        Leva em conta Touki, Postura Deus da Água (Parry) e Olho da Premonição.
        """
        logs = []
        player_def = player.get_total_defense()
        player_spd = player.get_total_speed()

        # 1. Verificação de Olho Demoníaco (Premonição)
        if player.demon_eye == "Premonição" and random.randint(1, 100) <= 40:
            logs.append("👁️ <b>[Olho da Premonição]</b> Você enxergou o golpe no futuro e esquivou perfeitamente!")
            return logs

        # 2. Verificação do Estilo Deus da Água (Parry / Contra-ataque)
        if player.sword_styles.get("Deus da Água") not in ["Nenhum", None]:
            if random.randint(1, 100) <= 35:
                counter_dmg = int(enemy.attack * 0.8)
                enemy.hp = max(0, enemy.hp - counter_dmg)
                logs.append(f"🌊 <b>[Deus da Água - Fluxo]</b> Você aparou o ataque e contra-atacou causando <b>{counter_dmg}</b> de dano!")
                return logs

        # 3. Esquiva por Velocidade
        speed_diff = max(0, player_spd - enemy.speed)
        dodge_chance = min(30, speed_diff * 3)
        if random.randint(1, 100) <= dodge_chance:
            logs.append(f"💨 Você foi mais veloz e esquivou do ataque de <b>{enemy.name}</b>!")
            return logs

        # 4. Cálculo de dano recebido mitigado por Defesa e Touki
        raw_dmg = enemy.attack - int(player_def * 0.6)
        damage = max(3, raw_dmg)

        # Touki absorve dano diretamente
        if player.has_touki_awakened and player.touki > 0:
            absorbed = min(player.touki, int(damage * 0.4))
            damage -= absorbed
            logs.append(f"🛡️ <b>[Touki Ativo]</b> O manto de mana amorteceu {absorbed} de dano!")

        player.hp = max(0, player.hp - damage)
        logs.append(f"🩸 <b>{enemy.name}</b> atacou você causando <b>{damage}</b> de dano!")

        return logs

    @classmethod
    def simulate_battle(
        cls,
        player: Player,
        enemy: Combatant,
        max_turns: int = 15
    ) -> Dict[str, Any]:
        """
        Simula a batalha completa em turnos e gera o relatório com histórico detalhado.
        """
        battle_logs: List[str] = []
        battle_logs.append(f"⚔️ <b>Confronto Iniciado!</b> Você encontrou <b>{enemy.name}</b> (Rank {enemy.danger_rank})!")

        # Ordem de iniciativa baseada em Velocidade
        player_first = player.get_total_speed() >= enemy.speed

        current_turn = 1
        winner = None

        while current_turn <= max_turns and player.hp > 0 and enemy.hp > 0:
            battle_logs.append(f"\n<b>[Turno {current_turn}]</b>")

            if player_first:
                p_logs = cls.execute_player_turn(player, enemy)
                battle_logs.extend(p_logs)

                if enemy.hp <= 0:
                    winner = "player"
                    break

                e_logs = cls.execute_enemy_turn(player, enemy)
                battle_logs.extend(e_logs)

                if player.hp <= 0:
                    winner = "enemy"
                    break
            else:
                e_logs = cls.execute_enemy_turn(player, enemy)
                battle_logs.extend(e_logs)

                if player.hp <= 0:
                    winner = "enemy"
                    break

                p_logs = cls.execute_player_turn(player, enemy)
                battle_logs.extend(p_logs)

                if enemy.hp <= 0:
                    winner = "player"
                    break

            current_turn += 1

        if not winner:
            if player.hp > 0 and enemy.hp <= 0:
                winner = "player"
            elif player.hp <= 0 and enemy.hp > 0:
                winner = "enemy"
            else:
                winner = "draw"

        # Coleta de drops e recompensas em caso de vitória
        drops_obtained = []
        if winner == "player":
            for drop in enemy.drops:
                chance = drop.get("chance", 0.5)
                if random.random() <= chance:
                    item_id = drop.get("item_id")
                    item_name = drop.get("name", item_id)
                    drops_obtained.append({"id": item_id, "name": item_name})
                    # Adiciona ao inventário do jogador
                    materials = player.inventory.setdefault("materials", {})
                    materials[item_id] = materials.get(item_id, 0) + 1

        return {
            "winner": winner,
            "turns_taken": current_turn,
            "player_remaining_hp": player.hp,
            "enemy_remaining_hp": enemy.hp,
            "xp_reward": enemy.xp_reward if winner == "player" else 0,
            "coins_reward": enemy.coins_reward if winner == "player" else 0,
            "drops": drops_obtained,
            "logs": battle_logs
        }
