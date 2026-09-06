from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from core.message_manager import MessageManager
from core.text_loader import TextLoader
from database.player_repo import PlayerRepository
from systems.energy_system import EnergySystem


async def inn_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Exibe o menu da Estalagem para restauração de energia."""
    chat_id = update.effective_chat.id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    player.regen_energy_passively()

    inn_uses_today = player.get_daily_inn_uses()
    inn_uses_left = max(0, 2 - inn_uses_today)

    text = TextLoader.load(
        "inn_menu.txt",
        current_location=player.current_location,
        character_name=player.character_name,
        hp=player.hp,
        max_hp=player.max_hp,
        mana=player.mana,
        max_mana=player.max_mana,
        energy=player.energy,
        max_energy=player.max_energy,
        iron_coins=player.iron_coins,
        diamonds=player.diamonds,
        inn_uses_left=inn_uses_left,
    )

    keyboard = [
        [
            InlineKeyboardButton(f"🛏️ Quarto Simples (20 Ferros) - +50 ⚡", callback_data="inn_rest_simple"),
        ],
        [
            InlineKeyboardButton(f"👑 Suíte Nobre (50 Ferros) - 100% ⚡", callback_data="inn_rest_luxury"),
        ],
        [
            InlineKeyboardButton(f"⚡ Elixir Divino (10 💎) - 100% ⚡", callback_data="inn_rest_diamonds"),
        ],
        [
            InlineKeyboardButton("⬅️ Voltar ao Hub", callback_data="hub_main"),
            InlineKeyboardButton("🏰 Menu Principal", callback_data="hub_main"),
        ]
    ]

    await MessageManager.send_or_edit(
        update=update,
        context=context,
        image_path="estalagem_descanso.jpg",
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def inn_rest_simple_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    success, msg = EnergySystem.rest_inn_simple(player)
    if success:
        await PlayerRepository.save_player(player)

    await update.callback_query.answer(msg, show_alert=True)
    await inn_main(update, context)


async def inn_rest_luxury_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    success, msg = EnergySystem.rest_inn_luxury(player)
    if success:
        await PlayerRepository.save_player(player)

    await update.callback_query.answer(msg, show_alert=True)
    await inn_main(update, context)


async def inn_rest_diamonds_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    success, msg = EnergySystem.recharge_with_diamonds(player)
    if success:
        await PlayerRepository.save_player(player)

    await update.callback_query.answer(msg, show_alert=True)
    await inn_main(update, context)
