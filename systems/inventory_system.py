import logging
from typing import Dict, Any, Tuple, Optional
from models.player import Player
from database.item_repo import ItemRepository

logger = logging.getLogger(__name__)


class InventorySystem:
    """
    Sistema de Inventário, Consumíveis, Troca de Equipamentos e Economia de Moedas.
    """

    @classmethod
    def use_consumable(cls, player: Player, item_id: str) -> Tuple[bool, str]:
        consumables = player.inventory.get("consumables", {})
        qty = consumables.get(item_id, 0)
        if qty <= 0:
            return False, "Você não possui este item em seu inventário."

        item = ItemRepository.get_item(item_id)
        if not item:
            return False, "Item não encontrado no catálogo."

        heal_hp = item.effects.get("heal_hp", 0)
        restore_mana = item.effects.get("restore_mana", 0)

        logs = []
        if heal_hp > 0:
            old_hp = player.hp
            player.hp = min(player.max_hp, player.hp + heal_hp)
            actual_heal = player.hp - old_hp
            logs.append(f"❤️ Recuperou <b>{actual_heal} HP</b>.")

        if restore_mana > 0:
            old_mana = player.mana
            player.mana = min(player.max_mana, player.mana + restore_mana)
            actual_mana = player.mana - old_mana
            logs.append(f"💧 Restaurou <b>{actual_mana} Mana</b>.")

        consumables[item_id] -= 1
        if consumables[item_id] <= 0:
            del consumables[item_id]

        return True, f"Você utilizou [{item.name}]! " + " ".join(logs)

    @classmethod
    def equip_item(cls, player: Player, equip_id: str) -> Tuple[bool, str]:
        equipment = ItemRepository.get_equipment(equip_id)
        if not equipment:
            return False, "Equipamento não encontrado."

        slot = equipment.slot
        if slot not in player.equipped:
            return False, "Slot de equipamento inválido."

        # Se já tem algo equipado, devolve pro inventário
        current_eq = player.equipped.get(slot)
        if current_eq:
            player.inventory.setdefault("equipment", []).append(current_eq["id"])

        player.equipped[slot] = equipment.to_dict()
        if equip_id in player.inventory.get("equipment", []):
            player.inventory["equipment"].remove(equip_id)

        return True, f"Você equipou [{equipment.name}] no slot [{slot}] com sucesso!"

    @classmethod
    def buy_item(cls, player: Player, item_id: str, item_type: str = "item") -> Tuple[bool, str]:
        if item_type == "item":
            item = ItemRepository.get_item(item_id)
            if not item:
                return False, "Item indisponível na loja."
            price = item.value_in_iron_coins
            if player.iron_coins < price:
                return False, f"Moedas de Ferro insuficientes (Necessário: {price}, Você tem: {player.iron_coins})."

            player.iron_coins -= price
            if item.item_type == "consumable":
                consumables = player.inventory.setdefault("consumables", {})
                consumables[item_id] = consumables.get(item_id, 0) + 1
            else:
                materials = player.inventory.setdefault("materials", {})
                materials[item_id] = materials.get(item_id, 0) + 1
            return True, f"Você comprou [{item.name}] por {price} Moedas de Ferro!"

        elif item_type == "equipment":
            equipment = ItemRepository.get_equipment(item_id)
            if not equipment:
                return False, "Equipamento indisponível."
            price = equipment.value_in_iron_coins
            if player.iron_coins < price:
                return False, f"Moedas de Ferro insuficientes (Necessário: {price}, Você tem: {player.iron_coins})."

            player.iron_coins -= price
            player.inventory.setdefault("equipment", []).append(item_id)
            return True, f"Você adquiriu [{equipment.name}] por {price} Moedas de Ferro!"

        return False, "Tipo de compra inválido."
