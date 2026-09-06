"""
Módulo Principal do Bot de RPG de Mushoku Tensei via Telegram.
Inicializa o bot, registra comandos e handlers de callbacks (botões).
"""
import logging
import asyncio
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    Defaults,
)
from telegram import constants, LinkPreviewOptions
from config import BOT_TOKEN
try:
    import aiohttp
    from aiohttp import TCPConnector
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

# Handlers de Registro e Hub
from systems.login_system import (
    start_login,
    receive_name,
    select_race_callback,
    select_vocation_callback,
    ASK_NAME,
)
from world.hub_menu import hub_main_menu

# Handlers de Personagem & Perfil
from systems.character.character_menu import (
    character_profile,
    character_skills_menu,
    stat_distribute_menu,
    add_stat,
)
from systems.character.inventory_menu import (
    inventory_menu,
    equipments_menu,
    equip_item_action,
    use_item_action,
)

# Handlers do Mundo (Guilda, Exploração, Estalagem, Treino, LootBoxes)
from world.guild_menu import (
    guild_main,
    guild_quests_board,
    guild_active_quests,
    accept_quest_action,
    claim_quest_action,
)
from world.exploration_menu import (
    explore_menu,
    hunt_region_fittoa,
    hunt_region_rikarisu,
)
from world.inn_menu import (
    inn_main,
    inn_rest_simple_action,
    inn_rest_luxury_action,
    inn_rest_diamonds_action,
)
from world.training_menu import (
    training_main,
    train_sword_action,
    train_magic_action,
    train_touki_action,
)
from world.lootbox_menu import (
    lootbox_main,
    open_box_action,
)

# Handlers de Forja, Crafting e Mercado entre Players
from world.crafting_menu import (
    crafting_main,
    crafting_category_menu,
    craft_exec_action,
    upgrade_menu,
    upgrade_level_action,
    select_rune_for_socket,
    socket_rune_action,
)
from world.market_menu import (
    market_main,
    market_buy_action,
    market_my_listings,
    market_cancel_action,
    market_create_menu,
    market_sell_item_action,
)

# Configuração de Logs
logging.basicConfig(
    format="%(asctime)s - [%(levelname)s] - %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def build_app():
    """Constrói e configura a aplicação do Telegram Bot."""
    if HAS_AIOHTTP:
        connector = TCPConnector(
            limit=100,
            limit_per_host=30,
            ttl_dns_cache=300,
            use_dns_cache=True,
            keepalive_timeout=30,
            enable_cleanup_closed=True,
            force_close=False,
        )
        client_session = aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(
                total=15,
                connect=10,
                sock_read=15,
                sock_connect=10,
            ),
        )
        app = (
            ApplicationBuilder()
            .token(BOT_TOKEN)
            .connect_timeout(10)
            .read_timeout(15)
            .write_timeout(15)
            .pool_timeout(10)
            .get_updates_read_timeout(30)
            .get_updates_write_timeout(15)
            .get_updates_connect_timeout(10)
            .get_updates_pool_timeout(10)
            .defaults(Defaults(
                parse_mode=constants.ParseMode.HTML,
                do_quote=False,
                link_preview_options=LinkPreviewOptions(is_disabled=True),
            ))
            .concurrent_updates(True)
            .http_version("2")
            .post_shutdown(_close_session)
            .build()
        )
        app._http_client = client_session
    else:
        app = (
            ApplicationBuilder()
            .token(BOT_TOKEN)
            .connect_timeout(10)
            .read_timeout(15)
            .write_timeout(15)
            .pool_timeout(10)
            .get_updates_read_timeout(30)
            .get_updates_write_timeout(15)
            .get_updates_connect_timeout(10)
            .get_updates_pool_timeout(10)
            .defaults(Defaults(
                parse_mode=constants.ParseMode.HTML,
                do_quote=False,
                link_preview_options=LinkPreviewOptions(is_disabled=True),
            ))
            .concurrent_updates(True)
            .post_shutdown(_close_session)
            .build()
        )
    return app


