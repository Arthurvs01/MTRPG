from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from core.message_manager import MessageManager
from core.text_loader import TextLoader
from database.player_repo import PlayerRepository


async def hub_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Renderiza o Menu Principal / Hub Central despoluído e organizado."""
    chat_id = update.effective_chat.id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    player.regen_energy_passively()

    text = TextLoader.load(
        "hub_menu.txt",
        character_name=player.character_name,
        current_location=player.current_location,
        level=player.level,
        adventurer_rank=player.adventurer_rank,
        hp=player.hp,
        max_hp=player.max_hp,
        mana=player.mana,
        max_mana=player.max_mana,
        energy=player.energy,
        max_energy=player.max_energy,
        iron_coins=player.iron_coins,
        diamonds=player.diamonds,
    )

    keyboard = [
        [
            InlineKeyboardButton("👤 Meu Cartão & Perfil", callback_data="profile"),
            InlineKeyboardButton("🎒 Mochila & Itens", callback_data="inventory_menu"),
        ],
        [
            InlineKeyboardButton("🏛️ Guilda de Aventureiros", callback_data="guild_main"),
            InlineKeyboardButton("🗺️ Expedição & Caçada", callback_data="explore_menu"),
        ],
        [
            InlineKeyboardButton("🔨 Forja & Upgrades", callback_data="crafting_main"),
            InlineKeyboardButton("🤝 Mercado entre Players", callback_data="market_main"),
        ],
        [
            InlineKeyboardButton("🏨 Estalagem & Descanso", callback_data="inn_main"),
            InlineKeyboardButton("🥋 Dojo & Torre de Treino", callback_data="training_main"),
        ],
        [
            InlineKeyboardButton("🎁 Baús & Relíquias", callback_data="lootbox_main"),
            InlineKeyboardButton("🗺️ Mapa & Viagens", callback_data="travel_menu"),
        ],
        [
            InlineKeyboardButton("🏰 Dungeons", callback_data="dungeon_main"),
            InlineKeyboardButton("🤝 Grupo de Aventureiros", callback_data="party_main"),
        ]
    ]

    await MessageManager.send_or_edit(
        update=update,
        context=context,
        image_path="menu_principal_hub.png",
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
