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
            print("DEBUG: query is None")
            return

        data = query.data or ""
        print(f"DEBUG Callback data: '{data}'")
        logger.debug(f"Processando Callback: {data}")

        # Ordena rotas por especificidade (maior comprimento de chave primeiro)
        sorted_routes: List[Tuple[str, Callable]] = sorted(
            self.routes.items(), key=lambda item: len(item[0]), reverse=True
        )

        print(f"DEBUG Total routes: {len(self.routes)}")
        print(f"DEBUG First few routes: {list(self.routes.keys())[:5]}")

        # 1. Correspondência exata
        if data in self.routes:
            print(f"DEBUG Exact match for: {data}")
            return await self.routes[data](update, context)

        # 2. Correspondência por prefixo
        matched = False
        for key, handler in sorted_routes:
            if data.startswith(key):
                print(f"DEBUG Prefix match: '{data}' -> '{key}'")
                matched = True
                return await handler(update, context)

        if not matched:
            print(f"DEBUG No match found for: {data}")

        # 3. Fallback se nenhuma rota for encontrada
        if self.fallback_handler:
            return await self.fallback_handler(update, context)

        logger.warning(f"Callback não reconhecido: {data}")
        try:
            await query.answer("Ação indisponível ou menu expirado.", show_alert=True)
        except Exception:
            pass
