from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from core.message_manager import MessageManager
from core.text_loader import TextLoader
from database.player_repo import PlayerRepository
from systems.lootbox_system import LootboxSystem


async def lootbox_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Exibe o Cofre das Relíquias e os Baús disponíveis."""
    chat_id = update.effective_chat.id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    can_daily, daily_status = LootboxSystem.get_daily_status(player)

    text = TextLoader.load(
        "lootbox_menu.txt",
        character_name=player.character_name,
        diamonds=player.diamonds,
        hunt_lootbox_count=player.hunt_lootbox_count,
        daily_status_str=daily_status,
    )

    keyboard = [
        [
            InlineKeyboardButton(f"🎁 Baú Diário ({'PRONTO' if can_daily else 'AGUARDE'})", callback_data="open_box_daily_free"),
        ],
        [
            InlineKeyboardButton(f"🐺 Baú de Caçada ({player.hunt_lootbox_count} Disp.)", callback_data="open_box_hunt_chest"),
        ],
        [
            InlineKeyboardButton("👑 Baú Nobre de Asura (50 💎)", callback_data="open_box_asura_noble"),
        ],
        [
            InlineKeyboardButton("✨ Relíquia das Seis Faces (100 💎)", callback_data="open_box_six_sided_relic"),
        ],
        [
            InlineKeyboardButton("⬅️ Voltar ao Hub Principal", callback_data="hub_main"),
        ]
    ]

    await MessageManager.send_or_edit(
        update=update,
        context=context,
        image_path="bau_lootbox.png",
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def open_box_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa a abertura do baú selecionado."""
    query = update.callback_query
    box_id = query.data.replace("open_box_", "")

    chat_id = update.effective_chat.id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    success, msg, result = LootboxSystem.open_lootbox(player, box_id)
    if not success:
        await query.answer(msg, show_alert=True)
        return

    PlayerRepository.save_player(player)

    result_text = TextLoader.load(
        "lootbox_result.txt",
        box_name=result.get("box_name", "Baú"),
        rewards_body=result.get("rewards_text", ""),
        iron_coins=player.iron_coins,
        diamonds=player.diamonds,
    )

    keyboard = [
        [
            InlineKeyboardButton("🎁 Abrir Outro Baú", callback_data="lootbox_main"),
            InlineKeyboardButton("🎒 Ver na Mochila", callback_data="inventory_menu"),
        ],
        [
            InlineKeyboardButton("⬅️ Voltar ao Hub", callback_data="hub_main"),
        ]
    ]

    await MessageManager.send_or_edit(
        update=update,
        context=context,
        image_path="bau_lootbox.png",
        text=result_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
