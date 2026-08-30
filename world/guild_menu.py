from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from core.message_manager import MessageManager
from core.text_loader import TextLoader
from database.player_repo import PlayerRepository
from database.quest_repo import QuestRepository
from systems.quest_system import QuestSystem


async def guild_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hub Central da Guilda de Aventureiros."""
    chat_id = update.effective_chat.id
    player = PlayerRepository.get_player(chat_id)
    if not player:
        return

    player.regen_energy_passively()

    text = TextLoader.load(
        "guild_main.txt",
        character_name=player.character_name,
        adventurer_rank=player.adventurer_rank,
        guild_points=player.guild_points,
        energy=player.energy,
        max_energy=player.max_energy,
        iron_coins=player.iron_coins,
        diamonds=player.diamonds,
    )

    keyboard = [
        [
            InlineKeyboardButton("📜 Quadro de Missões", callback_data="guild_quests_board"),
            InlineKeyboardButton("✅ Contratos Ativos", callback_data="guild_active_quests"),
        ],
        [
            InlineKeyboardButton("🏛️ Mercado entre Players", callback_data="market_main"),
            InlineKeyboardButton("🔨 Forja & Oficina Mágica", callback_data="crafting_main"),
        ],
        [
            InlineKeyboardButton("🗺️ Sair para Caçar", callback_data="explore_menu"),
            InlineKeyboardButton("🏰 Hub Principal", callback_data="hub_main"),
        ]
    ]

    await MessageManager.send_or_edit(
        update=update,
        context=context,
        image_path="guilda_aventureiros.png",
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def guild_quests_board(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Exibe as missões disponíveis para o Rank do jogador."""
    chat_id = update.effective_chat.id
    player = PlayerRepository.get_player(chat_id)
    if not player:
        return

    quests = QuestRepository.get_available_quests(player.adventurer_rank)

    quests_body_list = []
    keyboard = []
    for q in quests:
        quests_body_list.append(
            f"🔸 <b>[{q.rank}] {q.title}</b>\n"
            f"   📝 {q.description}\n"
            f"   💰 Recompensa: {q.reward_iron_coins} Ferros | 🎖️ +{q.reward_guild_points} pts"
        )
        keyboard.append([
            InlineKeyboardButton(f"Aceitar [{q.rank}] {q.title[:20]}...", callback_data=f"accept_quest_{q.id}")
        ])

    text = TextLoader.load(
        "guild_quests.txt",
        adventurer_rank=player.adventurer_rank,
        quests_body="\n\n".join(quests_body_list) if quests_body_list else "<i>Nenhum contrato disponível para seu rank no momento.</i>",
    )

    keyboard.append([
        InlineKeyboardButton("⬅️ Voltar à Guilda", callback_data="guild_main")
    ])

    await MessageManager.send_or_edit(
        update=update,
        context=context,
        image_path="quadro_missoes.png",
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def accept_quest_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Aceita o contrato selecionado."""
    query = update.callback_query
    quest_id = query.data.replace("accept_quest_", "")

    chat_id = update.effective_chat.id
    player = PlayerRepository.get_player(chat_id)
    if not player:
        return

    success, msg = QuestSystem.accept_quest(player, quest_id)
    if success:
        PlayerRepository.save_player(player)

    await query.answer(msg, show_alert=True)
    await guild_active_quests(update, context)


async def guild_active_quests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lista as missões atualmente aceitas pelo jogador."""
    chat_id = update.effective_chat.id
    player = PlayerRepository.get_player(chat_id)
    if not player:
        return

    keyboard = []
    if not player.active_quests:
        active_body = "<i>Você não possui nenhum contrato ativo no momento.</i>"
        keyboard.append([InlineKeyboardButton("📜 Ver Quadro de Missões", callback_data="guild_quests_board")])
    else:
        body_parts = []
        for q in player.active_quests:
            status_tag = "✅ PRONTA PARA ENTREGA" if q.get("completed") else f"⏳ Progresso: {q.get('current_count', 0)}/{q.get('required_count', 1)}"
            body_parts.append(f"🔸 <b>{q['title']}</b>\n   Status: {status_tag}")
            if q.get("completed"):
                keyboard.append([
                    InlineKeyboardButton(f"🎁 Resgatar: {q['title'][:20]}...", callback_data=f"claim_quest_{q['id']}")
                ])
        active_body = "\n\n".join(body_parts)
        keyboard.append([InlineKeyboardButton("📜 Pegar Mais Missões", callback_data="guild_quests_board")])

    keyboard.append([InlineKeyboardButton("⬅️ Voltar à Guilda", callback_data="guild_main")])

    text = TextLoader.load(
        "guild_active_quests.txt",
        character_name=player.character_name,
        active_quests_body=active_body,
    )

    await MessageManager.send_or_edit(
        update=update,
        context=context,
        image_path="quadro_missoes.png",
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def claim_quest_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Resgata a recompensa da missão concluída."""
    query = update.callback_query
    quest_id = query.data.replace("claim_quest_", "")

    chat_id = update.effective_chat.id
    player = PlayerRepository.get_player(chat_id)
    if not player:
        return

    success, msg = QuestSystem.claim_rewards(player, quest_id)
    if success:
        PlayerRepository.save_player(player)

    await query.answer("Recompensa resgatada com sucesso!", show_alert=True)
    await guild_active_quests(update, context)
