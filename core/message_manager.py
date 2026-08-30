import os
import logging
from typing import Optional
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

        # Verifica se o caminho da imagem existe
        image_full_path = None
        if image_path:
            candidate_path = os.path.join(IMAGES_DIR, image_path)
            if os.path.exists(candidate_path):
                image_full_path = candidate_path

        # Se o texto ultrapassar o limite seguro de legenda de foto, não envia como caption de foto
        if len(text) > MessageManager.MAX_CAPTION_LENGTH:
            image_full_path = None

        # Tentativa 1: Editar mensagem existente se tivermos o message_id
        if message_id:
            try:
                if image_full_path:
                    with open(image_full_path, "rb") as f:
                        media = InputMediaPhoto(
                            media=f,
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
            if image_full_path:
                with open(image_full_path, "rb") as f:
                    new_msg = await context.bot.send_photo(
                        chat_id=chat_id,
                        photo=f,
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
