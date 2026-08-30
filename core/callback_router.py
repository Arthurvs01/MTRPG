import logging
from typing import Callable, Dict, List, Tuple
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


class CallbackRouter:
    """
    Roteador Central de Callbacks do Telegram.
    Permite registrar manipuladores para chaves exatas ou prefixos parametrizados.
    """

    def __init__(self):
        self.routes: Dict[str, Callable] = {}
        self.fallback_handler: Optional[Callable] = None

    def register(self, key: str, handler: Callable):
        """
        Registra uma rota de callback.
        - Chave exata: 'character_profile', 'guild_hall'
        - Prefixo: 'race_', 'style_', 'cast_spell_', 'quest_'
        """
        self.routes[key] = handler

    def set_fallback(self, handler: Callable):
        """Define o manipulador padrão para callbacks não correspondidos."""
        self.fallback_handler = handler

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processa a callback query recebida e despacha para a função correspondente."""
        query = update.callback_query
        if not query:
            return

        data = query.data or ""
        logger.debug(f"Processando Callback: {data}")

        # Ordena rotas por especificidade (maior comprimento de chave primeiro)
        sorted_routes: List[Tuple[str, Callable]] = sorted(
            self.routes.items(), key=lambda item: len(item[0]), reverse=True
        )

        # 1. Correspondência exata
        if data in self.routes:
            return await self.routes[data](update, context)

        # 2. Correspondência por prefixo
        for key, handler in sorted_routes:
            if data.startswith(key):
                return await handler(update, context)

        # 3. Fallback se nenhuma rota for encontrada
        if self.fallback_handler:
            return await self.fallback_handler(update, context)

        logger.warning(f"Callback não reconhecido: {data}")
        try:
            await query.answer("Ação indisponível ou menu expirado.", show_alert=True)
        except Exception:
            pass
