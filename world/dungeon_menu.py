from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from core.message_manager import MessageManager
from core.text_loader import TextLoader
from core.json_loader import JsonLoader
from database.player_repo import PlayerRepository
from models.player import Player
from systems.dungeon_system import DungeonSystem


async def dungeon_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menu principal de Dungeons."""
    chat_id = update.effective_chat.id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    player.regen_energy_passively()

    regions_data = JsonLoader.load("regions.json")
    regions = regions_data.get("regions", [])
    current_region = next((r for r in regions if r["id"] == player.current_region), None)

    if not current_region or "dungeon" not in current_region:
        text = "❌ Esta região não possui dungeon disponível."
        keyboard = [[InlineKeyboardButton("⬅️ Voltar", callback_data="hub_main")]]
        await MessageManager.send_or_edit(update, context, "dungeon_entrada.jpg", text, InlineKeyboardMarkup(keyboard))
        return

    dungeon_data = current_region["dungeon"]
    dungeon_count = player.get_daily_dungeon_count()

    # Verifica se já está em uma dungeon ativa
    active_dungeon = None
    for d in DungeonSystem._active_dungeons.values():
        if d.get_member(player.chat_id) and not d.is_completed:
            active_dungeon = d
            break

    if active_dungeon:
        await dungeon_active_info(update, context, player, active_dungeon)
        return

    options = []
    keyboard = []

    if dungeon_count >= 3:
        options.append("🚫 Limite diário atingido (3/3)")
    else:
        options.append("✅ Disponível para entrar/criar")
        keyboard.append([InlineKeyboardButton("🏰 Criar Dungeon (Líder)", callback_data="dungeon_create")])
        keyboard.append([InlineKeyboardButton("🔑 Entrar na Dungeon (Senha)", callback_data="dungeon_join")])

    options.append(f"📊 Nível mínimo: {dungeon_data['min_level']}")
    options.append(f"👥 Grupo: 2-4 jogadores")

    keyboard.append([InlineKeyboardButton("⬅️ Voltar ao Hub", callback_data="hub_main")])
    keyboard.append([InlineKeyboardButton("🏰 Menu Principal", callback_data="hub_main")])

    text = TextLoader.load(
        "dungeon_main.txt",
        character_name=player.character_name,
        current_location=player.current_location,
        energy=player.energy,
        max_energy=player.max_energy,
        dungeon_count=dungeon_count,
        region_name=current_region["name"],
        dungeon_name=dungeon_data["name"],
        dungeon_min_level=dungeon_data["min_level"],
        options="\n".join(f"• {o}" for o in options),
    )

    await MessageManager.send_or_edit(
        update=update,
        context=context,
        image_path="dungeon_entrada.jpg",
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def dungeon_active_info(update: Update, context: ContextTypes.DEFAULT_TYPE, player: Player, instance):
    """Exibe informações de uma dungeon ativa."""
    info = DungeonSystem.get_dungeon_info(instance.dungeon_id)
    if not info:
        await dungeon_main(update, context)
        return

    is_leader = player.chat_id == instance.leader_id

    members_text = "\n".join([
        f"• {m['name']} - HP: {m['hp']}/{m['max_hp']} - Dano: {m['damage']}"
        for m in info["members"]
    ])

    text = (
        f"🏰 <b>DUNGEON ATIVA: {instance.dungeon_id.split('_')[0].replace('dungeon_', '').replace('_', ' ').title()}</b>\n\n"
        f"👑 <b>Líder:</b> {info['leader']}\n"
        f"🌊 <b>Onda:</b> {info['current_wave']}/{info['max_waves']}\n"
        f"🔐 <b>Senha:</b> {info['password']}\n\n"
        f"<b>Membros ({len(info['members'])}/4):</b>\n{members_text}\n\n"
    )

    keyboard = []
    if is_leader and not info["is_active"]:
        keyboard.append([InlineKeyboardButton("▶️ Iniciar Dungeon", callback_data=f"dungeon_start_{instance.dungeon_id}")])
        keyboard.append([InlineKeyboardButton("❌ Cancelar Dungeon", callback_data=f"dungeon_cancel_{instance.dungeon_id}")])
    elif info["is_active"]:
        keyboard.append([InlineKeyboardButton("⚔️ Atacar Onda Atual", callback_data=f"dungeon_attack_{instance.dungeon_id}")])
        keyboard.append([InlineKeyboardButton("🧪 Usar Poção", callback_data=f"dungeon_potion_{instance.dungeon_id}")])
    else:
        keyboard.append([InlineKeyboardButton("🚪 Sair da Dungeon", callback_data=f"dungeon_leave_{instance.dungeon_id}")])

    keyboard.append([InlineKeyboardButton("⬅️ Voltar", callback_data="dungeon_main")])

    await MessageManager.send_or_edit(
        update=update,
        context=context,
        image_path="dungeon_interior.jpg",
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def dungeon_create(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia criação de dungeon - pede senha."""
    query = update.callback_query
    chat_id = query.message.chat_id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    if not player.can_enter_dungeon():
        await query.answer("🚫 Limite diário de dungeons atingido!", show_alert=True)
        return

    context.user_data["dungeon_creating"] = True
    await query.answer()
    await query.edit_message_text(
        "🔐 <b>CRIAR DUNGEON</b>\n\n"
        "Digite uma senha de <b>4 dígitos numéricos</b> para sua dungeon:\n"
        "<i>Exemplo: 1234</i>\n\n"
        "Esta senha será necessária para seus amigos entrarem no grupo.",
        parse_mode="HTML"
    )


