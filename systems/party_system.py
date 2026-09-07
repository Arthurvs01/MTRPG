import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from models.player import Player
from models.party import Party
from database.player_repo import PlayerRepository
from database.party_repo import PartyRepository

logger = logging.getLogger(__name__)


class PartySystem:
    """Sistema de Gerenciamento de Grupos de Aventureiros."""

    _parties: Dict[str, Party] = {}
    _initialized: bool = False

    @classmethod
    async def initialize(cls):
        """Carrega todos os grupos salvos em disco para a memória."""
        if cls._initialized:
            return
        parties = await PartyRepository.load_all_parties()
        for party in parties:
            cls._parties[party.party_id] = party
            # Atualiza party_id e party_role nos players
            for member_id in party.members:
                player = PlayerRepository.get_player_sync(member_id)
                if player:
                    player.party_id = party.party_id
                    player.party_role = party.get_role(member_id)
                    PlayerRepository.save_player_sync(player)
        cls._initialized = True
        logger.info(f"PartySystem inicializado com {len(cls._parties)} grupos")

    @classmethod
    def initialize_sync(cls):
        """Versão síncrona para carregar grupos na inicialização."""
        if cls._initialized:
            return
        parties = PartyRepository.load_all_parties_sync()
        for party in parties:
            cls._parties[party.party_id] = party
            for member_id in party.members:
                player = PlayerRepository.get_player_sync(member_id)
                if player:
                    player.party_id = party.party_id
                    player.party_role = party.get_role(member_id)
                    PlayerRepository.save_player_sync(player)
        cls._initialized = True
        logger.info(f"PartySystem inicializado (sync) com {len(cls._parties)} grupos")

    @classmethod
    async def _save_party(cls, party: Party) -> bool:
        """Salva o grupo no repositório."""
        return await PartyRepository.save_party(party)

    @classmethod
    def _save_party_sync(cls, party: Party) -> bool:
        """Versão síncrona para salvar o grupo."""
        return PartyRepository.save_party_sync(party)

    @classmethod
    async def create_party(cls, leader: Player, name: str, is_public: bool = True) -> Tuple[bool, str, Optional[Party]]:
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
        party = Party.create(party_id, leader.chat_id, name, is_public)
        cls._parties[party_id] = party

        leader.party_id = party_id
        leader.party_role = "leader"

        # Salva o grupo e o player
        await cls._save_party(party)
        await PlayerRepository.save_player(leader)

        return True, f"Grupo '{name}' criado com sucesso! Você é o líder.", party

    @classmethod
    def create_party_sync(cls, leader: Player, name: str, is_public: bool = True) -> Tuple[bool, str, Optional[Party]]:
        """Versão síncrona para criar grupo."""
        if leader.party_id:
            return False, "Você já faz parte de um grupo!", None

        if len(name) < 3 or len(name) > 24:
            return False, "Nome do grupo deve ter entre 3 e 24 caracteres.", None

        for party in cls._parties.values():
            if party.name.lower() == name.lower():
                return False, "Já existe um grupo com este nome.", None

        party_id = f"party_{leader.chat_id}_{int(time.time())}"
        party = Party.create(party_id, leader.chat_id, name, is_public)
        cls._parties[party_id] = party

        leader.party_id = party_id
        leader.party_role = "leader"

        cls._save_party_sync(party)
        PlayerRepository.save_player_sync(leader)

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

        party.add_member(player.chat_id)
        player.party_id = party_id
        player.party_role = "member"
        player.party_join_requests.remove(party_id)

        cls._save_party_sync(party)
        PlayerRepository.save_player_sync(player)

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

        cls._save_party_sync(party)
        PlayerRepository.save_player_sync(player)

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

        cls._save_party_sync(party)

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

        # Deleta o arquivo do grupo
        PartyRepository._delete_party_sync(PartyRepository._get_party_file(party.party_id))
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

        cls._save_party_sync(party)

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
        cls._save_party_sync(party)
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

        cls._save_party_sync(party)
        PlayerRepository.save_player_sync(player)

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

        cls._save_party_sync(party)
        PlayerRepository.save_player_sync(leader)

        return True, f"Retirado {amount} Ferros do fundo do grupo."

    @classmethod
    def get_public_parties(cls) -> List[Dict[str, Any]]:
        """Retorna lista de grupos públicos para exibição."""
        public_parties = []
        for party in cls._parties.values():
            if party.is_public and len(party.members) < 10:
                public_parties.append({
                    "party_id": party.party_id,
                    "name": party.name,
                    "leader_name": PlayerRepository.get_player_sync(party.leader_id).character_name if PlayerRepository.get_player_sync(party.leader_id) else "Desconhecido",
                    "level": party.level,
                    "member_count": len(party.members),
                    "max_members": 10,
                })
        return public_parties

    @classmethod
    def request_join(cls, player: Player, party_id: str) -> Tuple[bool, str]:
        """Jogador solicita entrada em um grupo público."""
        if player.party_id:
            return False, "Você já está em um grupo."

        party = cls._parties.get(party_id)
        if not party:
            return False, "Grupo não encontrado."

        if not party.is_public:
            return False, "Este grupo não aceita solicitações públicas."

        if party.is_member(player.chat_id):
            return False, "Você já está neste grupo."

        if len(party.members) >= 10:
            return False, "Grupo cheio (máximo 10 membros)."

        if player.chat_id in party.join_requests:
            return False, "Você já solicitou entrada neste grupo."

        party.join_requests.append(player.chat_id)

        cls._save_party_sync(party)

        return True, f"Solicitação de entrada enviada para o grupo '{party.name}'! Aguarde aprovação do líder."

    @classmethod
    def get_join_requests(cls, leader: Player) -> List[Dict[str, Any]]:
        """Retorna solicitações de entrada pendentes para o líder."""
        if not leader.party_id:
            return []

        party = cls._parties.get(leader.party_id)
        if not party or not party.is_leader(leader.chat_id):
            return []

        requests = []
        for requester_id in party.join_requests:
            requester = PlayerRepository.get_player_sync(requester_id)
            if requester:
                requests.append({
                    "chat_id": requester.chat_id,
                    "name": requester.character_name,
                    "level": requester.level,
                    "vocation": requester.vocation,
                })
        return requests

    @classmethod
    def approve_join_request(cls, leader: Player, target_chat_id: int) -> Tuple[bool, str]:
        """Líder aprova solicitação de entrada."""
        if not leader.party_id:
            return False, "Você não é líder de nenhum grupo."

        party = cls._parties.get(leader.party_id)
        if not party or not party.is_leader(leader.chat_id):
            return False, "Apenas o líder pode aprovar solicitações."

        if target_chat_id not in party.join_requests:
            return False, "Solicitação não encontrada."

        target_player = PlayerRepository.get_player_sync(target_chat_id)
        if not target_player:
            return False, "Jogador não encontrado."

        if target_player.party_id:
            party.join_requests.remove(target_chat_id)
            return False, "Este jogador já entrou em outro grupo."

        if len(party.members) >= 10:
            return False, "Grupo cheio."

        party.join_requests.remove(target_chat_id)
        party.add_member(target_player.chat_id)
        target_player.party_id = party.party_id
        target_player.party_role = "member"
        PlayerRepository.save_player_sync(target_player)

        cls._save_party_sync(party)

        return True, f"{target_player.character_name} foi adicionado ao grupo!"

    @classmethod
    def deny_join_request(cls, leader: Player, target_chat_id: int) -> Tuple[bool, str]:
        """Líder recusa solicitação de entrada."""
        if not leader.party_id:
            return False, "Você não é líder de nenhum grupo."

        party = cls._parties.get(leader.party_id)
        if not party or not party.is_leader(leader.chat_id):
            return False, "Apenas o líder pode recusar solicitações."

        if target_chat_id not in party.join_requests:
            return False, "Solicitação não encontrada."

        party.join_requests.remove(target_chat_id)

        cls._save_party_sync(party)

        return True, "Solicitação recusada."

    @classmethod
    def toggle_public(cls, leader: Player) -> Tuple[bool, str]:
        """Alterna visibilidade pública do grupo."""
        if not leader.party_id:
            return False, "Você não está em um grupo."

        party = cls._parties.get(leader.party_id)
        if not party or not party.is_leader(leader.chat_id):
            return False, "Apenas o líder pode alterar esta configuração."

        party.is_public = not party.is_public

        cls._save_party_sync(party)

        status = "público" if party.is_public else "privado"
        return True, f"Grupo agora é {status}!"