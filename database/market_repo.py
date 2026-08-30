import os
import json
import uuid
import time
import tempfile
import logging
from typing import Dict, Any, List, Optional
from config import DATABASE_DIR
from models.player import Player
from database.player_repo import PlayerRepository
from database.item_repo import ItemRepository

logger = logging.getLogger(__name__)


class MarketRepository:
    """
    Repositório de Persistência do Mercado de Trocas entre Jogadores (Player-to-Player Marketplace).
    Armazena ofertas de venda ativas de forma atômica e segura.
    """

    FILE_PATH = os.path.join(DATABASE_DIR, "market_listings.json")

    @classmethod
    def _load_listings(cls) -> List[Dict[str, Any]]:
        if not os.path.exists(cls.FILE_PATH):
            return []
        try:
            with open(cls.FILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erro ao ler market_listings.json: {e}")
            return []

    @classmethod
    def _save_listings(cls, listings: List[Dict[str, Any]]) -> bool:
        os.makedirs(os.path.dirname(cls.FILE_PATH), exist_ok=True)
        try:
            dir_name = os.path.dirname(cls.FILE_PATH)
            with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, encoding="utf-8") as tf:
                json.dump(listings, tf, indent=2, ensure_ascii=False)
                temp_name = tf.name
            os.replace(temp_name, cls.FILE_PATH)
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar market_listings.json: {e}")
            return False

    @classmethod
    def get_all_active_listings(cls) -> List[Dict[str, Any]]:
        """Retorna todas as listagens de venda disponíveis."""
        return cls._load_listings()

    @classmethod
    def create_listing(
        cls,
        seller: Player,
        item_id: str,
        item_type: str,
        quantity: int,
        price_iron_coins: int,
        equipment_data: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str]:
        """Cria uma nova oferta de venda no mercado."""
        if price_iron_coins <= 0:
            return False, "O preço deve ser superior a 0 Moedas de Ferro."

        listing_id = str(uuid.uuid4())[:8]

        item_name = item_id
        if item_type == "equipment" and equipment_data:
            item_name = equipment_data.get("name", "Equipamento")
        else:
            item_obj = ItemRepository.get_item(item_id)
            if item_obj:
                item_name = item_obj.name

        listing = {
            "id": listing_id,
            "seller_chat_id": seller.chat_id,
            "seller_name": seller.character_name,
            "item_id": item_id,
            "item_type": item_type,  # 'material', 'consumable', 'rune', 'equipment'
            "item_name": item_name,
            "quantity": quantity,
            "price_iron_coins": price_iron_coins,
            "equipment_data": equipment_data,
            "created_at": time.time(),
        }

        listings = cls._load_listings()
        listings.append(listing)
        if cls._save_listings(listings):
            return True, f"Oferta cadastrada com sucesso no Mercado da Guilda! (Preço: {price_iron_coins} Ferros)"
        return False, "Erro ao salvar anúncio no mercado."

    @classmethod
    def buy_listing(cls, buyer: Player, listing_id: str) -> Tuple[bool, str]:
        """Processa a compra de uma oferta listada no mercado."""
        listings = cls._load_listings()
        target_listing = None
        for l in listings:
            if l["id"] == listing_id:
                target_listing = l
                break

        if not target_listing:
            return False, "Esta oferta já foi adquirida ou cancelada."

        if target_listing["seller_chat_id"] == buyer.chat_id:
            return False, "Você não pode comprar sua própria oferta. Use a opção de Cancelar Anúncio."

        price = target_listing["price_iron_coins"]
        if buyer.iron_coins < price:
            return False, f"Moedas insuficientes ({buyer.iron_coins}/{price} Ferros)."

        # 1. Deduz moedas do comprador
        buyer.iron_coins -= price

        # 2. Adiciona item ao comprador
        item_type = target_listing["item_type"]
        item_id = target_listing["item_id"]
        qty = target_listing.get("quantity", 1)

        if item_type == "equipment" and target_listing.get("equipment_data"):
            buyer.inventory.setdefault("equipment", []).append(target_listing["equipment_data"])
        elif item_type == "consumable":
            consumables = buyer.inventory.setdefault("consumables", {})
            consumables[item_id] = consumables.get(item_id, 0) + qty
        elif item_type == "rune":
            runes = buyer.inventory.setdefault("runes", {})
            runes[item_id] = runes.get(item_id, 0) + qty
        else:
            materials = buyer.inventory.setdefault("materials", {})
            materials[item_id] = materials.get(item_id, 0) + qty

        # 3. Credita moedas no vendedor
        seller_chat_id = target_listing["seller_chat_id"]
        seller = PlayerRepository.get_player(seller_chat_id)
        if seller:
            seller.iron_coins += price
            PlayerRepository.save_player(seller)

        # 4. Remove a listagem do mercado
        listings = [l for l in listings if l["id"] != listing_id]
        cls._save_listings(listings)

        return True, f"Você comprou [{target_listing['item_name']}] por {price} Moedas de Ferro!"

    @classmethod
    def cancel_listing(cls, player: Player, listing_id: str) -> Tuple[bool, str]:
        """Cancela uma oferta do próprio jogador e devolve os itens à sua mochila."""
        listings = cls._load_listings()
        target_listing = None
        for l in listings:
            if l["id"] == listing_id and l["seller_chat_id"] == player.chat_id:
                target_listing = l
                break

        if not target_listing:
            return False, "Oferta não encontrada ou não pertence a você."

        # Devolve o item ao jogador
        item_type = target_listing["item_type"]
        item_id = target_listing["item_id"]
        qty = target_listing.get("quantity", 1)

        if item_type == "equipment" and target_listing.get("equipment_data"):
            player.inventory.setdefault("equipment", []).append(target_listing["equipment_data"])
        elif item_type == "consumable":
            consumables = player.inventory.setdefault("consumables", {})
            consumables[item_id] = consumables.get(item_id, 0) + qty
        elif item_type == "rune":
            runes = player.inventory.setdefault("runes", {})
            runes[item_id] = runes.get(item_id, 0) + qty
        else:
            materials = player.inventory.setdefault("materials", {})
            materials[item_id] = materials.get(item_id, 0) + qty

        listings = [l for l in listings if l["id"] != listing_id]
        cls._save_listings(listings)

        return True, f"Anúncio cancelado! O item [{target_listing['item_name']}] retornou para sua mochila."