async def dungeon_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Exibe lista de dungeons disponíveis na região para entrar."""
    query = update.callback_query
    chat_id = query.message.chat_id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    if not player.can_enter_dungeon():
        await query.answer("🚫 Limite diário de dungeons atingido!", show_alert=True)
        return

    # Busca dungeons ativas na região atual que não começaram e têm vaga
    available_dungeons = []
    for instance in DungeonSystem._active_dungeons.values():
        if (not instance.is_active and 
            not instance.is_completed and 
            len(instance.members) < 4 and
            instance.get_member(player.chat_id) is None):
            # Verifica se a dungeon é da região atual do player
            dungeon_region = instance.dungeon_id.split("_")[0] + "_" + instance.dungeon_id.split("_")[1]
            if dungeon_region == player.current_region:
                leader = instance.get_member(instance.leader_id)
                leader_name = leader.character_name if leader else "Desconhecido"
                available_dungeons.append({
                    "dungeon_id": instance.dungeon_id,
                    "leader_name": leader_name,
                    "members": len(instance.members),
                    "password": instance.password,  # Para exibir se for do próprio player
                })

    if not available_dungeons:
        text = (
            "🔑 <b>ENTRAR NA DUNGEON</b>\n\n"
            "Nenhuma dungeon disponível na sua região no momento.\n"
            "Você pode criar uma nova ou aguardar alguém criar."
        )
        keyboard = [[InlineKeyboardButton("⬅️ Voltar", callback_data="dungeon_main")]]
        await MessageManager.send_or_edit(update, context, "dungeon_entrada.jpg", text, InlineKeyboardMarkup(keyboard))
        return

    text = "🔑 <b>DUNGEONS DISPONÍVEIS NA REGIÃO</b>\n\nSelecione uma dungeon para entrar (apenas a senha será necessária):\n"
    keyboard = []

    for d in available_dungeons:
        text += f"\n• <b>{d['dungeon_id']}</b>\n  Líder: {d['leader_name']} | Jogadores: {d['members']}/4"
        keyboard.append([
            InlineKeyboardButton(f"🔑 Entrar: {d['leader_name']} ({d['members']}/4)", callback_data=f"dungeon_join_select_{d['dungeon_id']}")
        ])

    keyboard.append([InlineKeyboardButton("⬅️ Voltar", callback_data="dungeon_main")])

    await MessageManager.send_or_edit(
        update=update,
        context=context,
        image_path="dungeon_entrada.jpg",
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def dungeon_join_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa seleção de dungeon - pede apenas a senha."""
    query = update.callback_query
    chat_id = query.message.chat_id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    dungeon_id = query.data.replace("dungeon_join_select_", "")
    
    # Verifica se a dungeon ainda existe e tem vaga
    instance = DungeonSystem._active_dungeons.get(dungeon_id)
    if not instance or instance.is_active or instance.is_completed or len(instance.members) >= 4:
        await query.answer("Esta dungeon não está mais disponível.", show_alert=True)
        await dungeon_join(update, context)
        return

    context.user_data["dungeon_joining_selected"] = dungeon_id
    await query.answer()
    await query.edit_message_text(
        f"🔑 <b>ENTRAR NA DUNGEON</b>\n\n"
        f"Dungeon: <code>{dungeon_id}</code>\n\n"
        f"Digite a <b>senha de 4 dígitos</b>:\n"
        f"<i>Exemplo: 1234</i>",
        parse_mode="HTML"
    )


