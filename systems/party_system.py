import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from models.player import Player
from database.player_repo import PlayerRepository

logger = logging.getLogger(__name__)


class Party:
    """Representa um Grupo de Aventureiros (Party/Guild)."""

    def __init__(self, party_id: str, leader: Player, name: str):
        self.party_id = party_id
        self.name = name
        self.leader_id = leader.chat_id
        self.members: List[int] = [leader.chat_id]  # Lista de chat_ids
        self.member_roles: Dict[int, str] = {leader.chat_id: "leader"}
        self.created_at = time.time()
        self.level = 1
        self.exp = 0
        self.funds = 0  # Fundo comum do grupo

    def add_member(self, player: Player, role: str = "member") -> bool:
        if player.chat_id in self.members:
            return False
        if len(self.members) >= 10:  # Máximo 10 membros por grupo
            return False
        self.members.append(player.chat_id)
        self.member_roles[player.chat_id] = role
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


class PartySystem:
    """Sistema de Gerenciamento de Grupos de Aventureiros."""

    _parties: Dict[str, Party] = {}

    @classmethod
    def create_party(cls, leader: Player, name: str) -> Tuple[bool, str, Optional[Party]]:
        """Cria um novo grupo de aventureiros."""
        if leader.party_id:
            return False, "Você já faz parte de um grupo!", None

        if len(name) < 3 or len(name) > 24:
            return False, "Nome do grupo deve ter entre 3 e 24 caracteres.", None

        # Verifica se nome já existe
        for party in cls._parties.values():
            if party.name.lower() == name.lower():
                return False, "Já existe um grupo com este nome.", None

        party_id = f"party_{leader.chat_id}_{int(time.time())}"
        party = Party(party_id, leader, name)
        cls._parties[party_id] = party

        leader.party_id = party_id
        leader.party_role = "leader"
        return True, f"Grupo '{name}' criado com sucesso! Você é o líder.", party

    @classmethod
    def invite_player(cls, leader: Player, target_player: Player) -> Tuple[bool, str]:
        """Líder convida jogador para o grupo."""
        if not leader.party_id:
            return False, "Você não é líder de nenhum grupo."

        party = cls._parties.get(leader.party_id)
        if not party:
            return False, "Grupo não encontrado."

        if not party.is_leader(leader.chat_id):
            return False, "Apenas o líder pode convidar."

        if party.is_member(target_player.chat_id):
            return False, "Este jogador já está no grupo."

        if target_player.party_id:
            return False, "Este jogador já faz parte de outro grupo."

        if len(party.members) >= 10:
            return False, "Grupo cheio (máximo 10 membros)."

        # Adiciona convite pendente
        if leader.party_id not in target_player.party_join_requests:
            target_player.party_join_requests.append(leader.party_id)

        return True, f"Convite enviado para {target_player.character_name}!"

    @classmethod
    def accept_invite(cls, player: Player, party_id: str) -> Tuple[bool, str]:
        """Jogador aceita convite para entrar no grupo."""
        if player.party_id:
            return False, "Você já está em um grupo."

        party = cls._parties.get(party_id)
        if not party:
            return False, "Grupo não encontrado."

        if party_id not in player.party_join_requests:
            return False, "Você não tem convite deste grupo."

        if len(party.members) >= 10:
            return False, "Grupo cheio."

        party.add_member(player)
        player.party_id = party_id
        player.party_role = "member"
        player.party_join_requests.remove(party_id)

        return True, f"Você entrou no grupo '{party.name}'!"

    @classmethod
    def decline_invite(cls, player: Player, party_id: str) -> Tuple[bool, str]:
        """Jogador recusa convite."""
        if party_id in player.party_join_requests:
            player.party_join_requests.remove(party_id)
            return True, "Convite recusado."
        return False, "Nenhum convite encontrado."

    @classmethod
    def leave_party(cls, player: Player) -> Tuple[bool, str]:
        """Jogador sai do grupo."""
        if not player.party_id:
            return False, "Você não está em nenhum grupo."

        party = cls._parties.get(player.party_id)
        if not party:
            player.party_id = None
            player.party_role = ""
            return True, "Grupo não encontrado, removido da sua lista."

        if party.is_leader(player.chat_id):
            return False, "O líder não pode sair. Transfira a liderança ou dissolva o grupo."

        party.remove_member(player.chat_id)
        player.party_id = None
        player.party_role = ""

        return True, f"Você saiu do grupo '{party.name}'."

    @classmethod
    def kick_member(cls, leader: Player, target_chat_id: int) -> Tuple[bool, str]:
        """Líder remove membro do grupo."""
        if not leader.party_id:
            return False, "Você não é líder de nenhum grupo."

        party = cls._parties.get(leader.party_id)
        if not party or not party.is_leader(leader.chat_id):
            return False, "Apenas o líder pode remover membros."

        target_player = PlayerRepository.get_player_sync(target_chat_id)
        if not target_player:
            return False, "Jogador não encontrado."

        if not party.is_member(target_chat_id):
            return False, "Este jogador não está no seu grupo."

        party.remove_member(target_chat_id)
        target_player.party_id = None
        target_player.party_role = ""
        PlayerRepository.save_player_sync(target_player)

        return True, f"{target_player.character_name} foi removido do grupo."

    @classmethod
    def disband_party(cls, leader: Player) -> Tuple[bool, str]:
        """Líder dissolve o grupo."""
        if not leader.party_id:
            return False, "Você não é líder de nenhum grupo."

        party = cls._parties.get(leader.party_id)
        if not party or not party.is_leader(leader.chat_id):
            return False, "Apenas o líder pode dissolver o grupo."

        # Remove party_id de todos os membros
        for member_id in party.members:
            member = PlayerRepository.get_player_sync(member_id)
            if member:
                member.party_id = None
                member.party_role = ""
                PlayerRepository.save_player_sync(member)

        del cls._parties[leader.party_id]
        return True, f"Grupo '{party.name}' foi dissolvido."

    @classmethod
    def transfer_leadership(cls, leader: Player, target_chat_id: int) -> Tuple[bool, str]:
        """Líder transfere liderança."""
        if not leader.party_id:
            return False, "Você não é líder de nenhum grupo."

        party = cls._parties.get(leader.party_id)
        if not party or not party.is_leader(leader.chat_id):
            return False, "Apenas o líder pode transferir liderança."

        if target_chat_id not in party.members:
            return False, "Jogador não está no grupo."

        if target_chat_id == leader.chat_id:
            return False, "Você já é o líder."

        target_player = PlayerRepository.get_player_sync(target_chat_id)
        if not target_player:
            return False, "Jogador não encontrado."

        party.promote_leader(target_chat_id)
        leader.party_role = "member"
        target_player.party_role = "leader"
        PlayerRepository.save_player_sync(leader)
        PlayerRepository.save_player_sync(target_player)

        return True, f"Liderança transferida para {target_player.character_name}!"

    @classmethod
    def get_party_info(cls, party_id: str) -> Optional[Dict[str, Any]]:
        """Retorna informações do grupo."""
        party = cls._parties.get(party_id)
        if not party:
            return None

        members_info = []
        for member_id in party.members:
            member = PlayerRepository.get_player_sync(member_id)
            if member:
                members_info.append({
                    "name": member.character_name,
                    "level": member.level,
                    "vocation": member.vocation,
                    "role": party.get_role(member_id),
                    "online": True,
                })
            else:
                members_info.append({
                    "name": "Desconhecido",
                    "level": 0,
                    "vocation": "?",
                    "role": party.get_role(member_id),
                    "online": False,
                })

        return {
            "party_id": party.party_id,
            "name": party.name,
            "leader_id": party.leader_id,
            "level": party.level,
            "exp": party.exp,
            "funds": party.funds,
            "members": members_info,
            "member_count": len(party.members),
            "max_members": 10,
        }

    @classmethod
    def add_party_exp(cls, party_id: str, exp: int) -> bool:
        """Adiciona experiência ao grupo."""
        party = cls._parties.get(party_id)
        if not party:
            return False
        party.exp += exp
        # Level up do grupo a cada 10000 exp
        new_level = (party.exp // 10000) + 1
        if new_level > party.level:
            party.level = new_level
        return True

    @classmethod
    def deposit_funds(cls, player: Player, amount: int) -> Tuple[bool, str]:
        """Deposita moedas no fundo do grupo."""
        if not player.party_id:
            return False, "Você não está em um grupo."

        if player.iron_coins < amount:
            return False, "Moedas insuficientes."

        party = cls._parties.get(player.party_id)
        if not party:
            return False, "Grupo não encontrado."

        player.iron_coins -= amount
        party.funds += amount
        return True, f"Depositado {amount} Ferros no fundo do grupo."

    @classmethod
    def withdraw_funds(cls, leader: Player, amount: int) -> Tuple[bool, str]:
        """Líder retira moedas do fundo do grupo."""
        if not leader.party_id:
            return False, "Você não é líder de nenhum grupo."

        party = cls._parties.get(leader.party_id)
        if not party or not party.is_leader(leader.chat_id):
            return False, "Apenas o líder pode retirar fundos."

        if party.funds < amount:
            return False, "Fundos insuficientes no grupo."

        party.funds -= amount
        leader.iron_coins += amount
        return True, f"Retirado {amount} Ferros do fundo do grupo."