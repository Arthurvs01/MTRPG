from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from core.message_manager import MessageManager
from core.text_loader import TextLoader
from database.player_repo import PlayerRepository
from database.market_repo import MarketRepository
from database.item_repo import ItemRepository


async def market_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Exibe o Mercado Global de Trocas entre Aventureiros."""
    chat_id = update.effective_chat.id
    player = PlayerRepository.get_player(chat_id)
    if not player:
        return

    listings = MarketRepository.get_all_active_listings()

    listings_lines = []
    keyboard = []

    for l in listings:
        seller_tag = " (Sua Oferta)" if l["seller_chat_id"] == player.chat_id else f" [Vendedor: {l['seller_name']}]"
        listings_lines.append(
            f"🔹 <b>{l['item_name']}</b> x{l.get('quantity', 1)}\n"
            f"   💰 Preço: <b>{l['price_iron_coins']} Ferros</b> {seller_tag}"
        )

        if l["seller_chat_id"] != player.chat_id:
            keyboard.append([
                InlineKeyboardButton(f"Comprar {l['item_name'][:16]} ({l['price_iron_coins']} F)", callback_data=f"mkt_buy_{l['id']}")
            ])

    keyboard.append([
        InlineKeyboardButton("➕ Anunciar Item para Venda", callback_data="mkt_create_menu"),
        InlineKeyboardButton("📋 Meus Anúncios", callback_data="mkt_my_listings"),
    ])
    keyboard.append([
        InlineKeyboardButton("🏛️ Voltar à Guilda", callback_data="guild_main"),
        InlineKeyboardButton("🏰 Hub Principal", callback_data="hub_main"),
    ])

    text = TextLoader.load(
        "market_main.txt",
        character_name=player.character_name,
        iron_coins=player.iron_coins,
        diamonds=player.diamonds,
        market_listings_body="\n\n".join(listings_lines) if listings_lines else "<i>Nenhum anúncio ativo no mercado no momento. Seja o primeiro a anunciar!</i>",
    )

    await MessageManager.send_or_edit(
        update=update,
        context=context,
        image_path="mercado_loja.png",
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def market_buy_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Executa a compra de uma oferta de outro jogador."""
    query = update.callback_query
    listing_id = query.data.replace("mkt_buy_", "")

    chat_id = update.effective_chat.id
    buyer = PlayerRepository.get_player(chat_id)
    if not buyer:
        return

    success, msg = MarketRepository.buy_listing(buyer, listing_id)
    if not success:
        await query.answer(msg, show_alert=True)
        return

    PlayerRepository.save_player(buyer)
    await query.answer(msg, show_alert=True)
    await market_main(update, context)


async def market_my_listings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Exibe as ofertas anunciadas pelo próprio jogador."""
    chat_id = update.effective_chat.id
    player = PlayerRepository.get_player(chat_id)
    if not player:
        return

    listings = MarketRepository.get_all_active_listings()
    my_listings = [l for l in listings if l["seller_chat_id"] == player.chat_id]

    lines = []
    keyboard = []

    for l in my_listings:
        lines.append(f"🔸 <b>{l['item_name']}</b> x{l.get('quantity', 1)} — 💰 {l['price_iron_coins']} Ferros")
        keyboard.append([
            InlineKeyboardButton(f"❌ Cancelar Anúncio: {l['item_name'][:16]}", callback_data=f"mkt_cancel_{l['id']}")
        ])

    keyboard.append([
        InlineKeyboardButton("➕ Anunciar Novo Item", callback_data="mkt_create_menu"),
        InlineKeyboardButton("⬅️ Voltar ao Mercado", callback_data="market_main"),
    ])

    text = TextLoader.load(
        "market_my_listings.txt",
        character_name=player.character_name,
        my_listings_body="\n".join(lines) if lines else "<i>Você não possui nenhuma oferta anunciada no momento.</i>",
    )

    await MessageManager.send_or_edit(
        update=update,
        context=context,
        image_path="mercado_loja.png",
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def market_cancel_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancela o anúncio do jogador e devolve os itens."""
    query = update.callback_query
    listing_id = query.data.replace("mkt_cancel_", "")

    chat_id = update.effective_chat.id
    player = PlayerRepository.get_player(chat_id)
    if not player:
        return

    success, msg = MarketRepository.cancel_listing(player, listing_id)
    if not success:
        await query.answer(msg, show_alert=True)
        return

    PlayerRepository.save_player(player)
    await query.answer("Anúncio cancelado com sucesso!", show_alert=True)
    await market_my_listings(update, context)


