import asyncio
import os
import logging
from typing import Optional, Dict
from telegram import InputMediaPhoto, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from config import IMAGES_DIR

logger = logging.getLogger(__name__)


class MessageManager:
    """
    Gerenciador Central de Interface do Telegram.
    Permite renderizar telas ricas (Foto + Legenda + Botões Inline) ou Mensagens de Texto
    editando a mensagem anterior para criar uma experiência de aplicativo fluida.
    Possui tratamento automático para limites de caracteres do Telegram (1024 em captions de fotos).
    """

    MAX_CAPTION_LENGTH = 1000  # Limite de segurança para legendas de fotos
    _image_cache: Dict[str, bytes] = {}

    @classmethod
    async def _get_image(cls, image_path: str) -> Optional[bytes]:
        """Carrega imagem do disco com cache em memória (async, não bloqueia event loop)."""
        if image_path in cls._image_cache:
            return cls._image_cache[image_path]
        
        candidate_path = os.path.join(IMAGES_DIR, image_path)
        if not os.path.exists(candidate_path):
            return None
        
        try:
            loop = asyncio.get_running_loop()
            data = await loop.run_in_executor(None, cls._read_image_sync, candidate_path)
            # Cache apenas imagens pequenas (< 500KB) para evitar uso excessivo de memória
            if data and len(data) < 500_000:
                cls._image_cache[image_path] = data
            return data
        except Exception as e:
            logger.error(f"Erro ao carregar imagem {candidate_path}: {e}")
            return None

    @staticmethod
    def _read_image_sync(path: str) -> bytes:
        """Leitura síncrona de imagem para uso em executor."""
        with open(path, "rb") as f:
            return f.read()

    @classmethod
    async def preload_images(cls, image_paths: list[str]) -> None:
        """Pré-carrega imagens comuns na inicialização (async)."""
        for path in image_paths:
            await cls._get_image(path)

    @staticmethod
    async def send_or_edit(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        image_path: Optional[str],
        text: str,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        parse_mode: str = "HTML",
    ):
        """
        Envia uma nova tela ou edita a mensagem existente.
        Caso o texto ultrapasse o limite de legenda de fotos (1024 caracteres),
        faz fallback automático para renderização em texto puro (que suporta até 4096 caracteres).
        """
        if update.callback_query:
            query = update.callback_query
            chat_id = query.message.chat_id
            message_id = query.message.message_id
            try:
                await query.answer()
            except Exception as e:
                logger.debug(f"Callback answer ignorado: {e}")
        else:
            chat_id = update.effective_chat.id
            message_id = context.user_data.get("last_message_id")

        image_data = await MessageManager._get_image(image_path) if image_path else None

        # Se o texto ultrapassar o limite seguro de legenda de foto, não envia como caption de foto
        if len(text) > MessageManager.MAX_CAPTION_LENGTH:
            image_data = None

        # Tentativa 1: Editar mensagem existente se tivermos o message_id
        if message_id:
            try:
                if image_data:
                    from io import BytesIO
                    media = InputMediaPhoto(
                        media=BytesIO(image_data),
                        caption=text,
                        parse_mode=parse_mode,
                    )
                    await context.bot.edit_message_media(
                        chat_id=chat_id,
                        message_id=message_id,
                        media=media,
                        reply_markup=reply_markup,
                    )
                else:
                    await context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_id,
                        text=text,
                        parse_mode=parse_mode,
                        reply_markup=reply_markup,
                    )

                context.user_data["last_message_id"] = message_id
                return
            except Exception as e:
                logger.debug(f"Não foi possível editar a mensagem #{message_id}, enviando nova. Detalhe: {e}")

        # Tentativa 2: Enviar nova mensagem caso a edição falhe ou não haja mensagem anterior
        try:
            if image_data:
                from io import BytesIO
                new_msg = await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=BytesIO(image_data),
                    caption=text,
                    parse_mode=parse_mode,
                    reply_markup=reply_markup,
                )
            else:
                new_msg = await context.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode=parse_mode,
                    reply_markup=reply_markup,
                )

            context.user_data["last_message_id"] = new_msg.message_id
        except Exception as e:
            logger.error(f"Erro fatal ao enviar mensagem para chat {chat_id}: {e}")
