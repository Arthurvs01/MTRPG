from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from core.message_manager import MessageManager
from core.text_loader import TextLoader
from core.json_loader import JsonLoader
from database.player_repo import PlayerRepository


async def travel_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Exibe o menu de viagem com todas as regiões desbloqueadas e bloqueadas."""
    chat_id = update.effective_chat.id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    player.regen_energy_passively()

    regions_data = JsonLoader.load("regions.json")
    regions = regions_data.get("regions", [])

    regions_lines = []
    keyboard = []

    for region in regions:
        is_unlocked = region["id"] in player.unlocked_regions
        is_current = player.current_region == region["id"]
        level_req = region["unlock_level"]
        diff = region["difficulty"]

        if is_current:
            status = "📍 <b>ATUAL</b>"
            button_text = f"📍 {region['name']} (ATUAL)"
            callback = "travel_current"
        elif is_unlocked:
            status = f"✅ <b>DESBLOQUEADA</b> (Lvl {level_req} - Rank {diff})"
            button_text = f"✈️ Viajar para {region['name']}"
            callback = f"travel_{region['id']}"
        else:
            status = f"🔒 <b>BLOQUEADA</b> (Lvl {level_req} - Rank {diff})"
            button_text = f"🔒 {region['name']} (Lvl {level_req})"
            callback = f"travel_locked_{region['id']}"

        regions_lines.append(f"• {region['name']}\n  {status}")

        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback)])

    keyboard.append([InlineKeyboardButton("⬅️ Voltar ao Hub", callback_data="hub_main")])
    keyboard.append([InlineKeyboardButton("🏰 Menu Principal", callback_data="hub_main")])

    text = TextLoader.load(
        "travel_menu.txt",
        character_name=player.character_name,
        current_location=player.current_location,
        level=player.level,
        adventurer_rank=player.adventurer_rank,
        energy=player.energy,
        max_energy=player.max_energy,
        regions_list="\n\n".join(regions_lines),
    )

    await MessageManager.send_or_edit(
        update=update,
        context=context,
        image_path="mapa_mundi.jpg",
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def travel_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa a viagem para uma nova região."""
    query = update.callback_query
    chat_id = query.message.chat_id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    data = query.data
    if data == "travel_current":
        await query.answer("Você já está nesta região!", show_alert=True)
        return

    if data.startswith("travel_locked_"):
        region_id = data.replace("travel_locked_", "")
        regions_data = JsonLoader.load("regions.json")
        regions = regions_data.get("regions", [])
        region = next((r for r in regions if r["id"] == region_id), None)
        if region:
            await query.answer(f"🔒 {region['name']} está bloqueada! Nível {region['unlock_level']} necessário.", show_alert=True)
        return

    if data.startswith("travel_"):
        region_id = data.replace("travel_", "")
        regions_data = JsonLoader.load("regions.json")
        regions = regions_data.get("regions", [])

        success, msg = player.travel_to(region_id, regions)
        if success:
            await PlayerRepository.save_player(player)
            await query.answer(msg, show_alert=True)
            await travel_menu(update, context)
        else:
            await query.answer(msg, show_alert=True)