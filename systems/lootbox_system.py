import time
import random
import logging
from typing import Dict, Any, Tuple, List
from models.player import Player
from core.json_loader import JsonLoader
from database.item_repo import ItemRepository

logger = logging.getLogger(__name__)


class LootboxSystem:
    """
    Sistema Central de LootBoxes & Recompensas Especiais:
    - Baú Diário Gratuito (Cooldown 24h)
    - Baú de Caçada (Dropado em monstros)
    - Baú Nobre de Asura & Relíquia das Seis Faces (Diamantes)
    """

    @classmethod
    def get_lootboxes_data(cls) -> Dict[str, Any]:
        return JsonLoader.load("lootboxes.json").get("lootboxes", {})

    @classmethod
    async def get_lootboxes_data_async(cls) -> Dict[str, Any]:
        data = await JsonLoader.load_async("lootboxes.json")
        return data.get("lootboxes", {})

    @classmethod
    def get_daily_status(cls, player: Player) -> Tuple[bool, str]:
        """Retorna se o baú diário está disponível ou o tempo restante."""
        now = time.time()
        elapsed = now - player.last_daily_lootbox_timestamp
        cooldown_seconds = 24 * 3600  # 24 horas

        if elapsed >= cooldown_seconds or player.last_daily_lootbox_timestamp == 0.0:
            return True, "✅ Disponível para resgate agora!"

        remaining = int(cooldown_seconds - elapsed)
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        return False, f"⏳ Disponível em {hours}h {minutes}m"

    @classmethod
    def open_lootbox(cls, player: Player, box_id: str) -> Tuple[bool, str, Dict[str, Any]]:
        boxes = cls.get_lootboxes_data()
        if box_id not in boxes:
            return False, "Tipo de baú desconhecido.", {}

        box_data = boxes[box_id]
        cost_type = box_data.get("cost_type", "free")
        cost_amount = box_data.get("cost_amount", 0)

        # 1. Validação de Custo / Cooldown
        if cost_type == "free":
            can_open, status_str = cls.get_daily_status(player)
            if not can_open:
                return False, f"O Baú Diário ainda não está pronto ({status_str}).", {}
            player.last_daily_lootbox_timestamp = time.time()

        elif cost_type == "item_hunt_chest":
            if player.hunt_lootbox_count < 1:
                return False, "Você não possui nenhum Baú Arcano de Caçada na mochila.", {}
            player.hunt_lootbox_count -= 1

    @classmethod
    async def open_lootbox_async(cls, player: Player, box_id: str) -> Tuple[bool, str, Dict[str, Any]]:
        boxes = await cls.get_lootboxes_data_async()
        if box_id not in boxes:
            return False, "Tipo de baú desconhecido.", {}

        box_data = boxes[box_id]
        cost_type = box_data.get("cost_type", "free")
        cost_amount = box_data.get("cost_amount", 0)

        # 1. Validação de Custo / Cooldown
        if cost_type == "free":
            can_open, status_str = cls.get_daily_status(player)
            if not can_open:
                return False, f"O Baú Diário ainda não está pronto ({status_str}).", {}
            player.last_daily_lootbox_timestamp = time.time()

        elif cost_type == "item_hunt_chest":
            if player.hunt_lootbox_count < 1:
                return False, "Você não possui nenhum Baú Arcano de Caçada na mochila.", {}
            player.hunt_lootbox_count -= 1

        elif cost_type == "diamonds":
            if player.diamonds < cost_amount:
                return False, f"Diamantes insuficientes (Necessário: {cost_amount} 💎, Você tem: {player.diamonds}).", {}
            player.diamonds -= cost_amount

        # 2. Sorteio de Moedas & Diamantes
        min_coins = box_data.get("min_iron_coins", 0)
        max_coins = box_data.get("max_iron_coins", 0)
        awarded_coins = random.randint(min_coins, max_coins) if max_coins > 0 else 0
        player.iron_coins += awarded_coins

        min_dia = box_data.get("min_diamonds", 0)
        max_dia = box_data.get("max_diamonds", 0)
        awarded_diamonds = random.randint(min_dia, max_dia) if max_dia > 0 else 0
        player.diamonds += awarded_diamonds

        # 3. Sorteio de Itens / Equipamentos por Peso
        possible_items = box_data.get("possible_items", [])
        awarded_items_list = []

        if possible_items:
            # Sorteia 1 a 2 itens da lista com base nos pesos
            total_draws = 2 if len(possible_items) >= 2 else 1
            for _ in range(total_draws):
                weights = [entry.get("weight", 10) for entry in possible_items]
                chosen_entry = random.choices(possible_items, weights=weights, k=1)[0]

                item_id = chosen_entry["id"]
                is_equipment = chosen_entry.get("type") == "equipment"

                if is_equipment:
                    eq = ItemRepository.get_equipment(item_id)
                    eq_name = eq.name if eq else item_id
                    player.inventory.setdefault("equipment", []).append(item_id)
                    awarded_items_list.append(f"⚔️ <b>{eq_name}</b> (Equipamento)")
                else:
                    item = ItemRepository.get_item(item_id)
                    item_name = item.name if item else item_id
                    qty = random.randint(chosen_entry.get("min_qty", 1), chosen_entry.get("max_qty", 1))

                    if item and item.item_type == "consumable":
                        consumables = player.inventory.setdefault("consumables", {})
                        consumables[item_id] = consumables.get(item_id, 0) + qty
                    else:
                        materials = player.inventory.setdefault("materials", {})
                        materials[item_id] = materials.get(item_id, 0) + qty

                    awarded_items_list.append(f"📦 <b>{item_name}</b> x{qty}")

        rewards_summary = []
        if awarded_coins > 0:
            rewards_summary.append(f"💰 +{awarded_coins} Moedas de Ferro")
        if awarded_diamonds > 0:
            rewards_summary.append(f"💎 +{awarded_diamonds} Diamantes")
        rewards_summary.extend(awarded_items_list)

        result_dict = {
            "box_name": box_data.get("name", "Baú"),
            "iron_coins": awarded_coins,
            "diamonds": awarded_diamonds,
            "rewards_text": "\n".join(rewards_summary) if rewards_summary else "Nenhum item adicional."
        }

        return True, f"Você abriu [{box_data.get('name')}] com sucesso!", result_dict
