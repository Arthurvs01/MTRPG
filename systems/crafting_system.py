import random
import logging
from typing import Dict, Any, Tuple, List, Optional
from models.player import Player
from models.item import Equipment
from core.json_loader import JsonLoader
from database.item_repo import ItemRepository

logger = logging.getLogger(__name__)


class CraftingSystem:
    """
    Sistema Central de Forja, Crafting de Equipamentos Mágicos, Upgrades e Runas.
    - Forja com Sorteio de Raridade (Comum, Raro, Santo, Imperial, Divino)
    - Upgrade de Nível do Equipamento (+1 a +10)
    - Engaste de Runas Mágicas que escalam com o Nível do Equipamento
    """

    RARITY_RATES = {
        "Comum": {"weight": 55, "slots": 1, "multiplier": 1.0},
        "Raro": {"weight": 30, "slots": 2, "multiplier": 1.3},
        "Santo": {"weight": 11, "slots": 3, "multiplier": 1.7},
        "Imperial": {"weight": 3.5, "slots": 4, "multiplier": 2.2},
        "Divino": {"weight": 0.5, "slots": 5, "multiplier": 3.0},
    }

    @classmethod
    def get_recipes(cls) -> Dict[str, Any]:
        return JsonLoader.load("crafting_recipes.json").get("recipes", {})

    @classmethod
    async def get_recipes_async(cls) -> Dict[str, Any]:
        data = await JsonLoader.load_async("crafting_recipes.json")
        return data.get("recipes", {})

    @classmethod
    def get_recipe(cls, recipe_id: str) -> Optional[Dict[str, Any]]:
        return cls.get_recipes().get(recipe_id)

    @classmethod
    def roll_rarity(cls) -> str:
        """Sorteia a raridade do equipamento produzido com base nas probabilidades canônicas."""
        rarities = list(cls.RARITY_RATES.keys())
        weights = [cls.RARITY_RATES[r]["weight"] for r in rarities]
        return random.choices(rarities, weights=weights, k=1)[0]

    @classmethod
    def craft_item(cls, player: Player, recipe_id: str) -> Tuple[bool, str, Optional[Equipment]]:
        recipe = cls.get_recipe(recipe_id)
        if not recipe:
            return False, "Receita de forja não encontrada.", None

        # 1. Verifica Moedas
        cost_coins = recipe.get("iron_coins_cost", 20)
        if player.iron_coins < cost_coins:
            return False, f"Moedas insuficientes ({player.iron_coins}/{cost_coins} Ferros).", None

        # 2. Verifica Materiais
        req_materials = recipe.get("required_materials", {})
        player_materials = player.inventory.get("materials", {})

        for mat_id, req_qty in req_materials.items():
            current_qty = player_materials.get(mat_id, 0)
            if current_qty < req_qty:
                mat_item = ItemRepository.get_item(mat_id)
                mat_name = mat_item.name if mat_item else mat_id
                return False, f"Material insuficiente: {mat_name} ({current_qty}/{req_qty}).", None

        # 3. Consome Moedas e Materiais
        player.iron_coins -= cost_coins
        for mat_id, req_qty in req_materials.items():
            player_materials[mat_id] -= req_qty
            if player_materials[mat_id] <= 0:
                del player_materials[mat_id]

        # 4. Sorteio de Raridade
        rarity = cls.roll_rarity()
        rarity_info = cls.RARITY_RATES[rarity]
        multiplier = rarity_info["multiplier"]
        slots = rarity_info["slots"]

        # 5. Instancia o Equipamento
        base_eq_id = recipe.get("equip_id")
        base_eq = ItemRepository.get_equipment(base_eq_id)
        if not base_eq:
            return False, "Modelo base de equipamento não encontrado.", None

        crafted_eq = Equipment(
            id=base_eq.id,
            name=base_eq.name,
            slot=base_eq.slot,
            description=base_eq.description,
            attack_bonus=int(base_eq.attack_bonus * multiplier),
            magic_bonus=int(base_eq.magic_bonus * multiplier),
            defense_bonus=int(base_eq.defense_bonus * multiplier),
            speed_bonus=int(base_eq.speed_bonus * multiplier),
            value_in_iron_coins=int(base_eq.value_in_iron_coins * multiplier),
            rarity=rarity,
            level=1,
            max_rune_slots=slots,
            socketed_runes=[],
        )

        player.inventory.setdefault("equipment", []).append(crafted_eq.to_dict())

        msg = (
            f"🔨 <b>Forja Concluída com Sucesso!</b>\n\n"
            f"Você forjou: <b>{crafted_eq.get_full_display_name()}</b>!\n"
            f"✨ <b>Raridade Obtida:</b> {rarity} (Multiplicador {multiplier}x)\n"
            f"🔮 <b>Slots de Runa Disponíveis:</b> {slots}\n"
        )
        return True, msg, crafted_eq

    @classmethod
    def upgrade_equipment(cls, player: Player, instance_id: str) -> Tuple[bool, str]:
        """Aprimora o nível de um equipamento em +1 (Máximo: +10)."""
        target_eq_dict = None
        is_equipped = False
        target_slot = None

        # Procura nos equipados
        for slot, eq_data in player.equipped.items():
            if eq_data and eq_data.get("instance_id") == instance_id:
                target_eq_dict = eq_data
                is_equipped = True
                target_slot = slot
                break

        # Procura na bolsa
        if not target_eq_dict:
            for eq_data in player.inventory.get("equipment", []):
                if isinstance(eq_data, dict) and eq_data.get("instance_id") == instance_id:
                    target_eq_dict = eq_data
                    break

        if not target_eq_dict:
            return False, "Equipamento não encontrado."

        current_lvl = target_eq_dict.get("level", 1)
        if current_lvl >= 10:
            return False, "Este equipamento já atingiu o nível máximo de aprimoramento (+10)!"

        # Custo do upgrade
        cost_coins = current_lvl * 40
        if player.iron_coins < cost_coins:
            return False, f"Moedas insuficientes para aprimoramento ({player.iron_coins}/{cost_coins} Ferros)."

        player.iron_coins -= cost_coins
        target_eq_dict["level"] = current_lvl + 1

        eq_obj = Equipment.from_dict(target_eq_dict)
        eff = eq_obj.get_effective_stats()

        msg = (
            f"⚡ <b>Equipamento Aprimorado!</b>\n\n"
            f"<b>{eq_obj.name}</b> subiu para o <b>Nível +{eq_obj.level}</b>!\n"
            f"⚔️ <b>Atributos Atuais:</b> Atk: {eff['attack']} | Mag: {eff['magic']} | Def: {eff['defense']} | Spd: {eff['speed']}\n"
            f"<i>O efeito das runas acopladas aumentou!</i>"
        )
        return True, msg

    @classmethod
    def socket_rune(cls, player: Player, instance_id: str, rune_id: str) -> Tuple[bool, str]:
        """Engasta uma runa mágica em um slot livre do equipamento."""
        target_eq_dict = None
        for slot, eq_data in player.equipped.items():
            if eq_data and eq_data.get("instance_id") == instance_id:
                target_eq_dict = eq_data
                break

        if not target_eq_dict:
            for eq_data in player.inventory.get("equipment", []):
                if isinstance(eq_data, dict) and eq_data.get("instance_id") == instance_id:
                    target_eq_dict = eq_data
                    break

        if not target_eq_dict:
            return False, "Equipamento não encontrado."

        runes_in_eq = target_eq_dict.setdefault("socketed_runes", [])
        max_slots = target_eq_dict.get("max_rune_slots", 1)

        if len(runes_in_eq) >= max_slots:
            return False, f"Todos os slots de runa deste equipamento estão ocupados ({len(runes_in_eq)}/{max_slots})."

        # Verifica se o jogador tem a runa
        player_runes = player.inventory.get("runes", {})
        if player_runes.get(rune_id, 0) <= 0:
            # Fallback para materiais caso esteja lá
            if player.inventory.get("materials", {}).get(rune_id, 0) > 0:
                player_runes = player.inventory.get("materials", {})
            else:
                return False, "Você não possui esta runa em sua bolsa."

        player_runes[rune_id] -= 1
        if player_runes[rune_id] <= 0:
            del player_runes[rune_id]

        runes_in_eq.append(rune_id)
        rune_item = ItemRepository.get_item(rune_id)
        rune_name = rune_item.name if rune_item else rune_id

        return True, f"✨ Runa [{rune_name}] engastada com sucesso no equipamento ({len(runes_in_eq)}/{max_slots})!"
