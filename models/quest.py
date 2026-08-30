from dataclasses import dataclass, field
from typing import Dict, Any, List


@dataclass
class Quest:
    """
    Missão da Guilda de Aventureiros.
    Ranks: F, E, D, C, B, A, S.
    Tipos: 'slay' (abate), 'gather' (coleta), 'explore' (exploração de labirinto/dungeon).
    """
    id: str
    title: str
    rank: str
    region: str
    description: str
    quest_type: str
    target_id: str
    required_count: int
    reward_iron_coins: int
    reward_guild_points: int
    reward_xp: int
    reward_items: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "rank": self.rank,
            "region": self.region,
            "description": self.description,
            "quest_type": self.quest_type,
            "target_id": self.target_id,
            "required_count": self.required_count,
            "reward_iron_coins": self.reward_iron_coins,
            "reward_guild_points": self.reward_guild_points,
            "reward_xp": self.reward_xp,
            "reward_items": self.reward_items,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Quest":
        return cls(
            id=data["id"],
            title=data["title"],
            rank=data.get("rank", "F"),
            region=data.get("region", "Fittoa"),
            description=data.get("description", ""),
            quest_type=data.get("quest_type", "slay"),
            target_id=data.get("target_id", ""),
            required_count=data.get("required_count", 1),
            reward_iron_coins=data.get("reward_iron_coins", 50),
            reward_guild_points=data.get("reward_guild_points", 10),
            reward_xp=data.get("reward_xp", 100),
            reward_items=data.get("reward_items", []),
        )
