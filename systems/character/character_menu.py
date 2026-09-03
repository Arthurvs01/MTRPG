from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from core.message_manager import MessageManager
from core.text_loader import TextLoader
from database.player_repo import PlayerRepository
from systems.progression_system import ProgressionSystem


async def character_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Renderiza a ficha resumida e cartão de aventureiro do jogador."""
    chat_id = update.effective_chat.id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    player.regen_energy_passively()

    touki_display = f"🛡️ {player.touki}/{player.max_touki}" if player.has_touki_awakened else "Não Despertado"

    text = TextLoader.load(
        "character_profile.txt",
        character_name=player.character_name,
        race=player.race,
        vocation=player.vocation,
        current_location=player.current_location,
        adventurer_rank=player.adventurer_rank,
        guild_points=player.guild_points,
        level=player.level,
        xp=player.xp,
        xp_next_level=player.xp_next_level,
        hp=player.hp,
        max_hp=player.max_hp,
        mana=player.mana,
        max_mana=player.max_mana,
        energy=player.energy,
        max_energy=player.max_energy,
        touki=touki_display,
        total_attack=player.get_total_attack(),
        total_defense=player.get_total_defense(),
        total_speed=player.get_total_speed(),
        total_magic=player.get_total_magic_power(),
        iron_coins=player.iron_coins,
        silver_coins=player.silver_coins,
        gold_coins=player.gold_coins,
        diamonds=player.diamonds,
    )

    keyboard = [
        [
            InlineKeyboardButton(f"📈 Atributos ({player.status_points} pts)", callback_data="stat_distribute_menu"),
            InlineKeyboardButton("🪄 Habilidades & Magias", callback_data="skills_menu"),
        ],
        [
            InlineKeyboardButton("🎒 Mochila / Itens", callback_data="inventory_menu"),
            InlineKeyboardButton("⚔️ Equipamentos", callback_data="equipments_menu"),
        ],
        [
            InlineKeyboardButton("🏰 Menu Principal", callback_data="hub_main"),
        ]
    ]

    await MessageManager.send_or_edit(
        update=update,
        context=context,
        image_path="perfil_aventureiro.jpg",
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def character_skills_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Submenu dedicado para visualização das Habilidades de Espada e Magias."""
    chat_id = update.effective_chat.id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    text = TextLoader.load(
        "character_skills.txt",
        character_name=player.character_name,
        sword_god_rank=player.sword_styles.get("Deus da Espada", "Nenhum"),
        water_god_rank=player.sword_styles.get("Deus da Água", "Nenhum"),
        north_god_rank=player.sword_styles.get("Deus do Norte", "Nenhum"),
        known_sword_skills_str=", ".join(player.known_sword_skills) if player.known_sword_skills else "Nenhuma técnica aprendida",
        fire_rank=player.magic_schools.get("Fogo", "Nenhum"),
        water_rank=player.magic_schools.get("Água", "Nenhum"),
        earth_rank=player.magic_schools.get("Terra", "Nenhum"),
        wind_rank=player.magic_schools.get("Vento", "Nenhum"),
        heal_rank=player.magic_schools.get("Cura", "Nenhum"),
        known_spells_str=", ".join(player.known_spells) if player.known_spells else "Nenhum feitiço aprendido",
        voiceless_str="✨ Despertada (Sem Encantamento)" if player.has_voiceless_casting else "❌ Não Dominada (Com Canto)",
        demon_eye_str=f"👁️ {player.demon_eye}" if player.demon_eye else "Nenhum",
        touki_awakened_str="🔥 Despertado" if player.has_touki_awakened else "❌ Adormecido",
    )

    keyboard = [
        [
            InlineKeyboardButton("🥋 Ir ao Dojo de Treino", callback_data="training_main"),
        ],
        [
            InlineKeyboardButton("⬅️ Voltar ao Cartão", callback_data="profile"),
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


async def stat_distribute_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menu para alocação de pontos de status adquiridos por nível."""
    chat_id = update.effective_chat.id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    text = TextLoader.load(
        "character_stats.txt",
        status_points=player.status_points,
        strength=player.strength,
        defense=player.defense,
        speed=player.speed,
        magic_power=player.magic_power,
        max_hp=player.max_hp,
    )

    keyboard = [
        [
            InlineKeyboardButton("➕ Força", callback_data="add_stat_str"),
            InlineKeyboardButton("➕ Defesa", callback_data="add_stat_def"),
        ],
        [
            InlineKeyboardButton("➕ Agilidade", callback_data="add_stat_spd"),
            InlineKeyboardButton("➕ Poder Mágico", callback_data="add_stat_mag"),
        ],
        [
            InlineKeyboardButton("➕ Vitalidade (HP)", callback_data="add_stat_hp"),
        ],
        [
            InlineKeyboardButton("⬅️ Voltar ao Cartão", callback_data="profile"),
            InlineKeyboardButton("🏰 Menu Principal", callback_data="hub_main"),
        ]
    ]

    await MessageManager.send_or_edit(
        update=update,
        context=context,
        image_path="status_atributos.jpg",
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def add_stat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manipula a adição de ponto no atributo selecionado."""
    query = update.callback_query
    data = query.data
    stat_key = data.replace("add_stat_", "")

    chat_id = update.effective_chat.id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    success, msg = ProgressionSystem.distribute_stat(player, stat_key, 1)
    if success:
        await PlayerRepository.save_player(player)

    await stat_distribute_menu(update, context)
