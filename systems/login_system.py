import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler
from core.message_manager import MessageManager
from core.text_loader import TextLoader
from core.json_loader import JsonLoader
from database.player_repo import PlayerRepository
from models.player import Player
from world.hub_menu import hub_main_menu

logger = logging.getLogger(__name__)

# Estados da Conversação de Registro
ASK_NAME, CHOOSE_RACE, CHOOSE_VOCATION = range(3)


async def start_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ponto de entrada do comando /start."""
    chat_id = update.effective_chat.id

    if PlayerRepository.player_exists(chat_id):
        # Jogador já registrado, direciona para o hub principal
        return await hub_main_menu(update, context)

    text = TextLoader.load("welcome.txt")

    await MessageManager.send_or_edit(
        update=update,
        context=context,
        image_path="reencarnacao_boas_vindas.jpg",
        text=text,
        reply_markup=None
    )
    context.user_data["awaiting_name"] = True
    return ASK_NAME


async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recebe o nome do personagem e abre a seleção de raça."""
    name = update.message.text.strip()
    if len(name) < 2 or len(name) > 24:
        await update.message.reply_text("Por favor, escolha um nome entre 2 e 24 caracteres:")
        return ASK_NAME

    context.user_data["temp_char_name"] = name
    context.user_data["awaiting_name"] = False

    data = JsonLoader.load("classes_races.json")
    races = data.get("races", {})

    races_lines = []
    keyboard = []
    for r_key, r_info in races.items():
        races_lines.append(f"🔹 <b>{r_info['name']}</b>: {r_info['description']}")
        keyboard.append([InlineKeyboardButton(f"🧬 Escolher {r_info['name']}", callback_data=f"race_{r_key}")])

    text = TextLoader.load(
        "choose_race.txt",
        character_name=name,
        races_description="\n\n".join(races_lines),
    )

    await MessageManager.send_or_edit(
        update=update,
        context=context,
        image_path="reencarnacao_boas_vindas.jpg",
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CHOOSE_RACE


async def select_race_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa a escolha de raça e exibe a seleção de vocação."""
    query = update.callback_query
    race_key = query.data.replace("race_", "")
    context.user_data["temp_race"] = race_key

    data = JsonLoader.load("classes_races.json")
    vocations = data.get("vocations", {})

    vocations_lines = []
    keyboard = []
    for v_key, v_info in vocations.items():
        vocations_lines.append(f"🔸 <b>{v_info['name']}</b>\n   {v_info['description']}")
        keyboard.append([InlineKeyboardButton(f"🗡️ {v_info['name']}", callback_data=f"vocation_{v_key}")])

    text = TextLoader.load(
        "choose_vocation.txt",
        vocations_description="\n\n".join(vocations_lines),
    )

    await MessageManager.send_or_edit(
        update=update,
        context=context,
        image_path="perfil_aventureiro.jpg",
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CHOOSE_VOCATION


async def select_vocation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Conclui a criação do aventureiro e salva no banco de dados."""
    query = update.callback_query
    vocation_key = query.data.replace("vocation_", "")

    chat_id = update.effective_chat.id
    name = context.user_data.get("temp_char_name", "Aventureiro")
    race_key = context.user_data.get("temp_race", "humano")

    data = JsonLoader.load("classes_races.json")
    race_info = data.get("races", {}).get(race_key, {})
    vocation_info = data.get("vocations", {}).get(vocation_key, {})

    race_name = race_info.get("name", "Humano")
    vocation_name = vocation_info.get("name", "Espadachim")
    origin = "demon" if "migurd" in race_key or "superd" in race_key else "central"

    # Instancia o novo jogador
    player = Player(
        chat_id=chat_id,
        character_name=name,
        race=race_name,
        vocation=vocation_name,
        origin_continent=origin
    )

    # Aplica bônus de raça e vocação
    player.hp = vocation_info.get("initial_hp", 120) + race_info.get("hp_bonus", 0)
    player.max_hp = player.hp
    player.mana = vocation_info.get("initial_mana", 50) + race_info.get("mana_bonus", 0)
    player.max_mana = player.mana
    player.strength = vocation_info.get("initial_strength", 10) + race_info.get("strength_bonus", 0)
    player.defense = vocation_info.get("initial_defense", 8) + race_info.get("defense_bonus", 0)
    player.speed = vocation_info.get("initial_speed", 10) + race_info.get("speed_bonus", 0)
    player.magic_power = vocation_info.get("initial_magic", 8) + race_info.get("magic_bonus", 0)

    # Habilidades nativas por raça
    if "migurd" in race_key:
        player.magic_schools["Água"] = "Iniciante"
    elif "superd" in race_key:
        player.sword_styles["Deus da Espada"] = "Iniciante"

    # Salva no banco de dados
    await PlayerRepository.save_player(player)

    await query.answer("Registro concluído! Bem-vindo à sua nova vida!", show_alert=True)
    await hub_main_menu(update, context)
