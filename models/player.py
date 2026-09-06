import time
from datetime import datetime
import logging
from typing import Dict, Any, List, Optional, Tuple
from models.item import Equipment

logger = logging.getLogger(__name__)


class Player:
    """
    Entidade Principal do Aventureiro no Universo de Mushoku Tensei.
    Gerencia atributos físicos, mana pool, touki, energia de ação, diamantes,
    proficiências em estilos de espada e magia, equipamentos e inventário.
    """

    def __init__(
        self,
        chat_id: int,
        character_name: str,
        race: str = "Humano",
        vocation: str = "Espadachim",
        origin_continent: str = "central",
    ):
        self.chat_id = chat_id
        self.character_name = character_name
        self.race = race  # Humano, Demônio (Migurd/Superd), Homem-Fera, Elfo, Anão
        self.vocation = vocation  # Espadachim, Mago, Híbrido
        self.origin_continent = origin_continent  # central, demon, milis, begaritt
        self.current_location = "Aldeia Buena (Fittoa)" if origin_continent == "central" else "Cidade de Rikarisu"
        self.current_region = "buena_village" if origin_continent == "central" else "rikarisu_demon_continent"

        # Progressão de Nível e Guilda
        self.level: int = 1
        self.xp: int = 0
        self.xp_next_level: int = 100
        self.status_points: int = 0
        self.adventurer_rank: str = "F"  # F, E, D, C, B, A, S
        self.guild_points: int = 0
        self.deaths: int = 0

        # Atributos Base
        self.hp: int = 120
        self.max_hp: int = 120
        self.mana: int = 50
        self.max_mana: int = 50
        self.touki: int = 0  # Revestimento de Mana (Aura de Batalha)
        self.max_touki: int = 0

        # Sistema de Energia & Vigor de Ação
        self.energy: int = 100
        self.max_energy: int = 100
        self.last_energy_regen_timestamp: float = time.time()

        # Moedas & Diamantes Nobres
        self.iron_coins: int = 100       # Moeda de Ferro (base de Asura / Moeda de Pedra)
        self.silver_coins: int = 0      # 1 Prata = 100 Ferros
        self.gold_coins: int = 0        # 1 Ouro = 100 Pratas
        self.diamonds: int = 10         # Diamantes Nobres / Moeda Premium

        # Sistema de LootBoxes & Cooldowns
        self.last_daily_lootbox_timestamp: float = 0.0
        self.hunt_lootbox_count: int = 0  # Baús arcanos dropados em caçadas

        # Atributos de Combate
        self.strength: int = 12       # Força física e dano com espada
        self.defense: int = 8         # Defesa natural
        self.speed: int = 10          # Agilidade, evasão e ordem de turno
        self.magic_power: int = 10    # Dano mágico e afinidade com elementos

        # Habilidades Especiais Canônicas
        self.has_voiceless_casting: bool = False  # Conjuração Silenciosa de Feitiços
        self.demon_eye: Optional[str] = None      # 'Premonição' (Foresight) / 'Clarividência'
        self.has_touki_awakened: bool = False     # Despertar do Touki

        # Ranks em Estilos de Espada
        self.sword_styles: Dict[str, str] = {
            "Deus da Espada": "Iniciante" if vocation == "Espadachim" else "Nenhum",
            "Deus da Água": "Nenhum",
            "Deus do Norte": "Nenhum"
        }

        # Ranks em Escolas de Magia
        self.magic_schools: Dict[str, str] = {
            "Fogo": "Iniciante" if vocation == "Mago" else "Nenhum",
            "Água": "Iniciante" if vocation == "Mago" else "Nenhum",
            "Terra": "Iniciante" if vocation == "Mago" else "Nenhum",
            "Vento": "Iniciante" if vocation == "Mago" else "Nenhum",
            "Cura": "Iniciante" if vocation == "Mago" else "Nenhum"
        }

        # Magias Conhecidas e Técnicas de Espada Aprendidas
        self.known_spells: List[str] = ["fireball_1"] if vocation == "Mago" else []
        self.known_sword_skills: List[str] = ["sword_strike_1"] if vocation == "Espadachim" else []

        # Inventário Organizado
        self.inventory: Dict[str, Any] = {
            "materials": {},    # {"treant_elder_wood": 2, "iron_ore": 3}
            "consumables": {"potion_hp_minor": 3, "potion_mana_minor": 2},
            "runes": {},        # {"rune_str_1": 1, "rune_mag_1": 1}
            "equipment": [],    # Dicionários serializados de Equipment ou IDs
            "quest_items": {}
        }

        # Equipamentos Ativos
        self.equipped: Dict[str, Optional[Dict[str, Any]]] = {
            "weapon": Equipment(
                id="iron_sword",
                name="Espada de Ferro de Asura",
                slot="weapon",
                attack_bonus=12,
                rarity="Comum",
                level=1,
                max_rune_slots=1,
            ).to_dict() if vocation == "Espadachim" else None,
            "staff": Equipment(
                id="wooden_staff",
                name="Cajado de Aprendiz de Magia",
                slot="staff",
                attack_bonus=2,
                magic_bonus=15,
                rarity="Comum",
                level=1,
                max_rune_slots=1,
            ).to_dict() if vocation == "Mago" else None,
            "armor": Equipment(
                id="leather_tunic",
                name="Túnica de Couro de Aventureiro",
                slot="armor",
                defense_bonus=8,
                speed_bonus=2,
                rarity="Comum",
                level=1,
                max_rune_slots=1,
            ).to_dict(),
            "accessory": None
        }

        # Quests em Andamento e Controle Diário
        self.active_quests: List[Dict[str, Any]] = []
        self.daily_quests_completed: int = 0
        self.last_quest_date: str = ""
        self.daily_quests_board: Dict[str, Any] = {}

        # Sistema de Viagem e Regiões
        self.unlocked_regions: List[str] = ["buena_village"]
        self.travel_cooldown: float = 0.0

        # Contadores Diários
        self.daily_inn_uses: int = 0
        self.last_inn_date: str = ""
        self.daily_training_uses: int = 0
        self.last_training_date: str = ""

        # Dungeons
        self.daily_dungeon_count: int = 0
        self.last_dungeon_date: str = ""

        # Grupo de Aventureiros (Party/Guild)
        self.party_id: Optional[str] = None
        self.party_role: str = ""  # "leader", "member"
        self.party_join_requests: List[str] = []  # IDs de convites pendentes

    def regen_energy_passively(self):
        """Regenera energia passivamente com base no tempo decorrido (+1 a cada 3 minutos)."""
        now = time.time()
        elapsed = now - self.last_energy_regen_timestamp
        regen_rate_seconds = 180  # 3 minutos por ponto de energia
        points_to_add = int(elapsed // regen_rate_seconds)

        if points_to_add > 0:
            self.energy = min(self.max_energy, self.energy + points_to_add)
            self.last_energy_regen_timestamp = now - (elapsed % regen_rate_seconds)

    def consume_energy(self, amount: int) -> bool:
        """Tenta consumir a quantidade especificada de energia."""
        self.regen_energy_passively()
        if self.energy >= amount:
            self.energy -= amount
            return True
        return False

    def get_today_str(self) -> str:
        return datetime.now().strftime("%Y-%m-%d")

    def get_daily_quests_completed(self) -> int:
        today = self.get_today_str()
        if self.last_quest_date != today:
            self.daily_quests_completed = 0
            self.last_quest_date = today
        return self.daily_quests_completed

    def can_complete_daily_quest(self) -> bool:
        return self.get_daily_quests_completed() < 2

    def increment_daily_quests_completed(self):
        self.get_daily_quests_completed()
        self.daily_quests_completed += 1

    def get_today_str(self) -> str:
        return datetime.now().strftime("%Y-%m-%d")

    def get_daily_inn_uses(self) -> int:
        today = self.get_today_str()
        if self.last_inn_date != today:
            self.daily_inn_uses = 0
            self.last_inn_date = today
        return self.daily_inn_uses

    def can_use_inn(self) -> bool:
        return self.get_daily_inn_uses() < 2

    def increment_inn_use(self):
        self.get_daily_inn_uses()
        self.daily_inn_uses += 1

    def get_daily_training_uses(self) -> int:
        today = self.get_today_str()
        if self.last_training_date != today:
            self.daily_training_uses = 0
            self.last_training_date = today
        return self.daily_training_uses

    def can_train(self) -> bool:
        return self.get_daily_training_uses() < 2

    def increment_training_use(self):
        self.get_daily_training_uses()
        self.daily_training_uses += 1

    def get_daily_dungeon_count(self) -> int:
        today = self.get_today_str()
        if self.last_dungeon_date != today:
            self.daily_dungeon_count = 0
            self.last_dungeon_date = today
        return self.daily_dungeon_count

    def can_enter_dungeon(self) -> bool:
        return self.get_daily_dungeon_count() < 3

    def increment_dungeon_count(self):
        self.get_daily_dungeon_count()
        self.daily_dungeon_count += 1

    def can_travel_to(self, region_id: str, regions_data: list) -> Tuple[bool, str]:
        """Verifica se o jogador pode viajar para uma região."""
        import time
        
        # Cooldown de viagem (30 minutos)
        if time.time() - self.travel_cooldown < 1800:
            remaining = int((1800 - (time.time() - self.travel_cooldown)) / 60)
            return False, f"Você deve aguardar {remaining} minutos antes de viajar novamente."

        # Verifica se a região existe
        region = next((r for r in regions_data if r["id"] == region_id), None)
        if not region:
            return False, "Região não encontrada."

        # Verifica se já está na região
        if self.current_region == region_id:
            return False, "Você já está nesta região."

        # Verifica nível mínimo
        if self.level < region["unlock_level"]:
            return False, f"Nível {region['unlock_level']} necessário para acessar {region['name']}."

        # Verifica pré-requisito de localização
        if region["required_location"] and region["required_location"] not in self.unlocked_regions:
            req_region = next((r for r in regions_data if r["id"] == region["required_location"]), None)
            req_name = req_region["name"] if req_region else region["required_location"]
            return False, f"Você deve desbloquear {req_name} primeiro."

        return True, "Viagem permitida."

    def travel_to(self, region_id: str, regions_data: list) -> Tuple[bool, str]:
        """Realiza a viagem para uma nova região."""
        can_travel, msg = self.can_travel_to(region_id, regions_data)
        if not can_travel:
            return False, msg

        region = next((r for r in regions_data if r["id"] == region_id), None)
        if not region:
            return False, "Região não encontrada."

        import time
        self.travel_cooldown = time.time()
        self.current_region = region_id
        self.current_location = region["name"]

        # Desbloqueia a região se não estiver desbloqueada
        if region_id not in self.unlocked_regions:
            self.unlocked_regions.append(region_id)

        return True, f"Você viajou para {region['name']}!"

    def get_total_attack(self) -> int:
        base = self.strength
        if self.has_touki_awakened:
            base += int(self.touki * 0.5)
        for slot in ["weapon", "staff", "armor", "accessory"]:
            eq_data = self.equipped.get(slot)
            if eq_data:
                eq = Equipment.from_dict(eq_data)
                eff = eq.get_effective_stats()
                base += eff["attack"]
        return base

    def get_total_magic_power(self) -> int:
        base = self.magic_power
        for slot in ["weapon", "staff", "armor", "accessory"]:
            eq_data = self.equipped.get(slot)
            if eq_data:
                eq = Equipment.from_dict(eq_data)
                eff = eq.get_effective_stats()
                base += eff["magic"]
        return base

    def get_total_defense(self) -> int:
        base = self.defense
        if self.has_touki_awakened:
            base += int(self.touki * 0.4)
        for slot in ["weapon", "staff", "armor", "accessory"]:
            eq_data = self.equipped.get(slot)
            if eq_data:
                eq = Equipment.from_dict(eq_data)
                eff = eq.get_effective_stats()
                base += eff["defense"]
        return base

    def get_total_speed(self) -> int:
        base = self.speed
        if self.has_touki_awakened:
            base += int(self.touki * 0.3)
        for slot in ["weapon", "staff", "armor", "accessory"]:
            eq_data = self.equipped.get(slot)
            if eq_data:
                eq = Equipment.from_dict(eq_data)
                eff = eq.get_effective_stats()
                base += eff["speed"]
        return base

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chat_id": self.chat_id,
            "character_name": self.character_name,
            "race": self.race,
            "vocation": self.vocation,
            "origin_continent": self.origin_continent,
            "current_location": self.current_location,
            "current_region": self.current_region,
            "level": self.level,
            "xp": self.xp,
            "xp_next_level": self.xp_next_level,
            "status_points": self.status_points,
            "adventurer_rank": self.adventurer_rank,
            "guild_points": self.guild_points,
            "deaths": self.deaths,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "mana": self.mana,
            "max_mana": self.max_mana,
            "touki": self.touki,
            "max_touki": self.max_touki,
            "energy": self.energy,
            "max_energy": self.max_energy,
            "last_energy_regen_timestamp": self.last_energy_regen_timestamp,
            "iron_coins": self.iron_coins,
            "silver_coins": self.silver_coins,
            "gold_coins": self.gold_coins,
            "diamonds": self.diamonds,
            "last_daily_lootbox_timestamp": self.last_daily_lootbox_timestamp,
            "hunt_lootbox_count": self.hunt_lootbox_count,
            "strength": self.strength,
            "defense": self.defense,
            "speed": self.speed,
            "magic_power": self.magic_power,
            "has_voiceless_casting": self.has_voiceless_casting,
            "demon_eye": self.demon_eye,
            "has_touki_awakened": self.has_touki_awakened,
            "sword_styles": self.sword_styles,
            "magic_schools": self.magic_schools,
            "known_spells": self.known_spells,
            "known_sword_skills": self.known_sword_skills,
            "inventory": self.inventory,
            "equipped": self.equipped,
            "active_quests": self.active_quests,
            "daily_quests_completed": self.daily_quests_completed,
            "last_quest_date": self.last_quest_date,
            "daily_quests_board": self.daily_quests_board,
            "unlocked_regions": self.unlocked_regions,
            "travel_cooldown": self.travel_cooldown,
            "daily_inn_uses": self.daily_inn_uses,
            "last_inn_date": self.last_inn_date,
            "daily_training_uses": self.daily_training_uses,
            "last_training_date": self.last_training_date,
            "daily_dungeon_count": self.daily_dungeon_count,
            "last_dungeon_date": self.last_dungeon_date,
            "party_id": self.party_id,
            "party_role": self.party_role,
            "party_join_requests": self.party_join_requests,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Player":
        player = cls(
            chat_id=data.get("chat_id", 0),
            character_name=data.get("character_name", "Aventureiro"),
            race=data.get("race", "Humano"),
            vocation=data.get("vocation", "Espadachim"),
            origin_continent=data.get("origin_continent", "central"),
        )
        player.current_location = data.get("current_location", player.current_location)
        player.current_region = data.get("current_region", player.current_region)
        player.level = data.get("level", 1)
        player.xp = data.get("xp", 0)
        player.xp_next_level = data.get("xp_next_level", 100)
        player.status_points = data.get("status_points", 0)
        player.adventurer_rank = data.get("adventurer_rank", "F")
        player.guild_points = data.get("guild_points", 0)
        player.deaths = data.get("deaths", 0)

        player.hp = data.get("hp", 120)
        player.max_hp = data.get("max_hp", 120)
        player.mana = data.get("mana", 50)
        player.max_mana = data.get("max_mana", 50)
        player.touki = data.get("touki", 0)
        player.max_touki = data.get("max_touki", 0)

        player.energy = data.get("energy", 100)
        player.max_energy = data.get("max_energy", 100)
        player.last_energy_regen_timestamp = data.get("last_energy_regen_timestamp", time.time())

        player.iron_coins = data.get("iron_coins", 100)
        player.silver_coins = data.get("silver_coins", 0)
        player.gold_coins = data.get("gold_coins", 0)
        player.diamonds = data.get("diamonds", 10)

        player.last_daily_lootbox_timestamp = data.get("last_daily_lootbox_timestamp", 0.0)
        player.hunt_lootbox_count = data.get("hunt_lootbox_count", 0)

        player.strength = data.get("strength", 12)
        player.defense = data.get("defense", 8)
        player.speed = data.get("speed", 10)
        player.magic_power = data.get("magic_power", 10)

        player.has_voiceless_casting = data.get("has_voiceless_casting", False)
        player.demon_eye = data.get("demon_eye", None)
        player.has_touki_awakened = data.get("has_touki_awakened", False)

        if "sword_styles" in data:
            player.sword_styles.update(data["sword_styles"])
        if "magic_schools" in data:
            player.magic_schools.update(data["magic_schools"])

        player.known_spells = data.get("known_spells", player.known_spells)
        player.known_sword_skills = data.get("known_sword_skills", player.known_sword_skills)

        if "inventory" in data:
            for k, v in data["inventory"].items():
                player.inventory[k] = v

        if "equipped" in data:
            player.equipped.update(data["equipped"])

        player.active_quests = data.get("active_quests", [])
        player.daily_quests_completed = data.get("daily_quests_completed", 0)
        player.last_quest_date = data.get("last_quest_date", "")
        player.daily_quests_board = data.get("daily_quests_board", {})

        player.unlocked_regions = data.get("unlocked_regions", ["buena_village"])
        player.travel_cooldown = data.get("travel_cooldown", 0.0)
        player.daily_inn_uses = data.get("daily_inn_uses", 0)
        player.last_inn_date = data.get("last_inn_date", "")
        player.daily_training_uses = data.get("daily_training_uses", 0)
        player.last_training_date = data.get("last_training_date", "")
        player.daily_dungeon_count = data.get("daily_dungeon_count", 0)
        player.last_dungeon_date = data.get("last_dungeon_date", "")
        player.party_id = data.get("party_id", None)
        player.party_role = data.get("party_role", "")
        player.party_join_requests = data.get("party_join_requests", [])
        return player