async def dungeon_process_join_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa entrada em dungeon selecionada (apenas senha)."""
    chat_id = update.effective_chat.id
    player = await PlayerRepository.get_player(chat_id)
    if not player or not context.user_data.get("dungeon_joining_selected"):
        return

    dungeon_id = context.user_data["dungeon_joining_selected"]
    password = update.message.text.strip()
    
    if len(password) != 4 or not password.isdigit():
        await update.message.reply_text("❌ A senha deve ter exatamente 4 dígitos numéricos!")
        return

    context.user_data["dungeon_joining_selected"] = False

    success, msg = DungeonSystem.join_dungeon(player, dungeon_id, password)
    await PlayerRepository.save_player(player)

    if success:
        await update.message.reply_text(f"✅ {msg}", parse_mode="HTML")
        await dungeon_main(update, context)
    else:
        await update.message.reply_text(f"❌ {msg}", parse_mode="HTML")


async def dungeon_process_create(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa a criação de dungeon com a senha digitada."""
    chat_id = update.effective_chat.id
    player = await PlayerRepository.get_player(chat_id)
    if not player or not context.user_data.get("dungeon_creating"):
        return

    password = update.message.text.strip()
    if len(password) != 4 or not password.isdigit():
        await update.message.reply_text("❌ A senha deve ter exatamente 4 dígitos numéricos!")
        return

    context.user_data["dungeon_creating"] = False

    regions_data = JsonLoader.load("regions.json")
    regions = regions_data.get("regions", [])
    current_region = next((r for r in regions if r["id"] == player.current_region), None)

    success, msg, instance = DungeonSystem.create_dungeon(player, player.current_region, password)
    await PlayerRepository.save_player(player)

    if success:
        await update.message.reply_text(f"✅ {msg}", parse_mode="HTML")
        await dungeon_main(update, context)
    else:
        await update.message.reply_text(f"❌ {msg}", parse_mode="HTML")


async def dungeon_process_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa entrada em dungeon com ID e senha (legado - compatibilidade)."""
    chat_id = update.effective_chat.id
    player = await PlayerRepository.get_player(chat_id)
    if not player or not context.user_data.get("dungeon_joining"):
        return

    parts = update.message.text.strip().split()
    if len(parts) != 2:
        await update.message.reply_text("❌ Formato inválido! Use: ID_DUNGEON SENHA")
        return

    dungeon_id, password = parts
    context.user_data["dungeon_joining"] = False

    success, msg = DungeonSystem.join_dungeon(player, dungeon_id, password)
    await PlayerRepository.save_player(player)

    if success:
        await update.message.reply_text(f"✅ {msg}", parse_mode="HTML")
        await dungeon_main(update, context)
    else:
        await update.message.reply_text(f"❌ {msg}", parse_mode="HTML")


async def dungeon_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia a dungeon (apenas líder)."""
    query = update.callback_query
    chat_id = query.message.chat_id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    dungeon_id = query.data.replace("dungeon_start_", "")
    success, msg = DungeonSystem.start_dungeon(player, dungeon_id)

    if success:
        await query.answer(msg, show_alert=True)
        await dungeon_attack(update, context)
    else:
        await query.answer(msg, show_alert=True)


async def dungeon_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancela a dungeon (apenas líder)."""
    query = update.callback_query
    chat_id = query.message.chat_id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    dungeon_id = query.data.replace("dungeon_cancel_", "")
    success, msg = DungeonSystem.cancel_dungeon(player, dungeon_id)

    await query.answer(msg, show_alert=True)
    if success:
        await dungeon_main(update, context)


async def dungeon_leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sai da dungeon."""
    query = update.callback_query
    chat_id = query.message.chat_id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    dungeon_id = query.data.replace("dungeon_leave_", "")
    success, msg = DungeonSystem.leave_dungeon(player, dungeon_id)

    await query.answer(msg, show_alert=True)
    if success:
        await dungeon_main(update, context)


