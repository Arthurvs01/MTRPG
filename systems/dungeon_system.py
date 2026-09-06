import random
import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from models.player import Player
from database.player_repo import PlayerRepository
from systems.combat_system import CombatSystem
from systems.progression_system import ProgressionSystem
from core.json_loader import JsonLoader

logger = logging.getLogger(__name__)


class DungeonInstance:
    """Representa uma instância ativa de dungeon."""

    def __init__(self, dungeon_id: str, leader: Player, password: str):
        self.dungeon_id = dungeon_id
        self.leader_id = leader.chat_id
        self.password = password
        self.members: List[Player] = [leader]
        self.member_damage: Dict[int, int] = {leader.chat_id: 0}
        self.current_wave = 0
        self.max_waves = 5  # 4 mobs + 1 boss
        self.is_active = False
        self.is_completed = False
        self.created_at = time.time()
        self.monsters_defeated: List[str] = []
        self.total_damage = 0

    def add_member(self, player: Player) -> bool:
        if len(self.members) >= 4:
            return False
        if any(m.chat_id == player.chat_id for m in self.members):
            return False
        self.members.append(player)
        self.member_damage[player.chat_id] = 0
        return True

    def remove_member(self, player: Player) -> bool:
        if player.chat_id == self.leader_id:
            return False
        self.members = [m for m in self.members if m.chat_id != player.chat_id]
        if player.chat_id in self.member_damage:
            del self.member_damage[player.chat_id]
        return True

    def get_member(self, chat_id: int) -> Optional[Player]:
        for m in self.members:
            if m.chat_id == chat_id:
                return m
        return None

    def add_damage(self, chat_id: int, damage: int):
        if chat_id in self.member_damage:
            self.member_damage[chat_id] += damage
        self.total_damage += damage

    def get_survivors(self) -> List[Player]:
        return [m for m in self.members if m.hp > 0]

    def get_dead_players(self) -> List[Player]:
        return [m for m in self.members if m.hp <= 0]


