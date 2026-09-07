"""
Módulo Principal do Bot de RPG de Mushoku Tensei via Telegram.
Inicializa o bot, registra comandos e handlers de callbacks (botões).
"""
import logging
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)
from config import BOT_TOKEN

# Handlers de Registro e Hub
from systems.login_system import (
    start_login,
    receive_name,
    select_race_callback,
    select_vocation_callback,
    ASK_NAME,
    CHOOSE_RACE,
    CHOOSE_VOCATION,
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

# Handlers do Mundo (Guilda, Exploração, Estalagem, Treino, LootBoxes, Viagem, Dungeons, Grupos)
from world.guild_menu import (
    guild_main,
    guild_quests_board,
    guild_active_quests,
    accept_quest_action,
    claim_quest_action,
)
from world.exploration_menu import (
    explore_menu,
    hunt_current,
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
from world.travel_menu import (
    travel_menu,
    travel_action,
)
from world.dungeon_menu import (
    dungeon_main,
    dungeon_create,
    dungeon_join,
    dungeon_process_create,
    dungeon_process_join,
    dungeon_process_join_selected,
    dungeon_join_select,
    dungeon_start,
    dungeon_cancel,
    dungeon_leave,
    dungeon_attack,
    dungeon_next_wave,
    dungeon_potion,
    dungeon_info,
)
from world.party_menu import (
    party_main,
    party_create,
    party_process_create,
    party_invite,
    party_process_invite,
    party_invites,
    party_accept,
    party_decline,
    party_leave,
    party_kick,
    party_process_kick,
    party_disband,
    party_transfer,
    party_process_transfer,
    party_funds,
    party_deposit,
    party_process_deposit,
    party_withdraw,
    party_process_withdraw,
    party_info_callback,
    party_browse,
    party_request_join,
    party_join_requests,
    party_approve_join,
    party_deny_join,
    party_toggle_public,
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
    # 1. Comando /start (único comando restante)
    # ==========================================
    login_conv = ConversationHandler(
        entry_points=[CommandHandler("start", start_login)],
        states={
            ASK_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name)
            ],
            CHOOSE_RACE: [
                CallbackQueryHandler(select_race_callback, pattern="^race_")
            ],
            CHOOSE_VOCATION: [
                CallbackQueryHandler(select_vocation_callback, pattern="^vocation_")
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
    app.add_handler(CallbackQueryHandler(hunt_current, pattern="^hunt_current$"))

    # Mapa & Viagens
    app.add_handler(CallbackQueryHandler(travel_menu, pattern="^travel_menu$"))
    app.add_handler(CallbackQueryHandler(travel_action, pattern="^travel_"))

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

    # Dungeons
    app.add_handler(CallbackQueryHandler(dungeon_main, pattern="^dungeon_main$"))
    app.add_handler(CallbackQueryHandler(dungeon_create, pattern="^dungeon_create$"))
    app.add_handler(CallbackQueryHandler(dungeon_join, pattern="^dungeon_join$"))
    app.add_handler(CallbackQueryHandler(dungeon_join_select, pattern="^dungeon_join_select_"))
    app.add_handler(CallbackQueryHandler(dungeon_start, pattern="^dungeon_start_"))
    app.add_handler(CallbackQueryHandler(dungeon_cancel, pattern="^dungeon_cancel_"))
    app.add_handler(CallbackQueryHandler(dungeon_leave, pattern="^dungeon_leave_"))
    app.add_handler(CallbackQueryHandler(dungeon_attack, pattern="^dungeon_attack_"))
    app.add_handler(CallbackQueryHandler(dungeon_next_wave, pattern="^dungeon_next_wave_"))
    app.add_handler(CallbackQueryHandler(dungeon_potion, pattern="^dungeon_potion_"))
    app.add_handler(CallbackQueryHandler(dungeon_info, pattern="^dungeon_info_"))

    # Grupos de Aventureiros
    app.add_handler(CallbackQueryHandler(party_main, pattern="^party_main$"))
    app.add_handler(CallbackQueryHandler(party_create, pattern="^party_create$"))
    app.add_handler(CallbackQueryHandler(party_invite, pattern="^party_invite$"))
    app.add_handler(CallbackQueryHandler(party_invites, pattern="^party_invites$"))
    app.add_handler(CallbackQueryHandler(party_accept, pattern="^party_accept_"))
    app.add_handler(CallbackQueryHandler(party_decline, pattern="^party_decline_"))
    app.add_handler(CallbackQueryHandler(party_leave, pattern="^party_leave$"))
    app.add_handler(CallbackQueryHandler(party_kick, pattern="^party_kick$"))
    app.add_handler(CallbackQueryHandler(party_disband, pattern="^party_disband$"))
    app.add_handler(CallbackQueryHandler(party_transfer, pattern="^party_transfer$"))
    app.add_handler(CallbackQueryHandler(party_funds, pattern="^party_funds$"))
    app.add_handler(CallbackQueryHandler(party_deposit, pattern="^party_deposit$"))
    app.add_handler(CallbackQueryHandler(party_withdraw, pattern="^party_withdraw$"))
    app.add_handler(CallbackQueryHandler(party_info_callback, pattern="^party_info_"))
    app.add_handler(CallbackQueryHandler(party_browse, pattern="^party_browse$"))
    app.add_handler(CallbackQueryHandler(party_request_join, pattern="^party_request_join_"))
    app.add_handler(CallbackQueryHandler(party_join_requests, pattern="^party_join_requests"))
    app.add_handler(CallbackQueryHandler(party_approve_join, pattern="^party_approve_"))
    app.add_handler(CallbackQueryHandler(party_deny_join, pattern="^party_deny_"))
    app.add_handler(CallbackQueryHandler(party_toggle_public, pattern="^party_toggle_public$"))

    # Baús & LootBoxes
    app.add_handler(CallbackQueryHandler(lootbox_main, pattern="^lootbox_main$"))
    app.add_handler(CallbackQueryHandler(open_box_action, pattern="^open_box_"))

    # MessageHandler único para inputs de texto baseados no estado do usuário
    from core.callback_router import route_text_input
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, route_text_input))

    # ==========================================
    # 3. Handler Central de Erros
    # ==========================================
    async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Log errors and notify user if possible."""
        logger.error(f"Exception while handling an update: {context.error}", exc_info=context.error)
        
        if isinstance(update, Update) and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "❌ Ocorreu um erro interno. A equipe foi notificada. Tente novamente em alguns instantes."
                )
            except Exception:
                pass

    app.add_error_handler(error_handler)

    return app


def main():
    """Função de inicialização do serviço."""
    logger.info("Iniciando Bot de RPG - Mushoku Tensei...")
    app = build_app()
    logger.info("Bot pronto e escutando eventos...")
    app.run_polling()


if __name__ == "__main__":
    main()