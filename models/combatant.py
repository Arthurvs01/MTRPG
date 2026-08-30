from dataclasses import dataclass, field
from typing import Dict, Any, List


@dataclass
class Combatant:
    """Entidade base para combate: usada por Monstros e servindo de referência para atributos calculados."""
    id: str
    name: str
    level: int
    hp: int
    max_hp: int
    mana: int = 0
    max_mana: int = 0
    touki: int = 0  # Revestimento defensivo e ofensivo de aura de batalha
    attack: int = 10
    magic_power: int = 5
    defense: int = 5
    speed: int = 10
    skills: List[str] = field(default_factory=list)
    drops: List[Dict[str, Any]] = field(default_factory=list)
    xp_reward: int = 20
    coins_reward: int = 10
    danger_rank: str = "F"  # F, E, D, C, B, A, S

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "level": self.level,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "mana": self.mana,
            "max_mana": self.max_mana,
            "touki": self.touki,
            "attack": self.attack,
            "magic_power": self.magic_power,
            "defense": self.defense,
            "speed": self.speed,
            "skills": self.skills,
            "drops": self.drops,
            "xp_reward": self.xp_reward,
            "coins_reward": self.coins_reward,
            "danger_rank": self.danger_rank,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Combatant":
        return cls(
            id=data["id"],
            name=data["name"],
            level=data.get("level", 1),
            hp=data.get("hp", 100),
            max_hp=data.get("max_hp", data.get("hp", 100)),
            mana=data.get("mana", 0),
            max_mana=data.get("max_mana", 0),
            touki=data.get("touki", 0),
            attack=data.get("attack", 10),
            magic_power=data.get("magic_power", 5),
            defense=data.get("defense", 5),
            speed=data.get("speed", 10),
            skills=data.get("skills", []),
            drops=data.get("drops", []),
            xp_reward=data.get("xp_reward", 20),
            coins_reward=data.get("coins_reward", 10),
            danger_rank=data.get("danger_rank", "F"),
        )