class DungeonSystem:
    """Sistema de Gerenciamento de Dungeons em Grupo."""

    _active_dungeons: Dict[str, DungeonInstance] = {}

    @classmethod
    def get_dungeon_data(cls, region_id: str) -> Optional[Dict[str, Any]]:
        regions_data = JsonLoader.load("regions.json")
        regions = regions_data.get("regions", [])
        region = next((r for r in regions if r["id"] == region_id), None)
        if region and "dungeon" in region:
            return region["dungeon"]
        return None

    @classmethod
    def get_dungeon_monsters(cls, dungeon_id: str, wave: int) -> List[str]:
        """Retorna os monstros para uma wave específica da dungeon."""
        dungeon_monsters = {
            "dungeon_buena_cave": {
                1: ["cave_bat", "cave_bat", "giant_rat"],
                2: ["cave_spider", "cave_spider", "rock_golem"],
                3: ["undead_miner", "undead_miner", "cave_troll"],
                4: ["crystal_basilisk", "crystal_basilisk"],
                5: ["ancient_treant"],
            },
            "dungeon_roitree_sewers": {
                1: ["sewer_rat", "sewer_rat", "slime"],
                2: ["giant_cockroach", "giant_cockroach", "sewer_snake"],
                3: ["mutated_turtle", "mutated_turtle", "toxic_sludge"],
                4: ["sewer_crocodile", "sewer_crocodile"],
                5: ["sewer_king_rat"],
            },
            "dungeon_ruins_ranoa": {
                1: ["mana_construct", "mana_construct", "arcane_sludge"],
                2: ["spell_thief", "spell_thief", "grimoire_mimic"],
                3: ["corrupted_apprentice", "corrupted_apprentice", "arcane_guardian"],
                4: ["archmage_shade_minion", "archmage_shade_minion"],
                5: ["archmage_shade"],
            },
            "dungeon_milis_catacombs": {
                1: ["scripture_wraith", "scripture_wraith", "holy_knight_fallen"],
                2: ["angel_statue_animated", "angel_statue_animated", "inquisitor_shade"],
                3: ["divine_golem", "divine_golem", "saint_shade"],
                4: ["high_inquisitor_guard", "high_inquisitor_guard"],
                5: ["high_inquisitor_undead"],
            },
            "dungeon_world_tree": {
                1: ["elven_guardian", "elven_guardian", "spirit_beast"],
                2: ["ancient_dryad", "ancient_dryad", "world_tree_root"],
                3: ["elder_elf_archer", "elder_elf_archer", "corrupted_spirit"],
                4: ["world_tree_avatar_minion", "world_tree_avatar_minion"],
                5: ["world_tree_avatar"],
            },
            "dungeon_labyrinth_begaritt": {
                1: ["sand_drake", "sand_drake", "mirage_beast"],
                2: ["ancient_scarab", "ancient_scarab", "phoenix_chick"],
                3: ["labyrinth_guardian", "labyrinth_guardian", "sand_worm_titan"],
                4: ["labyrinth_master_minion", "labyrinth_master_minion"],
                5: ["labyrinth_master"],
            },
            "dungeon_demon_king_castle": {
                1: ["demon_coyote_rikarisu", "demon_coyote_rikarisu", "kougumo_spider"],
                2: ["sand_worm_demon", "sand_worm_demon", "demon_vulture_roc"],
                3: ["stone_shell_tortoise", "stone_shell_tortoise", "two_headed_wyvern"],
                4: ["demon_general", "demon_general"],
                5: ["demon_king_avatar"],
            },
            "dungeon_sunken_city": {
                1: ["ghost_ship_crew", "ghost_ship_crew", "kraken_tentacle"],
                2: ["sea_serpent", "sea_serpent", "abyssal_leviathan"],
                3: ["storm_elemental", "storm_elemental", "drowned_king"],
                4: ["leviathan_lord_minion", "leviathan_lord_minion"],
                5: ["leviathan_lord"],
            },
        }
        return dungeon_monsters.get(dungeon_id, {}).get(wave, ["cave_bat"])

    @classmethod
    def create_dungeon(cls, leader: Player, region_id: str, password: str) -> Tuple[bool, str, Optional[DungeonInstance]]:
        """Cria uma nova instância de dungeon."""
        if not leader.can_enter_dungeon():
            return False, "🚫 Você já fez 3 dungeons hoje! Retorne amanhã.", None

        dungeon_data = cls.get_dungeon_data(region_id)
        if not dungeon_data:
            return False, "Esta região não possui dungeon.", None

        if leader.level < dungeon_data["min_level"]:
            return False, f"Nível {dungeon_data['min_level']} necessário para esta dungeon.", None

        if len(password) != 4 or not password.isdigit():
            return False, "A senha deve ter exatamente 4 dígitos numéricos.", None

        dungeon_id = f"{region_id}_{leader.chat_id}_{int(time.time())}"
        instance = DungeonInstance(dungeon_id, leader, password)
        cls._active_dungeons[dungeon_id] = instance

        leader.increment_dungeon_count()
        return True, f"Dungeon '{dungeon_data['name']}' criada! Senha: {password}. Aguardando 3 jogadores...", instance

    @classmethod
    def join_dungeon(cls, player: Player, dungeon_id: str, password: str) -> Tuple[bool, str]:
        """Junta-se a uma dungeon existente."""
        if not player.can_enter_dungeon():
            return False, "🚫 Você já fez 3 dungeons hoje! Retorne amanhã."

        instance = cls._active_dungeons.get(dungeon_id)
        if not instance:
            return False, "Dungeon não encontrada ou já finalizada."

        if instance.is_active:
            return False, "Esta dungeon já começou."

        if instance.password != password:
            return False, "Senha incorreta."

        if instance.get_member(player.chat_id):
            return False, "Você já está neste grupo."

        if len(instance.members) >= 4:
            return False, "Grupo cheio (máximo 4 jogadores)."

        instance.add_member(player)
        player.increment_dungeon_count()
        return True, f"Você entrou na dungeon! Jogadores: {len(instance.members)}/4"

    @classmethod
    def leave_dungeon(cls, player: Player, dungeon_id: str) -> Tuple[bool, str]:
        """Sai de uma dungeon."""
        instance = cls._active_dungeons.get(dungeon_id)
        if not instance:
            return False, "Dungeon não encontrada."

        if player.chat_id == instance.leader_id:
            return False, "O líder não pode sair. Use 'Cancelar Dungeon'."

        instance.remove_member(player)
        return True, "Você saiu da dungeon."

    @classmethod
    def start_dungeon(cls, leader: Player, dungeon_id: str) -> Tuple[bool, str]:
        """Inicia a dungeon (apenas líder)."""
        instance = cls._active_dungeons.get(dungeon_id)
        if not instance:
            return False, "Dungeon não encontrada."

        if leader.chat_id != instance.leader_id:
            return False, "Apenas o líder pode iniciar."

        if len(instance.members) < 2:
            return False, "Mínimo 2 jogadores para iniciar."

        instance.is_active = True
        instance.current_wave = 1
        return True, "Dungeon iniciada! Primeira onda de monstros aparecendo..."

    @classmethod
    def process_dungeon_battle(cls, instance: DungeonInstance, player: Player, monster_id: str) -> Dict[str, Any]:
        """Processa uma batalha na dungeon."""
        enemy = CombatSystem.get_monster(monster_id)
        result = CombatSystem.simulate_battle(player, enemy)

        if result["winner"] == "player":
            damage_dealt = enemy.max_hp  # Dano total causado
            instance.add_damage(player.chat_id, damage_dealt)
            instance.monsters_defeated.append(monster_id)
        elif result["winner"] == "enemy":
            player.deaths += 1
            player.hp = int(player.max_hp * 0.5)

        return result

    @classmethod
    def next_wave(cls, instance: DungeonInstance) -> Tuple[bool, str, List[str]]:
        """Avança para a próxima onda."""
        if instance.current_wave >= instance.max_waves:
            return cls.complete_dungeon(instance)

        instance.current_wave += 1
        monsters = cls.get_dungeon_monsters(instance.dungeon_id, instance.current_wave)

        if instance.current_wave == instance.max_waves:
            wave_type = "👑 <b>BOSS FINAL</b>"
        else:
            wave_type = f"🌊 <b>Onda {instance.current_wave}</b>"

        return True, f"{wave_type} iniciada! Monstros: {', '.join(monsters)}", monsters

    @classmethod
    def complete_dungeon(cls, instance: DungeonInstance) -> Tuple[bool, str, List[str]]:
        """Finaliza a dungeon e distribui recompensas."""
        instance.is_completed = True
        instance.is_active = False

        survivors = instance.get_survivors()
        dead_players = instance.get_dead_players()

        if not survivors:
            return False, "Todos os membros morreram! Dungeon falhada.", []

        dungeon_data = cls.get_dungeon_data(instance.dungeon_id.split("_")[0] + "_" + instance.dungeon_id.split("_")[1])
        base_rewards = {
            "iron_coins": 5000,
            "xp": 5000,
            "items": ["dungeon_key_fragment", "rare_material"],
        }

        if dungeon_data:
            min_level = dungeon_data.get("min_level", 1)
            base_rewards["iron_coins"] = min_level * 100
            base_rewards["xp"] = min_level * 100

        # Calcula distribuição proporcional ao dano
        total_damage = sum(instance.member_damage.values())
        rewards_log = []

        for player in survivors:
            player_damage = instance.member_damage.get(player.chat_id, 0)
            if total_damage > 0:
                share = player_damage / total_damage
            else:
                share = 1.0 / len(survivors)

            coins = int(base_rewards["iron_coins"] * share)
            xp = int(base_rewards["xp"] * share)

            player.iron_coins += coins
            xp_logs = ProgressionSystem.add_xp(player, xp)

            rewards_log.append(
                f"👤 {player.character_name}: {coins} Ferros, {xp} XP ({int(share*100)}% do dano)"
            )

        # Redistribui recompensas dos mortos
        if dead_players:
            dead_share_coins = sum(int(base_rewards["iron_coins"] * (instance.member_damage.get(p.chat_id, 0) / max(total_damage, 1))) for p in dead_players)
            dead_share_xp = sum(int(base_rewards["xp"] * (instance.member_damage.get(p.chat_id, 0) / max(total_damage, 1))) for p in dead_players)

            if survivors:
                per_survivor_coins = dead_share_coins // len(survivors)
                per_survivor_xp = dead_share_xp // len(survivors)

                for player in survivors:
                    player.iron_coins += per_survivor_coins
                    ProgressionSystem.add_xp(player, per_survivor_xp)
                    rewards_log.append(f"  ↳ +{per_survivor_coins} Ferros, +{per_survivor_xp} XP (parte dos caídos)")

        # Salva todos os jogadores
        for player in instance.members:
            PlayerRepository.save_player_sync(player)

        del cls._active_dungeons[instance.dungeon_id]

        return True, "Dungeon completada! Recompensas distribuídas.", rewards_log

    @classmethod
    def cancel_dungeon(cls, leader: Player, dungeon_id: str) -> Tuple[bool, str]:
        """Cancela a dungeon (apenas líder)."""
        instance = cls._active_dungeons.get(dungeon_id)
        if not instance:
            return False, "Dungeon não encontrada."

        if leader.chat_id != instance.leader_id:
            return False, "Apenas o líder pode cancelar."

        del cls._active_dungeons[dungeon_id]
        return True, "Dungeon cancelada."

    @classmethod
    def get_dungeon_info(cls, dungeon_id: str) -> Optional[Dict[str, Any]]:
        """Retorna informações da dungeon para exibição."""
        instance = cls._active_dungeons.get(dungeon_id)
        if not instance:
            return None

        return {
            "dungeon_id": instance.dungeon_id,
            "leader": instance.get_member(instance.leader_id).character_name if instance.get_member(instance.leader_id) else "Desconhecido",
            "members": [{"name": m.character_name, "hp": m.hp, "max_hp": m.max_hp, "damage": instance.member_damage.get(m.chat_id, 0)} for m in instance.members],
            "current_wave": instance.current_wave,
            "max_waves": instance.max_waves,
            "is_active": instance.is_active,
            "password": instance.password,
        }