async def dungeon_attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa ataque à onda atual."""
    chat_id = update.effective_chat.id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    # Determina dungeon_id
    if update.callback_query:
        dungeon_id = update.callback_query.data.replace("dungeon_attack_", "")
    else:
        # Procura dungeon ativa do player
        instance = None
        for d in DungeonSystem._active_dungeons.values():
            if d.get_member(player.chat_id) and d.is_active and not d.is_completed:
                instance = d
                break
        if not instance:
            await update.message.reply_text("Você não está em uma dungeon ativa.")
            return
        dungeon_id = instance.dungeon_id

    instance = DungeonSystem._active_dungeons.get(dungeon_id)
    if not instance or not instance.is_active:
        await update.message.reply_text("Dungeon não está ativa.")
        return

    # Pega monstros da onda atual
    monsters = DungeonSystem.get_dungeon_monsters(instance.dungeon_id, instance.current_wave)
    if not monsters:
        await update.message.reply_text("Erro: Nenhum monstro nesta onda.")
        return

    # Escolhe um monstro aleatório da onda
    monster_id = random.choice(monsters)

    result = DungeonSystem.process_dungeon_battle(instance, player, monster_id)

    summary = []
    if result["winner"] == "player":
        summary.append(f"🏆 <b>VITÓRIA!</b> Você derrotou {monster_id.replace('_', ' ').title()}!")
        summary.append(f"💥 Dano causado: {instance.member_damage.get(player.chat_id, 0)}")
    elif result["winner"] == "enemy":
        summary.append(f"💀 <b>DERROTA!</b> Você foi derrotado por {monster_id.replace('_', ' ').title()}!")
    else:
        summary.append("⚖️ Empate.")

    # Verifica se todos os monstros da onda foram derrotados
    # Para simplificar, cada jogador ataca um monstro por vez
    # A onda avança quando o líder clica em "Próxima Onda"

    text = (
        f"⚔️ <b>BATALHA NA DUNGEON - Onda {instance.current_wave}</b>\n\n"
        + "\n".join(summary) + "\n\n"
        f"💚 Seu HP: {player.hp}/{player.max_hp}\n"
        f"⚡ Energia: {player.energy}/{player.max_energy}"
    )

    keyboard = [
        [InlineKeyboardButton("⚔️ Atacar Novamente", callback_data=f"dungeon_attack_{dungeon_id}")],
        [InlineKeyboardButton("🧪 Usar Poção", callback_data=f"dungeon_potion_{dungeon_id}")],
    ]

    # Se for líder, mostra botão de próxima onda
    if player.chat_id == instance.leader_id:
        keyboard.append([InlineKeyboardButton("🌊 Próxima Onda (Líder)", callback_data=f"dungeon_next_wave_{dungeon_id}")])

    keyboard.append([InlineKeyboardButton("⬅️ Voltar", callback_data=f"dungeon_info_{dungeon_id}")])

    await MessageManager.send_or_edit(
        update=update,
        context=context,
        image_path="dungeon_battle.jpg",
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def dungeon_next_wave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Avança para a próxima onda (apenas líder)."""
    query = update.callback_query
    chat_id = query.message.chat_id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    dungeon_id = query.data.replace("dungeon_next_wave_", "")
    instance = DungeonSystem._active_dungeons.get(dungeon_id)
    if not instance:
        await query.answer("Dungeon não encontrada.", show_alert=True)
        return

    if player.chat_id != instance.leader_id:
        await query.answer("Apenas o líder pode avançar a onda.", show_alert=True)
        return

    success, msg, monsters = DungeonSystem.next_wave(instance)

    if not success:  # Dungeon completada
        await query.answer(msg, show_alert=True)
        await dungeon_main(update, context)
        return

    await query.answer(msg, show_alert=True)
    await dungeon_attack(update, context)


async def dungeon_potion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Usa poção na dungeon."""
    query = update.callback_query
    chat_id = query.message.chat_id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    # Lógica simples de poção
    potions = player.inventory.get("consumables", {})
    hp_potion = potions.get("potion_hp_minor", 0)

    if hp_potion <= 0:
        await query.answer("❌ Você não tem poções de vida!", show_alert=True)
        return

    potions["potion_hp_minor"] = hp_potion - 1
    heal = min(50, player.max_hp - player.hp)
    player.hp += heal
    await PlayerRepository.save_player(player)

    await query.answer(f"🧪 Poção usada! HP restaurado: +{heal}", show_alert=True)
    await dungeon_attack(update, context)


async def dungeon_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra info da dungeon."""
    query = update.callback_query
    chat_id = query.message.chat_id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    dungeon_id = query.data.replace("dungeon_info_", "")
    instance = DungeonSystem._active_dungeons.get(dungeon_id)
    if instance:
        await dungeon_active_info(update, context, player, instance)
    else:
        await dungeon_main(update, context)