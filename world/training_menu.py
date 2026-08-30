from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from core.message_manager import MessageManager
from core.text_loader import TextLoader
from database.player_repo import PlayerRepository
from systems.training_system import TrainingSystem


async def training_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Exibe o menu de Treinamento no Dojo e Torre de Magia."""
    chat_id = update.effective_chat.id
    player = PlayerRepository.get_player(chat_id)
    if not player:
        return

    player.regen_energy_passively()

    text = TextLoader.load(
        "training_menu.txt",
        character_name=player.character_name,
        energy=player.energy,
        max_energy=player.max_energy,
    )

    keyboard = [
        [
            InlineKeyboardButton("🗡️ Dojo: 1000 Cortes de Madeira", callback_data="train_sword"),
        ],
        [
            InlineKeyboardButton("🪄 Torre: Meditação Elemental", callback_data="train_magic"),
        ],
        [
            InlineKeyboardButton("🥋 Condicionamento de Touki", callback_data="train_touki"),
        ],
        [
            InlineKeyboardButton("⬅️ Voltar ao Hub Principal", callback_data="hub_main"),
        ]
    ]

    await MessageManager.send_or_edit(
        update=update,
        context=context,
        image_path="dojo_treinamento.jpg",
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def train_sword_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    player = PlayerRepository.get_player(chat_id)
    if not player:
        return

    success, msg, logs = TrainingSystem.train_sword_dojo(player)
    if not success:
        await update.callback_query.answer(msg, show_alert=True)
        return

    PlayerRepository.save_player(player)
    await _show_training_result(update, context, player, "Dojo de Espadas", logs)


async def train_magic_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    player = PlayerRepository.get_player(chat_id)
    if not player:
        return

    success, msg, logs = TrainingSystem.train_magic_tower(player)
    if not success:
        await update.callback_query.answer(msg, show_alert=True)
        return

    PlayerRepository.save_player(player)
    await _show_training_result(update, context, player, "Torre de Magia", logs)


async def train_touki_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    player = PlayerRepository.get_player(chat_id)
    if not player:
        return

    success, msg, logs = TrainingSystem.train_touki_conditioning(player)
    if not success:
        await update.callback_query.answer(msg, show_alert=True)
        return

    PlayerRepository.save_player(player)
    await _show_training_result(update, context, player, "Condicionamento Físico", logs)


async def _show_training_result(update: Update, context: ContextTypes.DEFAULT_TYPE, player, title: str, logs: list):
    text = (
        f"🥋 <b>═══ RESULTADO DO TREINAMENTO: {title} ═══</b>\n\n"
        + "\n".join(logs) + "\n\n"
        f"⚡ <b>Energia Restante:</b> {player.energy}/{player.max_energy}\n"
    )

    keyboard = [
        [
            InlineKeyboardButton("🥋 Treinar Novamente", callback_data=update.callback_query.data),
            InlineKeyboardButton("📈 Ver Atributos", callback_data="stat_distribute_menu"),
        ],
        [
            InlineKeyboardButton("⬅️ Voltar ao Dojo", callback_data="training_main"),
            InlineKeyboardButton("🏰 Hub Principal", callback_data="hub_main"),
        ]
    ]

    await MessageManager.send_or_edit(
        update=update,
        context=context,
        image_path="dojo_treinamento.jpg",
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
