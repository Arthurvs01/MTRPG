from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from core.message_manager import MessageManager
from core.text_loader import TextLoader
from database.player_repo import PlayerRepository
from models.player import Player
from systems.party_system import PartySystem


async def party_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menu principal do Grupo de Aventureiros."""
    chat_id = update.effective_chat.id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    player.regen_energy_passively()

    if player.party_id:
        party_info = PartySystem.get_party_info(player.party_id)
        if party_info:
            await party_info_menu(update, context, player, party_info)
            return

    # Não está em grupo
    text = TextLoader.load(
        "party_main.txt",
        character_name=player.character_name,
        party_status="❌ Sem grupo",
    )

    # Busca grupos públicos
    public_parties = PartySystem.get_public_parties()

    keyboard = [
        [InlineKeyboardButton("➕ Criar Grupo de Aventureiros", callback_data="party_create")],
        [InlineKeyboardButton("📋 Ver Convites Pendentes", callback_data="party_invites")],
        [InlineKeyboardButton("🔍 Buscar Grupos Públicos", callback_data="party_browse")],
        [InlineKeyboardButton("⬅️ Voltar ao Hub", callback_data="hub_main")],
        [InlineKeyboardButton("🏰 Menu Principal", callback_data="hub_main")],
    ]

    await MessageManager.send_or_edit(
        update=update,
        context=context,
        image_path="grupo_aventureiros.jpg",
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def party_info_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, player: Player, party_info: dict):
    """Exibe informações do grupo."""
    is_leader = party_info["leader_id"] == player.chat_id
    role_text = "👑 Líder" if is_leader else "👤 Membro"

    members_text = "\n".join([
        f"• {m['name']} (Lvl {m['level']} {m['vocation']}) - {m['role']} {'🟢' if m['online'] else '🔴'}"
        for m in party_info["members"]
    ])

    text = (
        f"🏰 <b>GRUPO: {party_info['name']}</b>\n"
        f"🆔 ID: <code>{party_info['party_id']}</code>\n"
        f"📊 Nível do Grupo: {party_info['level']} | EXP: {party_info['exp']}\n"
        f"💰 Fundo Comum: {party_info['funds']} Ferros\n"
        f"👥 Membros: {party_info['member_count']}/{party_info['max_members']}\n\n"
        f"<b>Seu Cargo:</b> {role_text}\n\n"
        f"<b>Membros:</b>\n{members_text}"
    )

    keyboard = []
    if is_leader:
        keyboard.append([
            InlineKeyboardButton("📨 Convidar Jogador", callback_data="party_invite"),
            InlineKeyboardButton("💰 Gerenciar Fundos", callback_data="party_funds"),
        ])
        keyboard.append([
            InlineKeyboardButton("📋 Solicitações de Entrada", callback_data=f"party_join_requests_{party_info['party_id']}"),
            InlineKeyboardButton("🔓 Alternar Público/Privado", callback_data="party_toggle_public"),
        ])
        keyboard.append([
            InlineKeyboardButton("👑 Transferir Liderança", callback_data="party_transfer"),
            InlineKeyboardButton("🗑️ Dissolver Grupo", callback_data="party_disband"),
        ])
    else:
        keyboard.append([
            InlineKeyboardButton("🚪 Sair do Grupo", callback_data="party_leave"),
        ])

    keyboard.append([
        InlineKeyboardButton("📋 Convites Pendentes", callback_data="party_invites"),
        InlineKeyboardButton("⬅️ Hub", callback_data="hub_main"),
    ])
    keyboard.append([
        InlineKeyboardButton("🏰 Menu Principal", callback_data="hub_main"),
    ])

    await MessageManager.send_or_edit(
        update=update,
        context=context,
        image_path="grupo_aventureiros.jpg",
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def party_info_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para callback party_info_{party_id}."""
    query = update.callback_query
    party_id = query.data.replace("party_info_", "")
    
    chat_id = update.effective_chat.id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return
    
    party_info = PartySystem.get_party_info(party_id)
    if party_info:
        await party_info_menu(update, context, player, party_info)
    else:
        await query.answer("Grupo não encontrado.", show_alert=True)
        await party_main(update, context)


