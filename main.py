"""
Módulo Principal do Bot de RPG de Mushoku Tensei via Telegram.
Inicializa o bot, registra todas as rotas de menus, forja, mercado entre players,
treinamentos por classe, energia e inicia o polling de eventos.
"""
import logging
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
    filters,
)
from config import BOT_TOKEN
from core.callback_router import CallbackRouter

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
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN não está definido. Verifique o arquivo .env.")

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .connect_timeout(60)
        .read_timeout(60)
        .write_timeout(60)
        .pool_timeout(60)
        .build()
    )

    # ==========================================
    # 1. Roteamento Centralizado de Callbacks
    # ==========================================
    router = CallbackRouter()

    # Criação de Personagem
    router.register("race_", select_race_callback)
    router.register("vocation_", select_vocation_callback)

    # Hub Principal
    router.register("hub_main", hub_main_menu)

    # Menus de Personagem & Perfil Despoluídos
    router.register("profile", character_profile)
    router.register("skills_menu", character_skills_menu)
    router.register("stat_distribute_menu", stat_distribute_menu)
    router.register("add_stat_", add_stat)

    # Mochila & Equipamentos
    router.register("inventory_menu", inventory_menu)
    router.register("equipments_menu", equipments_menu)
    router.register("equip_item_", equip_item_action)
    router.register("use_item_", use_item_action)

    # Guilda de Aventureiros
    router.register("guild_main", guild_main)
    router.register("guild_quests_board", guild_quests_board)
    router.register("guild_active_quests", guild_active_quests)
    router.register("accept_quest_", accept_quest_action)
    router.register("claim_quest_", claim_quest_action)

    # Forja, Crafting e Upgrades
    router.register("crafting_main", crafting_main)
    router.register("craft_cat_", crafting_category_menu)
    router.register("craft_exec_", craft_exec_action)
    router.register("upgrade_menu", upgrade_menu)
    router.register("up_lvl_", upgrade_level_action)
    router.register("up_rune_", select_rune_for_socket)
    router.register("sock_", socket_rune_action)

    # Mercado entre Players (Player-to-Player)
    router.register("market_main", market_main)
    router.register("mkt_all", market_main)           # Filtro: todos itens
    router.register("mkt_weapon", market_main)      # Filtro: armas
    router.register("mkt_staff", market_main)       # Filtro: cajados
    router.register("mkt_armor", market_main)       # Filtro: armaduras
    router.register("mkt_accessory", market_main)   # Filtro: acessórios
    router.register("mkt_buy_", market_buy_action)  # Compra de listing específico
    router.register("mkt_my_listings", market_my_listings)
    router.register("mkt_cancel_", market_cancel_action)
    router.register("mkt_create_menu", market_create_menu)
    router.register("mkt_sell_", market_sell_item_action)

    # Exploração e Caçada
    router.register("explore_menu", explore_menu)
    router.register("hunt_fittoa", hunt_region_fittoa)
    router.register("hunt_rikarisu", hunt_region_rikarisu)

    # Estalagem e Descanso
    router.register("inn_main", inn_main)
    router.register("inn_rest_simple", inn_rest_simple_action)
    router.register("inn_rest_luxury", inn_rest_luxury_action)
    router.register("inn_rest_diamonds", inn_rest_diamonds_action)

    # Treinamento & Dojo
    router.register("training_main", training_main)
    router.register("train_sword", train_sword_action)
    router.register("train_magic", train_magic_action)
    router.register("train_touki", train_touki_action)

    # Baús & LootBoxes
    router.register("lootbox_main", lootbox_main)
    router.register("open_box_", open_box_action)

    # ==========================================
    # 2. Handlers de Conversação e Comandos
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
    app.add_handler(CommandHandler("hub", hub_main_menu))
    app.add_handler(CommandHandler("menu", hub_main_menu))
    app.add_handler(CommandHandler("perfil", character_profile))
    app.add_handler(CommandHandler("guilda", guild_main))
    app.add_handler(CommandHandler("forja", crafting_main))
    app.add_handler(CommandHandler("mercado", market_main))
    app.add_handler(CommandHandler("explorar", explore_menu))
    app.add_handler(CommandHandler("estalagem", inn_main))
    app.add_handler(CommandHandler("treino", training_main))
    app.add_handler(CommandHandler("bau", lootbox_main))

    # Handler Central de Callbacks Inline
    app.add_handler(CallbackQueryHandler(router.handle))

    return app


def main():
    """Função de inicialização do serviço."""
    logger.info("Iniciando Bot de RPG - Mushoku Tensei...")
    app = build_app()
    logger.info("Bot pronto e escutando eventos...")
    app.run_polling()


if __name__ == "__main__":
    main()