async def _close_session(app):
    """Fecha a sessão HTTP personalizada ao desligar."""
    if hasattr(app, '_http_client') and app._http_client:
        await app._http_client.close()
    if HAS_AIOHTTP:
        import aiohttp
        await aiohttp.client._default_client.close()

    # ==========================================
    # 1. Comando /start (único comando restante)
    # ==========================================
    login_conv = ConversationHandler(
        entry_points=[CommandHandler("start", start_login)],
        states={
            ASK_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name)
            ],
        },
        fallbacks=[CommandHandler("start", start_login)],
        allow_reentry=True,
    )

    app.add_handler(login_conv)

    # ==========================================
    # 2. Handlers de CallbackQuery (Botões Inline)
    # Usamos regex patterns para matching - o Telegram filtra antes de chamar
    # ==========================================

    #menu principal
    app.add_handler(CallbackQueryHandler(hub_main_menu, pattern="^hub_main$"))

    # Personagem & Perfil
    app.add_handler(CallbackQueryHandler(character_profile, pattern="^profile$"))
    app.add_handler(CallbackQueryHandler(character_skills_menu, pattern="^skills_menu$"))
    app.add_handler(CallbackQueryHandler(stat_distribute_menu, pattern="^stat_distribute_menu$"))
    app.add_handler(CallbackQueryHandler(add_stat, pattern="^add_stat_"))

    # Mochila & Equipamentos
    app.add_handler(CallbackQueryHandler(inventory_menu, pattern="^inventory_menu$"))
    app.add_handler(CallbackQueryHandler(equipments_menu, pattern="^equipments_menu$"))
    app.add_handler(CallbackQueryHandler(equip_item_action, pattern="^equip_item_"))
    app.add_handler(CallbackQueryHandler(use_item_action, pattern="^use_item_"))

    # Guilda de Aventureiros
    app.add_handler(CallbackQueryHandler(guild_main, pattern="^guild_main$"))
    app.add_handler(CallbackQueryHandler(guild_quests_board, pattern="^guild_quests_board.*"))
    app.add_handler(CallbackQueryHandler(guild_active_quests, pattern="^guild_active_quests$"))
    app.add_handler(CallbackQueryHandler(accept_quest_action, pattern="^accept_quest_"))
    app.add_handler(CallbackQueryHandler(claim_quest_action, pattern="^claim_quest_"))

    # Forja, Crafting e Upgrades
    app.add_handler(CallbackQueryHandler(crafting_main, pattern="^crafting_main$"))
    app.add_handler(CallbackQueryHandler(crafting_category_menu, pattern="^craft_cat_"))
    app.add_handler(CallbackQueryHandler(craft_exec_action, pattern="^craft_exec_"))
    app.add_handler(CallbackQueryHandler(upgrade_menu, pattern="^upgrade_menu$"))
    app.add_handler(CallbackQueryHandler(upgrade_level_action, pattern="^up_lvl_"))
    app.add_handler(CallbackQueryHandler(select_rune_for_socket, pattern="^up_rune_"))
    app.add_handler(CallbackQueryHandler(socket_rune_action, pattern="^sock_"))

    # Mercado entre Players (Player-to-Player)
    app.add_handler(CallbackQueryHandler(market_main, pattern="^market_main$"))
    app.add_handler(CallbackQueryHandler(market_main, pattern="^mkt_all$"))        # Filtro: todos itens
    app.add_handler(CallbackQueryHandler(market_main, pattern="^mkt_weapon$"))     # Filtro: armas
    app.add_handler(CallbackQueryHandler(market_main, pattern="^mkt_staff$"))      # Filtro: cajados
    app.add_handler(CallbackQueryHandler(market_main, pattern="^mkt_armor$"))      # Filtro: armaduras
    app.add_handler(CallbackQueryHandler(market_main, pattern="^mkt_accessory$"))   # Filtro: acessórios
    app.add_handler(CallbackQueryHandler(market_buy_action, pattern="^mkt_buy_"))  # Compra de listing específico
    app.add_handler(CallbackQueryHandler(market_my_listings, pattern="^mkt_my_listings$"))
    app.add_handler(CallbackQueryHandler(market_cancel_action, pattern="^mkt_cancel_"))
    app.add_handler(CallbackQueryHandler(market_create_menu, pattern="^mkt_create_menu$"))
    app.add_handler(CallbackQueryHandler(market_sell_item_action, pattern="^mkt_sell_"))

    # Exploração e Caçada
    app.add_handler(CallbackQueryHandler(explore_menu, pattern="^explore_menu$"))
    app.add_handler(CallbackQueryHandler(hunt_region_fittoa, pattern="^hunt_fittoa$"))
    app.add_handler(CallbackQueryHandler(hunt_region_rikarisu, pattern="^hunt_rikarisu$"))

    # Estalagem e Descanso
    app.add_handler(CallbackQueryHandler(inn_main, pattern="^inn_main$"))
    app.add_handler(CallbackQueryHandler(inn_rest_simple_action, pattern="^inn_rest_simple$"))
    app.add_handler(CallbackQueryHandler(inn_rest_luxury_action, pattern="^inn_rest_luxury$"))
    app.add_handler(CallbackQueryHandler(inn_rest_diamonds_action, pattern="^inn_rest_diamonds$"))

    # Treinamento & Dojo
    app.add_handler(CallbackQueryHandler(training_main, pattern="^training_main$"))
    app.add_handler(CallbackQueryHandler(train_sword_action, pattern="^train_sword$"))
    app.add_handler(CallbackQueryHandler(train_magic_action, pattern="^train_magic$"))
    app.add_handler(CallbackQueryHandler(train_touki_action, pattern="^train_touki$"))

    # Baús & LootBoxes
    app.add_handler(CallbackQueryHandler(lootbox_main, pattern="^lootbox_main$"))
    app.add_handler(CallbackQueryHandler(open_box_action, pattern="^open_box_"))

    # ==========================================
    # 3. Handler Central de Erros (opcional)
    # ==========================================
    # Pode adicionar error handlers aqui se desejar

    return app


def main():
    """Função de inicialização do serviço."""
    logger.info("Iniciando Bot de RPG - Mushoku Tensei...")
    
    # Pré-carrega imagens comuns para evitar I/O de disco nas primeiras interações
    common_images = [
        "welcome.jpg",
        "city_hub.png",
        "character_menu.jpg",
        "inventario_bolsa.png",
        "guilda_aventureiros.png",
        "exploracao_floresta.jpg",
        "dojo_treinamento.jpg",
        "bau_lootbox.png",
        "commerce.png",
        "quadro_missoes.png",
        "status_atributos.jpg",
        "equipamentos_armas.png",
        "perfil_aventureiro.jpg",
        "missions.png",
        "allies.png",
        "reencarnacao_boas_vindas.jpg",
        "floor_1.jpg",
    ]
    from core.message_manager import MessageManager
    import asyncio
    asyncio.run(MessageManager.preload_images(common_images))
    logger.info(f"Pré-carregadas {len(common_images)} imagens no cache")
    
    app = build_app()
    logger.info("Bot pronto e escutando eventos...")
    app.run_polling(
        poll_interval=0.0,
        timeout=10,
        bootstrap_retries=3,
        drop_pending_updates=True,
        allowed_updates=["callback_query", "message", "inline_query"],
    )


if __name__ == "__main__":
    main()