async def party_create(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia criação de grupo."""
    query = update.callback_query
    chat_id = query.message.chat_id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    if player.party_id:
        await query.answer("Você já está em um grupo!", show_alert=True)
        return

    context.user_data["party_creating"] = True
    await query.answer()
    await query.edit_message_text(
        "➕ <b>CRIAR GRUPO DE AVENTUREIROS</b>\n\n"
        "Digite o nome do seu grupo (3-24 caracteres):\n"
        "<i>Exemplo: Cavaleiros de Rudeus</i>",
        parse_mode="HTML"
    )


async def party_process_create(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa criação de grupo."""
    chat_id = update.effective_chat.id
    player = await PlayerRepository.get_player(chat_id)
    if not player or not context.user_data.get("party_creating"):
        return

    name = update.message.text.strip()
    if len(name) < 3 or len(name) > 24:
        await update.message.reply_text("❌ Nome deve ter entre 3 e 24 caracteres!")
        return

    context.user_data["party_creating"] = False

    success, msg, party = PartySystem.create_party(player, name)
    await PlayerRepository.save_player(player)

    if success:
        await update.message.reply_text(f"✅ {msg}", parse_mode="HTML")
        await party_main(update, context)
    else:
        await update.message.reply_text(f"❌ {msg}", parse_mode="HTML")


async def party_invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Líder convida jogador."""
    query = update.callback_query
    chat_id = query.message.chat_id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    context.user_data["party_invite_target"] = True
    await query.answer()
    await query.edit_message_text(
        "📨 <b>CONVIDAR JOGADOR</b>\n\n"
        "Digite o <b>Chat ID</b> do jogador que deseja convidar:\n"
        "<i>O jogador deve estar sem grupo.</i>",
        parse_mode="HTML"
    )


async def party_process_invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa convite."""
    chat_id = update.effective_chat.id
    player = await PlayerRepository.get_player(chat_id)
    if not player or not context.user_data.get("party_invite_target"):
        return

    try:
        target_chat_id = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Chat ID inválido!")
        return

    context.user_data["party_invite_target"] = False

    target_player = PlayerRepository.get_player_sync(target_chat_id)
    if not target_player:
        await update.message.reply_text("❌ Jogador não encontrado!")
        return

    success, msg = PartySystem.invite_player(player, target_player)
    await PlayerRepository.save_player(target_player)

    await update.message.reply_text(f"{'✅' if success else '❌'} {msg}", parse_mode="HTML")


async def party_invites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra convites pendentes."""
    chat_id = update.effective_chat.id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    if not player.party_join_requests:
        text = "📋 <b>CONVITES PENDENTES</b>\n\nNenhum convite pendente."
        keyboard = [[InlineKeyboardButton("⬅️ Voltar", callback_data="party_main")]]
        await MessageManager.send_or_edit(update, context, "grupo_aventureiros.jpg", text, InlineKeyboardMarkup(keyboard))
        return

    text = "📋 <b>CONVITES PENDENTES</b>\n\n"
    keyboard = []

    for party_id in player.party_join_requests:
        party_info = PartySystem.get_party_info(party_id)
        if party_info:
            text += f"• <b>{party_info['name']}</b> (Líder: {party_info['members'][0]['name']})\n"
            keyboard.append([
                InlineKeyboardButton(f"✅ Entrar em {party_info['name']}", callback_data=f"party_accept_{party_id}"),
                InlineKeyboardButton(f"❌ Recusar", callback_data=f"party_decline_{party_id}"),
            ])

    keyboard.append([InlineKeyboardButton("⬅️ Voltar", callback_data="party_main")])

    await MessageManager.send_or_edit(
        update=update,
        context=context,
        image_path="grupo_aventureiros.jpg",
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def party_accept(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Aceita convite."""
    query = update.callback_query
    chat_id = query.message.chat_id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    party_id = query.data.replace("party_accept_", "")
    success, msg = PartySystem.accept_invite(player, party_id)
    await PlayerRepository.save_player(player)

    await query.answer(msg, show_alert=True)
    if success:
        await party_main(update, context)


async def party_decline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recusa convite."""
    query = update.callback_query
    chat_id = query.message.chat_id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    party_id = query.data.replace("party_decline_", "")
    success, msg = PartySystem.decline_invite(player, party_id)

    await query.answer(msg, show_alert=True)
    if success:
        await party_invites(update, context)


async def party_leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sai do grupo."""
    query = update.callback_query
    chat_id = query.message.chat_id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    success, msg = PartySystem.leave_party(player)
    await PlayerRepository.save_player(player)

    await query.answer(msg, show_alert=True)
    if success:
        await party_main(update, context)


async def party_kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Líder remove membro."""
    query = update.callback_query
    chat_id = query.message.chat_id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    context.user_data["party_kick_target"] = True
    await query.answer()
    await query.edit_message_text(
        "👢 <b>REMOVER MEMBRO</b>\n\n"
        "Digite o <b>Chat ID</b> do membro a remover:",
        parse_mode="HTML"
    )


async def party_process_kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa remoção."""
    chat_id = update.effective_chat.id
    player = await PlayerRepository.get_player(chat_id)
    if not player or not context.user_data.get("party_kick_target"):
        return

    try:
        target_chat_id = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Chat ID inválido!")
        return

    context.user_data["party_kick_target"] = False

    success, msg = PartySystem.kick_member(player, target_chat_id)
    await PlayerRepository.save_player(player)

    await update.message.reply_text(f"{'✅' if success else '❌'} {msg}", parse_mode="HTML")


async def party_disband(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Dissolve grupo."""
    query = update.callback_query
    chat_id = query.message.chat_id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    success, msg = PartySystem.disband_party(player)
    await PlayerRepository.save_player(player)

    await query.answer(msg, show_alert=True)
    if success:
        await party_main(update, context)


async def party_transfer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Transfere liderança."""
    query = update.callback_query
    chat_id = query.message.chat_id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    context.user_data["party_transfer_target"] = True
    await query.answer()
    await query.edit_message_text(
        "👑 <b>TRANSFERIR LIDERANÇA</b>\n\n"
        "Digite o <b>Chat ID</b> do novo líder:",
        parse_mode="HTML"
    )


async def party_process_transfer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa transferência."""
    chat_id = update.effective_chat.id
    player = await PlayerRepository.get_player(chat_id)
    if not player or not context.user_data.get("party_transfer_target"):
        return

    try:
        target_chat_id = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Chat ID inválido!")
        return

    context.user_data["party_transfer_target"] = False

    success, msg = PartySystem.transfer_leadership(player, target_chat_id)
    await PlayerRepository.save_player(player)

    await update.message.reply_text(f"{'✅' if success else '❌'} {msg}", parse_mode="HTML")


async def party_funds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gerencia fundos do grupo."""
    query = update.callback_query
    chat_id = query.message.chat_id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    party_info = PartySystem.get_party_info(player.party_id)
    if not party_info:
        await query.answer("Grupo não encontrado.", show_alert=True)
        return

    is_leader = party_info["leader_id"] == player.chat_id

    text = (
        f"💰 <b>FUNDOS DO GRUPO: {party_info['name']}</b>\n\n"
        f"Saldo: {party_info['funds']} Ferros\n"
        f"Seus Ferros: {player.iron_coins}\n\n"
    )

    keyboard = [
        [InlineKeyboardButton("💰 Depositar", callback_data="party_deposit")],
    ]
    if is_leader:
        keyboard.append([InlineKeyboardButton("💸 Sacar (Líder)", callback_data="party_withdraw")])
    keyboard.append([InlineKeyboardButton("⬅️ Voltar", callback_data=f"party_info_{player.party_id}")])

    await MessageManager.send_or_edit(
        update=update,
        context=context,
        image_path="grupo_aventureiros.jpg",
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def party_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Deposita no fundo."""
    query = update.callback_query
    chat_id = query.message.chat_id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    context.user_data["party_deposit_amount"] = True
    await query.answer()
    await query.edit_message_text(
        "💰 <b>DEPOSITAR NO FUNDO DO GRUPO</b>\n\n"
        "Digite a quantidade de Ferros a depositar:",
        parse_mode="HTML"
    )


async def party_process_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa depósito."""
    chat_id = update.effective_chat.id
    player = await PlayerRepository.get_player(chat_id)
    if not player or not context.user_data.get("party_deposit_amount"):
        return

    try:
        amount = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Valor inválido!")
        return

    context.user_data["party_deposit_amount"] = False

    success, msg = PartySystem.deposit_funds(player, amount)
    await PlayerRepository.save_player(player)

    await update.message.reply_text(f"{'✅' if success else '❌'} {msg}", parse_mode="HTML")


async def party_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Líder saca do fundo."""
    query = update.callback_query
    chat_id = query.message.chat_id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    context.user_data["party_withdraw_amount"] = True
    await query.answer()
    await query.edit_message_text(
        "💸 <b>SACAR DO FUNDO DO GRUPO (LÍDER)</b>\n\n"
        "Digite a quantidade de Ferros a sacar:",
        parse_mode="HTML"
    )


async def party_process_withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa saque."""
    chat_id = update.effective_chat.id
    player = await PlayerRepository.get_player(chat_id)
    if not player or not context.user_data.get("party_withdraw_amount"):
        return

    try:
        amount = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Valor inválido!")
        return

    context.user_data["party_withdraw_amount"] = False

    success, msg = PartySystem.withdraw_funds(player, amount)
    await PlayerRepository.save_player(player)

    await update.message.reply_text(f"{'✅' if success else '❌'} {msg}", parse_mode="HTML")


async def party_browse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Exibe grupos públicos disponíveis para entrar."""
    chat_id = update.effective_chat.id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    public_parties = PartySystem.get_public_parties()

    if not public_parties:
        text = "🔍 <b>BUSCAR GRUPOS PÚBLICOS</b>\n\nNenhum grupo público disponível no momento."
        keyboard = [[InlineKeyboardButton("⬅️ Voltar", callback_data="party_main")]]
        await MessageManager.send_or_edit(update, context, "grupo_aventureiros.jpg", text, InlineKeyboardMarkup(keyboard))
        return

    text = "🔍 <b>GRUPOS PÚBLICOS DISPONÍVEIS</b>\n\n"
    keyboard = []

    for party in public_parties:
        text += (
            f"• <b>{party['name']}</b>\n"
            f"  Líder: {party['leader_name']} | Nível: {party['level']} | "
            f"Membros: {party['member_count']}/{party['max_members']}\n"
        )
        keyboard.append([
            InlineKeyboardButton(f"📝 Solicitar: {party['name'][:20]}", callback_data=f"party_request_join_{party['party_id']}")
        ])

    keyboard.append([InlineKeyboardButton("⬅️ Voltar", callback_data="party_main")])

    await MessageManager.send_or_edit(
        update=update,
        context=context,
        image_path="grupo_aventureiros.jpg",
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def party_request_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa solicitação de entrada em grupo público."""
    query = update.callback_query
    chat_id = query.message.chat_id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    party_id = query.data.replace("party_request_join_", "")
    success, msg = PartySystem.request_join(player, party_id)
    await PlayerRepository.save_player(player)

    await query.answer(msg, show_alert=True)
    if success:
        await party_browse(update, context)
    else:
        await party_main(update, context)


async def party_join_requests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Exibe solicitações de entrada pendentes (para líder)."""
    query = update.callback_query
    chat_id = update.effective_chat.id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    # Extrai party_id do callback se presente
    party_id = player.party_id
    if query and "party_join_requests_" in query.data:
        party_id = query.data.replace("party_join_requests_", "")

    if not party_id:
        if query:
            await query.answer("Você não está em um grupo.", show_alert=True)
        return

    requests = PartySystem.get_join_requests(player)

    if not requests:
        text = "📋 <b>SOLICITAÇÕES DE ENTRADA</b>\n\nNenhuma solicitação pendente."
        keyboard = [[InlineKeyboardButton("⬅️ Voltar", callback_data=f"party_info_{party_id}")]]
        await MessageManager.send_or_edit(update, context, "grupo_aventureiros.jpg", text, InlineKeyboardMarkup(keyboard))
        return

    text = "📋 <b>SOLICITAÇÕES DE ENTRADA PENDENTES</b>\n\n"
    keyboard = []

    for req in requests:
        text += f"• <b>{req['name']}</b> (Lvl {req['level']} {req['vocation']})\n"
        keyboard.append([
            InlineKeyboardButton(f"✅ Aprovar {req['name'][:15]}", callback_data=f"party_approve_{req['chat_id']}"),
            InlineKeyboardButton(f"❌ Recusar {req['name'][:15]}", callback_data=f"party_deny_{req['chat_id']}"),
        ])

    keyboard.append([InlineKeyboardButton("⬅️ Voltar", callback_data=f"party_info_{party_id}")])

    await MessageManager.send_or_edit(
        update=update,
        context=context,
        image_path="grupo_aventureiros.jpg",
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def party_approve_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Aprova solicitação de entrada."""
    query = update.callback_query
    chat_id = query.message.chat_id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    target_chat_id = int(query.data.replace("party_approve_", ""))
    success, msg = PartySystem.approve_join_request(player, target_chat_id)
    await PlayerRepository.save_player(player)

    await query.answer(msg, show_alert=True)
    if success:
        await party_join_requests(update, context)
    else:
        await party_info_menu(update, context, player, PartySystem.get_party_info(player.party_id))


async def party_deny_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recusa solicitação de entrada."""
    query = update.callback_query
    chat_id = query.message.chat_id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    target_chat_id = int(query.data.replace("party_deny_", ""))
    success, msg = PartySystem.deny_join_request(player, target_chat_id)

    await query.answer(msg, show_alert=True)
    if success:
        await party_join_requests(update, context)
    else:
        await party_info_menu(update, context, player, PartySystem.get_party_info(player.party_id))


async def party_toggle_public(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Alterna visibilidade pública do grupo."""
    query = update.callback_query
    chat_id = query.message.chat_id
    player = await PlayerRepository.get_player(chat_id)
    if not player:
        return

    success, msg = PartySystem.toggle_public(player)
    await PlayerRepository.save_player(player)

    await query.answer(msg, show_alert=True)
    await party_info_menu(update, context, player, PartySystem.get_party_info(player.party_id))