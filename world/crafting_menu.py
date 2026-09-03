from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from core.message_manager import MessageManager
from core.text_loader import TextLoader
from database.player_repo import PlayerRepository
from database.item_repo import ItemRepository
from models.item import Equipment
from systems.crafting_system import CraftingSystem


CATEGORY_NAMES = {
    "weapon": "🗡️ Armas & Lâminas",
    "staff": "🪄 Cajados Mágicos",
    "armor": "🛡️ Armaduras & Túnicas",
    "accessory": "💍 Acessórios & Amuletos",
}


async def crafting_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Exibe o menu principal de Forja organizado por categorias."""
    chat_id = update.effective_chat.id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    keyboard = [
        [
            InlineKeyboardButton("🗡️ Armas & Lâminas", callback_data="craft_cat_weapon"),
            InlineKeyboardButton("🪄 Cajados Mágicos", callback_data="craft_cat_staff"),
        ],
        [
            InlineKeyboardButton("🛡️ Armaduras & Túnicas", callback_data="craft_cat_armor"),
            InlineKeyboardButton("💍 Acessórios & Amuletos", callback_data="craft_cat_accessory"),
        ],
        [
            InlineKeyboardButton("⚡ Aprimoramento & Runas", callback_data="upgrade_menu"),
            InlineKeyboardButton("🤝 Mercado da Guilda", callback_data="market_main"),
        ],
        [
            InlineKeyboardButton("⬅️ Voltar à Guilda", callback_data="guild_main"),
            InlineKeyboardButton("🏰 Menu Principal", callback_data="hub_main"),
        ]
    ]

    text = TextLoader.load(
        "crafting_main.txt",
        character_name=player.character_name,
        iron_coins=player.iron_coins,
    )

    await MessageManager.send_or_edit(
        update=update,
        context=context,
        image_path="dojo_treinamento.jpg",
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def crafting_category_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Exibe as receitas de uma categoria específica (weapon, staff, armor, accessory)."""
    query = update.callback_query
    category = query.data.replace("craft_cat_", "")

    chat_id = update.effective_chat.id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    recipes = CraftingSystem.get_recipes()
    recipes_lines = []
    keyboard = []

    player_materials = player.inventory.get("materials", {})

    for rec_id, rec_data in recipes.items():
        if rec_data.get("slot") == category:
            name = rec_data.get("name", "Equipamento")
            cost = rec_data.get("iron_coins_cost", 30)
            req_mats = rec_data.get("required_materials", {})

            req_str_list = []
            can_craft = player.iron_coins >= cost

            for mat_id, qty in req_mats.items():
                mat_item = ItemRepository.get_item(mat_id)
                mat_name = mat_item.name if mat_item else mat_id
                have_qty = player_materials.get(mat_id, 0)
                if have_qty < qty:
                    can_craft = False
                req_str_list.append(f"{mat_name} ({have_qty}/{qty})")

            mats_text = ", ".join(req_str_list)
            status_icon = "✅" if can_craft else "🔒"

            recipes_lines.append(
                f"{status_icon} <b>{name}</b>\n"
                f"   📦 Materiais: {mats_text}\n"
                f"   💰 Custo: {cost} Moedas de Ferro"
            )

            btn_text = f"🔨 Forjar {name[:18]}" if can_craft else f"🔒 {name[:18]}"
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"craft_exec_{rec_id}")])

    keyboard.append([
        InlineKeyboardButton("⬅️ Voltar às Categorias", callback_data="crafting_main"),
        InlineKeyboardButton("🏰 Hub Principal", callback_data="hub_main"),
    ])

    cat_title = CATEGORY_NAMES.get(category, "Equipamentos")
    text = TextLoader.load(
        "crafting_category.txt",
        category_name=cat_title,
        character_name=player.character_name,
        iron_coins=player.iron_coins,
        recipes_list="\n\n".join(recipes_lines) if recipes_lines else "<i>Nenhuma receita cadastrada nesta categoria.</i>",
    )

    await MessageManager.send_or_edit(
        update=update,
        context=context,
        image_path="dojo_treinamento.jpg",
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def craft_exec_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Executa a forja da receita selecionada."""
    query = update.callback_query
    recipe_id = query.data.replace("craft_exec_", "")

    chat_id = update.effective_chat.id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    success, msg, crafted_eq = CraftingSystem.craft_item(player, recipe_id)
    if not success:
        await query.answer(msg, show_alert=True)
        return

    await PlayerRepository.save_player(player)

    keyboard = [
        [
            InlineKeyboardButton("🔨 Forjar Mais Itens", callback_data="crafting_main"),
            InlineKeyboardButton("⚡ Ir Aprimorar", callback_data="upgrade_menu"),
        ],
        [
            InlineKeyboardButton("🎒 Ver na Mochila", callback_data="inventory_menu"),
            InlineKeyboardButton("🏰 Hub Principal", callback_data="hub_main"),
        ]
    ]

    await MessageManager.send_or_edit(
        update=update,
        context=context,
        image_path="equipamentos_armas.png",
        text=msg,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def upgrade_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menu para seleção de equipamentos e aprimoramento de nível / runas."""
    chat_id = update.effective_chat.id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    # Lista de equipamentos disponíveis (equipados e na bolsa)
    equipments_list = []
    for slot, eq_data in player.equipped.items():
        if eq_data:
            eq_obj = Equipment.from_dict(eq_data)
            equipments_list.append((eq_obj, f"[Equipado no {slot.capitalize()}]"))

    for eq_data in player.inventory.get("equipment", []):
        if isinstance(eq_data, dict):
            eq_obj = Equipment.from_dict(eq_data)
            equipments_list.append((eq_obj, "[Na Mochila]"))

    keyboard = []
    eq_info_lines = []

    for eq_obj, loc in equipments_list:
        eff = eq_obj.get_effective_stats()
        eq_info_lines.append(
            f"🔹 <b>{eq_obj.get_full_display_name()}</b> {loc}\n"
            f"   Atk: +{eff['attack']} | Mag: +{eff['magic']} | Def: +{eff['defense']} | Spd: +{eff['speed']}"
        )
        keyboard.append([
            InlineKeyboardButton(f"⚡ Subir Nível: {eq_obj.name[:16]} (+{eq_obj.level+1})", callback_data=f"up_lvl_{eq_obj.instance_id}"),
            InlineKeyboardButton(f"🔮 Runa ({len(eq_obj.socketed_runes)}/{eq_obj.max_rune_slots})", callback_data=f"up_rune_{eq_obj.instance_id}"),
        ])

    # Lista de runas do jogador
    runes_list = []
    for r_id, qty in player.inventory.get("runes", {}).items():
        r_item = ItemRepository.get_item(r_id)
        name = r_item.name if r_item else r_id
        runes_list.append(f"🔮 {name} x{qty}")

    # Fallback para materiais
    for r_id, qty in player.inventory.get("materials", {}).items():
        if r_id.startswith("rune_"):
            r_item = ItemRepository.get_item(r_id)
            name = r_item.name if r_item else r_id
            runes_list.append(f"🔮 {name} x{qty}")

    keyboard.append([
        InlineKeyboardButton("🔨 Voltar à Forja", callback_data="crafting_main"),
        InlineKeyboardButton("🏰 Hub Principal", callback_data="hub_main"),
    ])

    text = TextLoader.load(
        "upgrade_menu.txt",
        character_name=player.character_name,
        iron_coins=player.iron_coins,
        selected_equipment_info="\n\n".join(eq_info_lines) if eq_info_lines else "<i>Nenhum equipamento encontrado.</i>",
        available_runes_body="\n".join(runes_list) if runes_list else "<i>Nenhuma runa mágica na bolsa.</i>",
    )

    await MessageManager.send_or_edit(
        update=update,
        context=context,
        image_path="equipamentos_armas.png",
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def upgrade_level_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Executa a subida de nível do equipamento."""
    query = update.callback_query
    instance_id = query.data.replace("up_lvl_", "")

    chat_id = update.effective_chat.id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    success, msg = CraftingSystem.upgrade_equipment(player, instance_id)
    if not success:
        await query.answer(msg, show_alert=True)
        return

    await PlayerRepository.save_player(player)
    await query.answer("Aprimoramento realizado com sucesso!", show_alert=True)
    await upgrade_menu(update, context)


async def select_rune_for_socket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menu para selecionar qual runa da bolsa engastar no equipamento escolhido."""
    query = update.callback_query
    instance_id = query.data.replace("up_rune_", "")

    chat_id = update.effective_chat.id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    available_runes = []
    for r_id, qty in player.inventory.get("runes", {}).items():
        if qty > 0:
            available_runes.append(r_id)

    for r_id, qty in player.inventory.get("materials", {}).items():
        if r_id.startswith("rune_") and qty > 0 and r_id not in available_runes:
            available_runes.append(r_id)

    if not available_runes:
        await query.answer("Você não possui nenhuma runa mágica na bolsa.", show_alert=True)
        return

    keyboard = []
    for r_id in available_runes:
        r_item = ItemRepository.get_item(r_id)
        name = r_item.name if r_item else r_id
        keyboard.append([
            InlineKeyboardButton(f"🔮 Engastar {name}", callback_data=f"sock_{instance_id}_{r_id}")
        ])

    keyboard.append([
        InlineKeyboardButton("⬅️ Voltar aos Equipamentos", callback_data="upgrade_menu"),
        InlineKeyboardButton("🏰 Menu Principal", callback_data="hub_main"),
    ])

    text = (
        f"🔮 <b>═══ ENGASTE DE RUNA MÁGICA ═══</b>\n\n"
        f"Selecione uma runa de sua bolsa para engastar no equipamento selecionado:\n"
    )

    await MessageManager.send_or_edit(
        update=update,
        context=context,
        image_path="equipamentos_armas.png",
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def socket_rune_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa o engaste da runa selecionada."""
    query = update.callback_query
    parts = query.data.split("_", 2)
    if len(parts) < 3:
        return

    instance_id = parts[1]
    rune_id = parts[2]

    chat_id = update.effective_chat.id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    success, msg = CraftingSystem.socket_rune(player, instance_id, rune_id)
    if not success:
        await query.answer(msg, show_alert=True)
        return

    await PlayerRepository.save_player(player)
    await query.answer("Runa acoplada com sucesso!", show_alert=True)
    await upgrade_menu(update, context)
