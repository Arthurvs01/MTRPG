import logging
from typing import Dict, Optional, List
from core.json_loader import JsonLoader
from models.item import Item, Equipment

logger = logging.getLogger(__name__)


class ItemRepository:
    """Repositório central para catálogo de itens, consumíveis, armas e equipamentos."""

    @classmethod
    def get_item(cls, item_id: str) -> Optional[Item]:
        data = JsonLoader.load("items.json")
        items = data.get("items", {})
        if item_id in items:
            item_data = items[item_id]
            item_data["id"] = item_id
            return Item.from_dict(item_data)
        return None

    @classmethod
    def get_equipment(cls, equip_id: str) -> Optional[Equipment]:
        data = JsonLoader.load("items.json")
        equipments = data.get("equipments", {})
        if equip_id in equipments:
            eq_data = equipments[equip_id]
            eq_data["id"] = equip_id
            return Equipment.from_dict(eq_data)
        return None

    @classmethod
    def get_shop_items(cls, continent: str = "central") -> List[Dict]:
        data = JsonLoader.load("items.json")
        shops = data.get("shops", {})
        return shops.get(continent, shops.get("central", []))
