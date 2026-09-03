from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from core.message_manager import MessageManager
from core.text_loader import TextLoader
from database.player_repo import PlayerRepository
from database.item_repo import ItemRepository
from models.item import Equipment
from systems.inventory_system import InventorySystem


async def inventory_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menu da mochila (consumíveis, materiais de monstros, runas e baús)."""
    chat_id = update.effective_chat.id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    # Consumíveis com nome canônico formatado
    consumables_list = []
    for item_id, qty in player.inventory.get("consumables", {}).items():
        item = ItemRepository.get_item(item_id)
        name = item.name if item else item_id.replace("_", " ").title()
        consumables_list.append(f"🧪 <b>{name}</b> x{qty}")

    # Materiais com nome canônico formatado
    materials_list = []
    for item_id, qty in player.inventory.get("materials", {}).items():
        if not item_id.startswith("rune_"):
            item = ItemRepository.get_item(item_id)
            name = item.name if item else item_id.replace("_", " ").title()
            materials_list.append(f"📦 <b>{name}</b> x{qty}")

    # Runas Mágicas
    runes_list = []
    for item_id, qty in player.inventory.get("runes", {}).items():
        item = ItemRepository.get_item(item_id)
        name = item.name if item else item_id.replace("_", " ").title()
        runes_list.append(f"🔮 <b>{name}</b> x{qty}")

    # Fallback caso haja runas na chave de materiais
    for item_id, qty in player.inventory.get("materials", {}).items():
        if item_id.startswith("rune_"):
            item = ItemRepository.get_item(item_id)
            name = item.name if item else item_id.replace("_", " ").title()
            runes_list.append(f"🔮 <b>{name}</b> x{qty}")

    text = TextLoader.load(
        "inventory.txt",
        character_name=player.character_name,
        iron_coins=player.iron_coins,
        diamonds=player.diamonds,
        consumables_list="\n".join(consumables_list) if consumables_list else "<i>Nenhum consumível na bolsa.</i>",
        materials_list="\n".join(materials_list) if materials_list else "<i>Nenhum material coletado.</i>",
        runes_list="\n".join(runes_list) if runes_list else "<i>Nenhuma runa mágica na bolsa.</i>",
        lootbox_hunt_count=player.hunt_lootbox_count,
    )

    keyboard = []

    # Botões rápidos para uso de poção se existirem
    row_actions = []
    if "potion_hp_minor" in player.inventory.get("consumables", {}):
        row_actions.append(InlineKeyboardButton("❤️ Usar Poção HP", callback_data="use_item_potion_hp_minor"))
    if "potion_mana_minor" in player.inventory.get("consumables", {}):
        row_actions.append(InlineKeyboardButton("💧 Usar Poção Mana", callback_data="use_item_potion_mana_minor"))
    if row_actions:
        keyboard.append(row_actions)

    keyboard.append([
        InlineKeyboardButton("⚔️ Ver Equipamentos", callback_data="equipments_menu"),
        InlineKeyboardButton("🔨 Forja & Upgrades", callback_data="crafting_main"),
    ])
    keyboard.append([
        InlineKeyboardButton("🏛️ Mercado da Guilda", callback_data="market_main"),
        InlineKeyboardButton("⬅️ Voltar ao Perfil", callback_data="profile"),
    ])
    keyboard.append([
        InlineKeyboardButton("🏰 Menu Principal", callback_data="hub_main"),
    ])

    await MessageManager.send_or_edit(
        update=update,
        context=context,
        image_path="inventario_bolsa.png",
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def equipments_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Submenu dedicado para equipamentos ativos e armaduras na bolsa."""
    chat_id = update.effective_chat.id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    equipped_weapon = player.equipped.get("weapon")
    equipped_staff = player.equipped.get("staff")
    equipped_armor = player.equipped.get("armor")
    equipped_acc = player.equipped.get("accessory")

    weapon_str = Equipment.from_dict(equipped_weapon).get_full_display_name() if equipped_weapon else "Nenhuma (Punhos)"
    staff_str = Equipment.from_dict(equipped_staff).get_full_display_name() if equipped_staff else "Nenhum"
    armor_str = Equipment.from_dict(equipped_armor).get_full_display_name() if equipped_armor else "Nenhuma"
    accessory_str = Equipment.from_dict(equipped_acc).get_full_display_name() if equipped_acc else "Nenhum"

    bag_eq_list = []
    keyboard = []

    for eq_data in player.inventory.get("equipment", []):
        if isinstance(eq_data, dict):
            eq_obj = Equipment.from_dict(eq_data)
            eff = eq_obj.get_effective_stats()
            bag_eq_list.append(f"🔹 <b>{eq_obj.get_full_display_name()}</b> ({eq_obj.slot.capitalize()})\n   Atk: +{eff['attack']} | Mag: +{eff['magic']} | Def: +{eff['defense']} | Spd: +{eff['speed']}")
            keyboard.append([InlineKeyboardButton(f"Equipar {eq_obj.name[:16]}", callback_data=f"equip_item_{eq_obj.instance_id}")])
        elif isinstance(eq_data, str):
            eq_item = ItemRepository.get_equipment(eq_data)
            if eq_item:
                bag_eq_list.append(f"🔹 <b>{eq_item.name}</b> ({eq_item.slot.capitalize()})")
                keyboard.append([InlineKeyboardButton(f"Equipar {eq_item.name[:16]}", callback_data=f"equip_item_{eq_data}")])

    keyboard.append([
        InlineKeyboardButton("⚡ Forja & Aprimoramento", callback_data="crafting_main"),
        InlineKeyboardButton("🎒 Voltar à Mochila", callback_data="inventory_menu"),
    ])
    keyboard.append([
        InlineKeyboardButton("👤 Meu Cartão", callback_data="profile"),
        InlineKeyboardButton("🏰 Hub Principal", callback_data="hub_main"),
    ])

    text = TextLoader.load(
        "equipments.txt",
        character_name=player.character_name,
        weapon_str=weapon_str,
        staff_str=staff_str,
        armor_str=armor_str,
        accessory_str=accessory_str,
        bag_equipments_list="\n\n".join(bag_eq_list) if bag_eq_list else "<i>Nenhum outro equipamento na bolsa.</i>",
    )

    await MessageManager.send_or_edit(
        update=update,
        context=context,
        image_path="equipamentos_armas.png",
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def equip_item_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Executa a troca/equipagem de um item."""
    query = update.callback_query
    equip_identifier = query.data.replace("equip_item_", "")

    chat_id = update.effective_chat.id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    # Procura o equipamento correspondente no inventário (por instance_id ou id)
    target_eq_dict = None
    for eq_data in player.inventory.get("equipment", []):
        if isinstance(eq_data, dict):
            if eq_data.get("instance_id") == equip_identifier or eq_data.get("id") == equip_identifier:
                target_eq_dict = eq_data
                break
        elif isinstance(eq_data, str) and eq_data == equip_identifier:
            eq_obj = ItemRepository.get_equipment(eq_data)
            if eq_obj:
                target_eq_dict = eq_obj.to_dict()
                break

    if not target_eq_dict:
        await query.answer("Equipamento não encontrado.", show_alert=True)
        return

    slot = target_eq_dict.get("slot", "weapon")
    current_eq = player.equipped.get(slot)
    if current_eq:
        player.inventory.setdefault("equipment", []).append(current_eq)

    player.equipped[slot] = target_eq_dict
    if target_eq_dict in player.inventory.get("equipment", []):
        player.inventory["equipment"].remove(target_eq_dict)
    elif equip_identifier in player.inventory.get("equipment", []):
        player.inventory["equipment"].remove(equip_identifier)

    await PlayerRepository.save_player(player)
    await query.answer(f"Você equipou [{target_eq_dict.get('name')}] no slot [{slot}]!", show_alert=True)
    await equipments_menu(update, context)


async def use_item_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Executa o uso do consumível selecionado."""
    query = update.callback_query
    item_id = query.data.replace("use_item_", "")

    chat_id = update.effective_chat.id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    success, msg = InventorySystem.use_consumable(player, item_id)
    if success:
        await PlayerRepository.save_player(player)

    await query.answer(msg.replace("<b>", "").replace("</b>", ""), show_alert=True)
    await inventory_menu(update, context)
