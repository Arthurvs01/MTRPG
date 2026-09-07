import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class Party:
    """Representa um Grupo de Aventureiros (Party/Guild)."""

    party_id: str
    name: str
    leader_id: int
    members: List[int] = field(default_factory=list)  # Lista de chat_ids
    member_roles: Dict[int, str] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    level: int = 1
    exp: int = 0
    funds: int = 0  # Fundo comum do grupo
    is_public: bool = True  # Se o grupo aparece na lista pública
    join_requests: List[int] = field(default_factory=list)  # Lista de chat_ids que pediram para entrar

    @classmethod
    def create(cls, party_id: str, leader_chat_id: int, name: str, is_public: bool = True) -> "Party":
        """Factory method to create a new party with leader."""
        party = cls(
            party_id=party_id,
            name=name,
            leader_id=leader_chat_id,
            members=[leader_chat_id],
            member_roles={leader_chat_id: "leader"},
            created_at=time.time(),
            level=1,
            exp=0,
            funds=0,
            is_public=is_public,
            join_requests=[],
        )
        return party

    def add_member(self, player_chat_id: int, role: str = "member") -> bool:
        if player_chat_id in self.members:
            return False
        if len(self.members) >= 10:  # Máximo 10 membros por grupo
            return False
        self.members.append(player_chat_id)
        self.member_roles[player_chat_id] = role
        return True

    def remove_member(self, chat_id: int) -> bool:
        if chat_id == self.leader_id:
            return False
        if chat_id in self.members:
            self.members.remove(chat_id)
            if chat_id in self.member_roles:
                del self.member_roles[chat_id]
            return True
        return False

    def is_member(self, chat_id: int) -> bool:
        return chat_id in self.members

    def is_leader(self, chat_id: int) -> bool:
        return chat_id == self.leader_id

    def get_role(self, chat_id: int) -> str:
        return self.member_roles.get(chat_id, "")

    def promote_leader(self, new_leader_id: int) -> bool:
        if new_leader_id in self.members and new_leader_id != self.leader_id:
            self.member_roles[self.leader_id] = "member"
            self.leader_id = new_leader_id
            self.member_roles[new_leader_id] = "leader"
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "party_id": self.party_id,
            "name": self.name,
            "leader_id": self.leader_id,
            "members": self.members,
            "member_roles": self.member_roles,
            "created_at": self.created_at,
            "level": self.level,
            "exp": self.exp,
            "funds": self.funds,
            "is_public": self.is_public,
            "join_requests": self.join_requests,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Party":
        party = cls.__new__(cls)
        party.party_id = data["party_id"]
        party.name = data["name"]
        party.leader_id = data["leader_id"]
        party.members = data.get("members", [])
        party.member_roles = data.get("member_roles", {})
        party.created_at = data.get("created_at", time.time())
        party.level = data.get("level", 1)
        party.exp = data.get("exp", 0)
        party.funds = data.get("funds", 0)
        party.is_public = data.get("is_public", True)
        party.join_requests = data.get("join_requests", [])
        return party