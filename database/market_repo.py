import asyncio
import json
import os
import uuid
import time
import tempfile
import logging
from typing import Dict, Any, List, Optional, Tuple
from config import DATABASE_DIR
from models.player import Player
from database.player_repo import PlayerRepository
from database.item_repo import ItemRepository

logger = logging.getLogger(__name__)


def _sort_listings_by_price(listings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ordena listagens do mais barato para o mais caro."""
    return sorted(listings, key=lambda l: l.get("price_iron_coins", 0))


class MarketRepository:
    """
    Repositório de Persistência do Mercado de Trocas entre Jogadores (Player-to-Player Marketplace).
    Mantém listagens em cache em memória para acesso rápido e persiste em disco assincronamente.
    Itens são separados de equipamentos e sempre ordenados do mais barato para o mais caro.
    """

    FILE_PATH = os.path.join(DATABASE_DIR, "market_listings.json")
    _listings_cache: List[Dict[str, Any]] = []
    _initialized: bool = False

    @classmethod
    async def ensure_initialized(cls):
        """Carrega o cache de listagens em memória uma única vez na inicialização do bot."""
        if not cls._initialized:
            # Tenta carregar do arquivo; se não existir, começa com lista vazia
            cache = await asyncio.to_thread(cls._load_listings_sync)
            cls._listings_cache = cache
            cls._initialized = True
            logger.info(f"Market cache initialized with {len(cls._listings_cache)} listings")

    @classmethod
    def _load_listings_sync(cls) -> List[Dict[str, Any]]:
        """Carrega listagens do arquivo de forma síncrona (chamado em thread separado)."""
        if not os.path.exists(cls.FILE_PATH):
            return []
        try:
            with open(cls.FILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erro ao ler market_listings.json: {e}")
            return []

    @classmethod
    def _save_listings_sync(cls, listings: List[Dict[str, Any]]) -> bool:
        """Salva listagens em arquivo de forma síncrona (chamado em thread separado)."""
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
    async def get_all_active_listings(cls) -> List[Dict[str, Any]]:
        """Retorna todas as listagens de venda disponíveis, ordenadas do mais barato para o mais caro."""
        await cls.ensure_initialized()
        return _sort_listings_by_price(list(cls._listings_cache))

    @classmethod
    async def get_listings_by_type(cls, item_type: str) -> List[Dict[str, Any]]:
        """Retorna listagens filtradas por tipo ('material', 'consumable', 'rune', 'equipment')."""
        await cls.ensure_initialized()
        filtered = [l for l in cls._listings_cache if l.get("item_type") == item_type]
        return _sort_listings_by_price(filtered)

    @classmethod
    async def get_equipment_listings_by_slot(cls, slot: str) -> List[Dict[str, Any]]:
        """Retorna listagens de equipamentos filtrados por slot (weapon, staff, armor, accessory)."""
        await cls.ensure_initialized()
        equipment_listings = [
            l for l in cls._listings_cache
            if l.get("item_type") == "equipment" and l.get("slot") == slot
        ]
        return _sort_listings_by_price(equipment_listings)

    @classmethod
    async def create_listing(
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

        if quantity <= 0:
            return False, "A quantidade deve ser superior a 0."

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
            "item_type": item_type,
            "item_name": item_name,
            "quantity": quantity,
            "price_iron_coins": price_iron_coins,
            "equipment_data": equipment_data,
            "created_at": time.time(),
        }

        # Atualiza cache em memória
        cls._listings_cache.append(listing)

        # Persiste em disco de forma assíncrona (não-blocking)
        await asyncio.to_thread(cls._save_listings_sync, list(cls._listings_cache))

        return True, f"Oferta cadastrada com sucesso no Mercado da Guilda! (Preço: {price_iron_coins} Ferros / Qtd: {quantity})"

    @classmethod
    async def buy_listing(cls, buyer: Player, listing_id: str) -> Tuple[bool, str]:
        """Processa a compra de uma oferta listada no mercado."""
        await cls.ensure_initialized()
        listings = list(cls._listings_cache)
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
        seller = await PlayerRepository.get_player_async(seller_chat_id)
        if seller:
            seller.iron_coins += price
            await PlayerRepository.save_player_async(seller)

        # 4. Remove a listagem do mercado
        cls._listings_cache = [l for l in cls._listings_cache if l["id"] != listing_id]
        await asyncio.to_thread(cls._save_listings_sync, list(cls._listings_cache))

        return True, f"Você comprou [{target_listing['item_name']}] por {price} Moedas de Ferro!"

    @classmethod
    async def cancel_listing(cls, player: Player, listing_id: str) -> Tuple[bool, str]:
        """Cancela uma oferta do próprio jogador e devolve os itens à sua mochila."""
        await cls.ensure_initialized()
        listings = list(cls._listings_cache)
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

        cls._listings_cache = [l for l in cls._listings_cache if l["id"] != listing_id]
        await asyncio.to_thread(cls._save_listings_sync, list(cls._listings_cache))

        return True, f"Anúncio cancelado! O item [{target_listing['item_name']}] retornou para sua mochila."