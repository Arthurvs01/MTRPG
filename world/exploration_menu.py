import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from core.message_manager import MessageManager
from core.text_loader import TextLoader
from database.player_repo import PlayerRepository
from systems.combat_system import CombatSystem
from systems.progression_system import ProgressionSystem
from systems.quest_system import QuestSystem
from systems.energy_system import EnergySystem


async def explore_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menu principal de exploração e áreas selvagens."""
    chat_id = update.effective_chat.id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    player.regen_energy_passively()

    text = TextLoader.load(
        "explore_menu.txt",
        character_name=player.character_name,
        current_location=player.current_location,
        hp=player.hp,
        max_hp=player.max_hp,
        mana=player.mana,
        max_mana=player.max_mana,
        energy=player.energy,
        max_energy=player.max_energy,
    )

    keyboard = [
        [
            InlineKeyboardButton("🌲 Floresta de Fittoa (15 ⚡ - Rank F/E)", callback_data="hunt_fittoa"),
        ],
        [
            InlineKeyboardButton("🏜️ Terras Ermas de Rikarisu (15 ⚡ - Rank E/C)", callback_data="hunt_rikarisu"),
        ],
        [
            InlineKeyboardButton("🏨 Estalagem & Descanso", callback_data="inn_main"),
            InlineKeyboardButton("🏛️ Guilda de Aventureiros", callback_data="guild_main"),
        ],
        [
            InlineKeyboardButton("🏰 Hub Principal", callback_data="hub_main"),
        ]
    ]

    await MessageManager.send_or_edit(
        update=update,
        context=context,
        image_path="exploracao_floresta.jpg",
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def hunt_region_fittoa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Realiza uma caçada na região florestal de Fittoa."""
    chat_id = update.effective_chat.id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    can_act, err_msg = EnergySystem.can_perform_action(player, EnergySystem.HUNT_ENERGY_COST)
    if not can_act:
        await update.callback_query.answer(err_msg, show_alert=True)
        return

    if player.hp <= 20:
        await update.callback_query.answer("Sua vida está muito baixa! Descanse na Estalagem ou use uma poção antes de lutar.", show_alert=True)
        return

    EnergySystem.consume(player, EnergySystem.HUNT_ENERGY_COST)

    # Sorteio de monstro por probabilidade escalonada
    roll = random.random()
    if roll < 0.35:
        monster_id = "buena_wild_boar"
    elif roll < 0.60:
        monster_id = "horned_wolf"
    elif roll < 0.78:
        monster_id = "pax_monkey"
    elif roll < 0.88:
        monster_id = "freshwater_snake"
    elif roll < 0.95:
        monster_id = "treant_forest"
    else:
        monster_id = "iron_claw_bear"

    await _process_hunt(update, context, player, monster_id, "Floresta de Fittoa", "exploracao_floresta.jpg")


async def hunt_region_rikarisu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Realiza uma caçada no Continente Demônio (Rikarisu)."""
    chat_id = update.effective_chat.id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    can_act, err_msg = EnergySystem.can_perform_action(player, EnergySystem.HUNT_ENERGY_COST)
    if not can_act:
        await update.callback_query.answer(err_msg, show_alert=True)
        return

    if player.hp <= 25:
        await update.callback_query.answer("Sua vida está muito baixa! Cure-se na Estalagem antes de enfrentar as feras demoníacas.", show_alert=True)
        return

    EnergySystem.consume(player, EnergySystem.HUNT_ENERGY_COST)

    roll = random.random()
    if roll < 0.35:
        monster_id = "demon_coyote_rikarisu"
    elif roll < 0.60:
        monster_id = "sand_worm_demon"
    elif roll < 0.78:
        monster_id = "kougumo_spider"
    elif roll < 0.90:
        monster_id = "demon_vulture_roc"
    elif roll < 0.96:
        monster_id = "stone_shell_tortoise"
    else:
        monster_id = "two_headed_wyvern"

    await _process_hunt(update, context, player, monster_id, "Terras de Rikarisu", "exploracao_deserto.jpg")


async def _process_hunt(update: Update, context: ContextTypes.DEFAULT_TYPE, player, monster_id: str, region_name: str, image_name: str):
    """Executa o combate, distribui recompensas, avalia drop de Baú e atualiza missões."""
    enemy = CombatSystem.get_monster(monster_id)
    result = CombatSystem.simulate_battle(player, enemy)

    summary_lines = []

    if result["winner"] == "player":
        xp_logs = ProgressionSystem.add_xp(player, result["xp_reward"])
        player.iron_coins += result["coins_reward"]
        quest_logs = QuestSystem.update_kill_progress(player, monster_id)

        summary_lines.append(
            f"🏆 <b>VITÓRIA GLORIOSA!</b>\n"
            f"💰 <b>Moedas de Ferro:</b> +{result['coins_reward']}\n"
            + "\n".join(xp_logs)
        )

        if result["drops"]:
            drops_str = ", ".join([d["name"] for d in result["drops"]])
            summary_lines.append(f"📦 <b>Despojos:</b> {drops_str}")

        # Chance de drop do Baú Arcano de Caçada (20% de chance)
        if random.random() <= 0.20:
            player.hunt_lootbox_count += 1
            summary_lines.append("🎁 <b>[DROP ESPECIAL]</b> Você encontrou um <b>Baú Arcano de Caçada</b>! (Disponível no menu de Baús)")

        if quest_logs:
            summary_lines.append("\n" + "\n".join(quest_logs))

    elif result["winner"] == "enemy":
        player.deaths += 1
        player.hp = int(player.max_hp * 0.5)  # Revive com metade da vida
        summary_lines.append(
            f"💀 <b>VOCÊ FOI DERROTADO!</b>\n"
            f"Aventureiros da Guilda resgataram você inconsciente e o levaram à Estalagem local."
        )
    else:
        summary_lines.append("⚖️ O combate terminou em empate e ambos recuaram.")

    # Salva o estado atualizado do jogador
    await PlayerRepository.save_player(player)

    text = TextLoader.load(
        "hunt_report.txt",
        region_name=region_name,
        battle_logs="\n".join(result["logs"][-6:]),
        result_summary="\n\n".join(summary_lines),
        energy=player.energy,
        max_energy=player.max_energy,
    )

    keyboard = [
        [
            InlineKeyboardButton("⚔️ Caçar Novamente (15 ⚡)", callback_data=update.callback_query.data),
            InlineKeyboardButton("🗺️ Mudar de Região", callback_data="explore_menu"),
        ],
        [
            InlineKeyboardButton("🏨 Ir à Estalagem", callback_data="inn_main"),
            InlineKeyboardButton("🎁 Ver Baús", callback_data="lootbox_main"),
        ],
        [
            InlineKeyboardButton("🏛️ Guilda", callback_data="guild_main"),
            InlineKeyboardButton("🏰 Hub Principal", callback_data="hub_main"),
        ]
    ]

    await MessageManager.send_or_edit(
        update=update,
        context=context,
        image_path=image_name,
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