async def market_create_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menu para o jogador escolher um item da sua bolsa para colocar à venda."""
    chat_id = update.effective_chat.id
    player = PlayerRepository.get_player(chat_id)
    if not player:
        return

    keyboard = []

    # Opções de materiais
    for mat_id, qty in player.inventory.get("materials", {}).items():
        if qty > 0:
            mat_item = ItemRepository.get_item(mat_id)
            name = mat_item.name if mat_item else mat_id
            base_val = mat_item.value_in_iron_coins if mat_item else 20
            # Preço sugerido do mercado = 1.2x do valor base
            suggested_price = int(base_val * 1.3)
            keyboard.append([
                InlineKeyboardButton(f"Vender {name} x1 por {suggested_price} F", callback_data=f"mkt_sell_mat_{mat_id}_{suggested_price}")
            ])

    # Opções de runas
    for rune_id, qty in player.inventory.get("runes", {}).items():
        if qty > 0:
            r_item = ItemRepository.get_item(rune_id)
            name = r_item.name if r_item else rune_id
            suggested_price = 90
            keyboard.append([
                InlineKeyboardButton(f"Vender {name} x1 por {suggested_price} F", callback_data=f"mkt_sell_rune_{rune_id}_{suggested_price}")
            ])

    keyboard.append([
        InlineKeyboardButton("⬅️ Voltar ao Mercado", callback_data="market_main")
    ])

    text = (
        f"📦 <b>═══ ANUNCIAR ITEM NO MERCADO DA GUILDA ═══</b>\n\n"
        f"Selecione um item da sua mochila para listar no mercado comunitário:\n"
        f"<i>Ao anunciar, outros jogadores poderão comprar seu item e você receberá as Moedas de Ferro!</i>\n"
    )

    await MessageManager.send_or_edit(
        update=update,
        context=context,
        image_path="mercado_loja.png",
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def market_sell_item_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Executa a publicação do anúncio."""
    query = update.callback_query
    parts = query.data.split("_")  # mkt, sell, type, id, price
    if len(parts) < 5:
        return

    item_type = parts[2]
    item_id = parts[3]
    price = int(parts[4])

    chat_id = update.effective_chat.id
    player = PlayerRepository.get_player(chat_id)
    if not player:
        return

    # Retira 1 unidade da bolsa do jogador
    if item_type == "mat":
        mats = player.inventory.get("materials", {})
        if mats.get(item_id, 0) < 1:
            await query.answer("Você não possui este material.", show_alert=True)
            return
        mats[item_id] -= 1
        if mats[item_id] <= 0:
            del mats[item_id]
        real_type = "material"

    elif item_type == "rune":
        runes = player.inventory.get("runes", {})
        if runes.get(item_id, 0) < 1:
            await query.answer("Você não possui esta runa.", show_alert=True)
            return
        runes[item_id] -= 1
        if runes[item_id] <= 0:
            del runes[item_id]
        real_type = "rune"
    else:
        return

    success, msg = MarketRepository.create_listing(
        seller=player,
        item_id=item_id,
        item_type=real_type,
        quantity=1,
        price_iron_coins=price
    )

    if success:
        PlayerRepository.save_player(player)

    await query.answer(msg, show_alert=True)
    await market_my_listings(update, context)
