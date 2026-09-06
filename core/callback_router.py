import logging
from typing import Callable, Dict, List, Tuple, Optional
from telegram import Update
from telegram.ext import ContextTypes
from world.dungeon_menu import (
    dungeon_process_create,
    dungeon_process_join,
)
from world.party_menu import (
    party_process_create,
    party_process_invite,
    party_process_kick,
    party_process_transfer,
    party_process_deposit,
    party_process_withdraw,
)

logger = logging.getLogger(__name__)


class CallbackRouter:
    """
    Roteador Central de Callbacks do Telegram.
    Permite registrar manipuladores para chaves exatas ou prefixos parametrizados.
    """

    def __init__(self):
        self.routes: Dict[str, Callable] = {}
        self.fallback_handler: Optional[Callable] = None
        self._sorted_routes: List[Tuple[str, Callable]] = []
        self._rebuild_sorted_routes()

    def _rebuild_sorted_routes(self):
        """Reconstroi a lista de rotas ordenadas por especificidade (chave mais longa primeiro)."""
        self._sorted_routes = sorted(
            self.routes.items(), key=lambda item: len(item[0]), reverse=True
        )

    def register(self, key: str, handler: Callable):
        """
        Registra uma rota de callback.
        - Chave exata: 'character_profile', 'guild_hall'
        - Prefixo: 'race_', 'style_', 'cast_spell_', 'quest_'
        """
        self.routes[key] = handler
        self._rebuild_sorted_routes()

    def set_fallback(self, handler: Callable):
        """Define o manipulador padrão para callbacks não correspondidos."""
        self.fallback_handler = handler

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processa a callback query recebida e despacha para a função correspondente."""
        query = update.callback_query
        if not query:
            logger.warning("Callback query is None")
            return

        data = query.data or ""
        logger.debug(f"Processando Callback: {data}")

        # 1. Correspondência exata
        if data in self.routes:
            logger.debug(f"Exact match for: {data}")
            return await self.routes[data](update, context)

        # 2. Correspondência por prefixo (já ordenado por especificidade)
        matched = False
        for key, handler in self._sorted_routes:
            if data.startswith(key):
                logger.debug(f"Prefix match: '{data}' -> '{key}'")
                matched = True
                return await handler(update, context)

        if not matched:
            logger.debug(f"No match found for: {data}")

        # 3. Fallback se nenhuma rota for encontrada
        if self.fallback_handler:
            return await self.fallback_handler(update, context)

        logger.warning(f"Callback não reconhecido: {data}")
        try:
            await query.answer("Ação indisponível ou menu expirado.", show_alert=True)
        except Exception:
            pass


async def route_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Roteia inputs de texto baseado no estado do usuário (user_data)."""
    user_data = context.user_data

    # Dungeon creation
    if user_data.get("dungeon_creating"):
        await dungeon_process_create(update, context)
        return

    if user_data.get("dungeon_joining"):
        await dungeon_process_join(update, context)
        return

    # Party system
    if user_data.get("party_creating"):
        await party_process_create(update, context)
        return

    if user_data.get("party_invite_target"):
        await party_process_invite(update, context)
        return

    if user_data.get("party_kick_target"):
        await party_process_kick(update, context)
        return

    if user_data.get("party_transfer_target"):
        await party_process_transfer(update, context)
        return

    if user_data.get("party_deposit_amount"):
        await party_process_deposit(update, context)
        return

    if user_data.get("party_withdraw_amount"):
        await party_process_withdraw(update, context)
        return

    # Login system (name input)
    if user_data.get("awaiting_name"):
        from systems.login_system import receive_name
        await receive_name(update, context)
        return

    # Se nenhum estado especial, ignora
    logger.debug(f"Texto recebido sem estado especial: {update.message.text[:50]}")