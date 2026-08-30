from dataclasses import dataclass, field
from typing import Dict, Any, List


@dataclass
class Spell:
    """
    Feitiço mágico de Mushoku Tensei.
    Elementos: Fogo, Água, Vento, Terra, Cura/Desintoxicação, Barreira.
    Ranks: Iniciante, Intermediário, Avançado, Santo, Rei, Imperial, Divino.
    """
    id: str
    name: str
    element: str
    rank: str
    mana_cost: int
    base_power: int
    incantation: str = ""  # Canto tradicional do feitiço
    description: str = ""
    effects: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "element": self.element,
            "rank": self.rank,
            "mana_cost": self.mana_cost,
            "base_power": self.base_power,
            "incantation": self.incantation,
            "description": self.description,
            "effects": self.effects,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Spell":
        return cls(
            id=data["id"],
            name=data["name"],
            element=data.get("element", "Fogo"),
            rank=data.get("rank", "Iniciante"),
            mana_cost=data.get("mana_cost", 5),
            base_power=data.get("base_power", 15),
            incantation=data.get("incantation", ""),
            description=data.get("description", ""),
            effects=data.get("effects", {}),
        )


@dataclass
class SwordSkill:
    """
    Técnica dos 3 Grandes Estilos de Espada:
    - Estilo Deus da Espada (Ataque relâmpago, Espada de Luz)
    - Estilo Deus da Água (Contra-ataque, Parry absoluto, Fluxo)
    - Estilo Deus do Norte (Arremesso, truques, esquiva oportunista)
    """
    id: str
    name: str
    style: str
    rank: str
    stamina_cost: int
    base_power: int
    speed_modifier: float = 1.0
    parry_chance: float = 0.0
    description: str = ""
    effects: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "style": self.style,
            "rank": self.rank,
            "stamina_cost": self.stamina_cost,
            "base_power": self.base_power,
            "speed_modifier": self.speed_modifier,
            "parry_chance": self.parry_chance,
            "description": self.description,
            "effects": self.effects,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SwordSkill":
        return cls(
            id=data["id"],
            name=data["name"],
            style=data.get("style", "Deus da Espada"),
            rank=data.get("rank", "Iniciante"),
            stamina_cost=data.get("stamina_cost", 5),
            base_power=data.get("base_power", 20),
            speed_modifier=data.get("speed_modifier", 1.0),
            parry_chance=data.get("parry_chance", 0.0),
            description=data.get("description", ""),
            effects=data.get("effects", {}),
        )
