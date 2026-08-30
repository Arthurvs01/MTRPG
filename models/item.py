import uuid
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from core.json_loader import JsonLoader


@dataclass
class Item:
    """Representa um item comum, consumível, material de monstro ou runa."""
    id: str
    name: str
    description: str
    item_type: str  # 'consumable', 'material', 'rune', 'special'
    value_in_iron_coins: int = 10
    rune_type: Optional[str] = None  # 'attack', 'magic', 'defense', 'speed'
    rune_value: int = 0
    effects: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "item_type": self.item_type,
            "value_in_iron_coins": self.value_in_iron_coins,
            "rune_type": self.rune_type,
            "rune_value": self.rune_value,
            "effects": self.effects,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Item":
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            item_type=data.get("item_type", "material"),
            value_in_iron_coins=data.get("value_in_iron_coins", 10),
            rune_type=data.get("rune_type"),
            rune_value=data.get("rune_value", 0),
            effects=data.get("effects", {}),
        )


@dataclass
class Equipment:
    """
    Representa uma instância de equipamento única com Raridade, Nível de Upgrade (+1 a +10)
    e Slots para Engaste de Runas Mágicas.
    """
    id: str
    name: str
    slot: str  # 'weapon', 'staff', 'armor', 'accessory'
    instance_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    description: str = ""
    attack_bonus: int = 0
    magic_bonus: int = 0
    defense_bonus: int = 0
    speed_bonus: int = 0
    value_in_iron_coins: int = 50
    rarity: str = "Comum"  # Comum (1 slot), Raro (2 slots), Santo (3 slots), Imperial (4 slots), Divino (5 slots)
    level: int = 1         # Nível de upgrade (1 a 10)
    max_rune_slots: int = 1
    socketed_runes: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.instance_id:
            self.instance_id = str(uuid.uuid4())[:8]
        if self.max_rune_slots <= 1:
            rarity_slots = {
                "Comum": 1,
                "Raro": 2,
                "Santo": 3,
                "Imperial": 4,
                "Divino": 5
            }
            self.max_rune_slots = rarity_slots.get(self.rarity, 1)

    def get_full_display_name(self) -> str:
        """Ex: 'Florete de Aço [Raro +3] (2/2 Runas)'"""
        lvl_str = f" +{self.level}" if self.level > 1 else ""
        runes_str = f" ({len(self.socketed_runes)}/{self.max_rune_slots} 🔮)"
        return f"{self.name} [{self.rarity}{lvl_str}]{runes_str}"

    def get_effective_stats(self) -> Dict[str, int]:
        """Calcula os atributos totais combinando base, nível de upgrade e bônus escalados das runas."""
        # Cada nível acima de 1 concede +12% aos atributos base
        lvl_multiplier = 1.0 + (0.12 * (self.level - 1))

        eff_atk = int(self.attack_bonus * lvl_multiplier)
        eff_mag = int(self.magic_bonus * lvl_multiplier)
        eff_def = int(self.defense_bonus * lvl_multiplier)
        eff_spd = int(self.speed_bonus * lvl_multiplier)

        # O nível do equipamento amplia o efeito das runas acopladas (+15% por nível do item)
        rune_scale = 1.0 + (0.15 * self.level)

        items_data = JsonLoader.load("items.json").get("items", {})

        for rune_id in self.socketed_runes:
            r_info = items_data.get(rune_id)
            if r_info and r_info.get("item_type") == "rune":
                r_type = r_info.get("rune_type")
                r_val = int(r_info.get("rune_value", 0) * rune_scale)

                if r_type == "attack":
                    eff_atk += r_val
                elif r_type == "magic":
                    eff_mag += r_val
                elif r_type == "defense":
                    eff_def += r_val
                elif r_type == "speed":
                    eff_spd += r_val

        return {
            "attack": eff_atk,
            "magic": eff_mag,
            "defense": eff_def,
            "speed": eff_spd,
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "slot": self.slot,
            "instance_id": self.instance_id,
            "description": self.description,
            "attack_bonus": self.attack_bonus,
            "magic_bonus": self.magic_bonus,
            "defense_bonus": self.defense_bonus,
            "speed_bonus": self.speed_bonus,
            "value_in_iron_coins": self.value_in_iron_coins,
            "rarity": self.rarity,
            "level": self.level,
            "max_rune_slots": self.max_rune_slots,
            "socketed_runes": self.socketed_runes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Equipment":
        return cls(
            id=data["id"],
            name=data["name"],
            slot=data["slot"],
            instance_id=data.get("instance_id", str(uuid.uuid4())[:8]),
            description=data.get("description", ""),
            attack_bonus=data.get("attack_bonus", 0),
            magic_bonus=data.get("magic_bonus", 0),
            defense_bonus=data.get("defense_bonus", 0),
            speed_bonus=data.get("speed_bonus", 0),
            value_in_iron_coins=data.get("value_in_iron_coins", 50),
            rarity=data.get("rarity", "Comum"),
            level=data.get("level", 1),
            max_rune_slots=data.get("max_rune_slots", 1),
            socketed_runes=data.get("socketed_runes", []),
        )
