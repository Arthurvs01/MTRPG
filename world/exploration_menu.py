import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from core.message_manager import MessageManager
from core.text_loader import TextLoader
from core.json_loader import JsonLoader
from database.player_repo import PlayerRepository
from systems.combat_system import CombatSystem
from systems.progression_system import ProgressionSystem
from systems.quest_system import QuestSystem
from systems.energy_system import EnergySystem


async def explore_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menu principal de exploração e caçada na região atual."""
    chat_id = update.effective_chat.id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    player.regen_energy_passively()

    regions_data = JsonLoader.load("regions.json")
    regions = regions_data.get("regions", [])
    current_region = next((r for r in regions if r["id"] == player.current_region), None)

    if not current_region:
        current_region = regions[0] if regions else None

    if not current_region:
        await MessageManager.send_or_edit(
            update=update,
            context=context,
            image_path="exploracao_floresta.jpg",
            text="Erro: Nenhuma região encontrada.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Hub", callback_data="hub_main")]])
        )
        return

    monsters = current_region.get("monsters", [])
    monster_names = ", ".join([m.replace("_", " ").title() for m in monsters[:3]]) + ("..." if len(monsters) > 3 else "")

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
        region_name=current_region["name"],
        region_difficulty=current_region["difficulty"],
        region_level=current_region["recommended_level"],
        monster_list=monster_names,
    )

    keyboard = [
        [
            InlineKeyboardButton(f"⚔️ Caçar em {current_region['name']} (15 ⚡)", callback_data="hunt_current"),
        ],
        [
            InlineKeyboardButton("🗺️ Mapa & Viagens", callback_data="travel_menu"),
            InlineKeyboardButton("🏨 Estalagem", callback_data="inn_main"),
        ],
        [
            InlineKeyboardButton("🏛️ Guilda de Aventureiros", callback_data="guild_main"),
            InlineKeyboardButton("🏰 Hub Principal", callback_data="hub_main"),
        ],
        [
            InlineKeyboardButton("⬅️ Voltar", callback_data="hub_main"),
        ]
    ]

    await MessageManager.send_or_edit(
        update=update,
        context=context,
        image_path="exploracao_floresta.jpg",
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def hunt_current(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Realiza uma caçada na região atual do jogador."""
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

    regions_data = JsonLoader.load("regions.json")
    regions = regions_data.get("regions", [])
    current_region = next((r for r in regions if r["id"] == player.current_region), None)

    if not current_region:
        await update.callback_query.answer("Erro: Região atual não encontrada.", show_alert=True)
        return

    monsters = current_region.get("monsters", [])
    if not monsters:
        await update.callback_query.answer("Nenhum monstro disponível nesta região.", show_alert=True)
        return

    monster_id = random.choice(monsters)

    EnergySystem.consume(player, EnergySystem.HUNT_ENERGY_COST)

    await _process_hunt(update, context, player, monster_id, current_region["name"], "exploracao_floresta.jpg")


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
        player.hp = int(player.max_hp * 0.5)
        summary_lines.append(
            f"💀 <b>VOCÊ FOI DERROTADO!</b>\n"
            f"Aventureiros da Guilda resgataram você inconsciente e o levaram à Estalagem local."
        )
    else:
        summary_lines.append("⚖️ O combate terminou em empate e ambos recuaram.")

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
            InlineKeyboardButton("⚔️ Caçar Novamente (15 ⚡)", callback_data="hunt_current"),
            InlineKeyboardButton("🗺️ Mapa & Viagens", callback_data="travel_menu"),
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
