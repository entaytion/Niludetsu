import asyncio
import discord
import os
import re

# Подавляем низкоуровневые предупреждения gRPC/absl до импорта Google SDK
os.environ.setdefault("GRPC_VERBOSITY", "ERROR")
os.environ.setdefault("GLOG_minloglevel", "3")

from discord import SeparatorSpacing, app_commands
from discord.ext import commands
from typing import Optional

from Niludetsu import Colors, Embed, safe_delete
from Niludetsu.ai.models import (
    HISTORY_LIMIT,
    IMAGE_MODEL_CHOICES,
    LONG_REQUEST_THRESHOLD,
    GeminiChatService,
    PuterImageService,
)
from Niludetsu.config import SERVERS
from Niludetsu.database import database
from Niludetsu.logging import logger
from putergenai import PuterClient


class ConversationManager:
    """Управление историей разговоров через базу данных."""

    def __init__(self, history_limit: int = HISTORY_LIMIT):
        self.history_limit = history_limit
        self.table = "conversation_messages"

    async def add_message(self, user_id: str, role: str, content: str) -> None:
        payload = {
            "user_id": str(user_id),
            "role": role,
            "content": content,
        }
        try:
            await database.insert(self.table, payload)
        except Exception as exc:
            logger.error(f"Ошибка при сохранении сообщения в БД: {exc}")

    async def get_history(self, user_id: str) -> list[dict[str, str]]:
        try:
            rows = await database.where(
                self.table,
                columns=["role", "content", "created_at"],
                filters=[{"column": "user_id", "value": str(user_id)}],
                order=[{"column": "created_at", "ascending": False}],
                limit=self.history_limit,
            )
        except Exception as exc:
            logger.error(f"Ошибка при загрузке истории из БД: {exc}")
            return []

        rows.reverse()
        return [
            {
                "role": row.get("role", "assistant"),
                "content": row.get("content", ""),
            }
            for row in rows
            if row.get("content")
        ]


class EmbedFormatter:
    """Форматирование эмбедов."""

    @staticmethod
    def split_into_v2_views(text: str) -> list[discord.ui.View]:
        max_length = 3900
        parts = EmbedFormatter._split_text(text, max_length)

        views = []
        for idx, part in enumerate(parts):
            children = [
                discord.ui.Separator(visible=True, spacing=SeparatorSpacing.small)
            ]

            if idx == 0:
                children.append(discord.ui.TextDisplay(content="### Ответ ИИ"))

            children.append(discord.ui.TextDisplay(content=part))

            if idx == len(parts) - 1:
                children.append(
                    discord.ui.Separator(
                        visible=True,
                        spacing=SeparatorSpacing.small,
                    )
                )
                children.append(
                    discord.ui.TextDisplay(
                        content=(
                            "-# Модель: Google: Gemini 3 Flash Preview "
                            "(Nullther Enhanced) | Шаблон: Стандартный"
                        )
                    )
                )

            container = discord.ui.Container(
                *children,
                accent_colour=0x5865F2,
            )
            view = discord.ui.LayoutView(timeout=None)
            view.add_item(container)
            views.append(view)

        return views

    @staticmethod
    def _split_text(text: str, max_length: int) -> list[str]:
        if not text:
            return []
        if len(text) <= max_length:
            return [text]

        sentences = text.split(". ")
        parts = []
        current_part: list[str] = []
        current_length = 0

        for sentence in sentences:
            if sentence != sentences[-1]:
                sentence += ". "

            if len(sentence) > max_length:
                if current_part:
                    parts.append("".join(current_part))
                    current_part = []
                    current_length = 0

                words = sentence.split()
                word_chunk = []
                word_length = 0

                for word in words:
                    if word_length + len(word) + 1 > max_length:
                        parts.append(" ".join(word_chunk))
                        word_chunk = [word]
                        word_length = len(word)
                    else:
                        word_chunk.append(word)
                        word_length += len(word) + 1

                if word_chunk:
                    chunk_text = " ".join(word_chunk)
                    current_part = [chunk_text]
                    current_length = len(chunk_text)
            elif current_length + len(sentence) > max_length:
                parts.append("".join(current_part))
                current_part = [sentence]
                current_length = len(sentence)
            else:
                current_part.append(sentence)
                current_length += len(sentence)

        if current_part:
            parts.append("".join(current_part))

        return parts


class AISystem(commands.Cog):
    """Основной класс системы ИИ."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.conversation_manager = ConversationManager()
        self.gemini_api = GeminiChatService(getattr(bot, "http_session", None))
        self.image_api = PuterImageService(getattr(bot, "http_session", None))

    async def cog_unload(self) -> None:
        await asyncio.gather(
            self.gemini_api.close(),
            self.image_api.close(),
        )

    async def _is_bot_mentioned_or_reply(self, message: discord.Message) -> bool:
        bot_mention = f"<@{self.bot.user.id}>"
        is_mentioned = message.content.startswith(bot_mention) or re.search(
            r"^[Нн]ил[аюу]\s*,",
            message.content,
        )

        if is_mentioned:
            return True

        if message.reference and message.reference.message_id:
            try:
                ref_msg = message.reference.cached_message
                if not ref_msg:
                    ref_msg = await message.channel.fetch_message(
                        message.reference.message_id
                    )

                if ref_msg.author.id == self.bot.user.id:
                    if ref_msg.embeds and any(
                        embed.title == "🎨 Генерация завершена"
                        for embed in ref_msg.embeds
                    ):
                        return bool(is_mentioned)
                    return True
            except (discord.NotFound, discord.HTTPException):
                return False

        return False

    async def _validate_reply(self, message: discord.Message) -> bool:
        if not message.reference:
            return True

        try:
            referenced_message = message.reference.cached_message
            if not referenced_message:
                referenced_message = await message.channel.fetch_message(
                    message.reference.message_id
                )

            if referenced_message.author.id != self.bot.user.id:
                return False

            if (
                not referenced_message.reference
                or not referenced_message.reference.message_id
            ):
                return True

            try:
                original_msg = referenced_message.reference.cached_message
                if not original_msg:
                    original_msg = await message.channel.fetch_message(
                        referenced_message.reference.message_id
                    )
                return original_msg.author.id == message.author.id
            except Exception:
                return True
        except discord.NotFound:
            return False
        except Exception:
            return False

    @staticmethod
    def _extract_image_url(message: discord.Message) -> Optional[str]:
        image_extensions = (".png", ".jpg", ".jpeg", ".gif", ".webp")
        for attachment in message.attachments:
            if attachment.filename.lower().endswith(image_extensions):
                return attachment.url
        return None

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot and message.author.id != self.bot.user.id:
            return

        if message.guild and message.guild.id != SERVERS["MAIN_ID"]:
            return

        if not await self._is_bot_mentioned_or_reply(message):
            return

        if not await self._validate_reply(message):
            return

        if message.author.bot:
            return

        user_id = str(message.author.id)

        async with message.channel.typing():
            content = message.content.replace(f"<@{self.bot.user.id}>", "").strip()
            if not content and message.attachments:
                content = "Опиши, что ты видишь на этом изображении"

            image_url = self._extract_image_url(message)
            thinking_message = None

            if len(content) > LONG_REQUEST_THRESHOLD:
                thinking_embed = Embed(
                    description="🤔 Думаю над вашим вопросом...",
                    color=Colors.INFO,
                )
                thinking_embed.set_author(
                    name=message.author.display_name,
                    icon_url=(
                        message.author.avatar.url if message.author.avatar else None
                    ),
                )
                thinking_message = await message.reply(embed=thinking_embed)

            user_history = await self.conversation_manager.get_history(user_id)
            response, used_secondary = await self.gemini_api.generate_response(
                content,
                image_url,
                user_history,
            )

            if not response:
                await safe_delete(thinking_message)
                return

            await safe_delete(thinking_message)

            if used_secondary:
                fallback_embed = Embed(
                    description="🔄 Хм, произошла ошибка, попробуем другой ключ...",
                    color=Colors.WARNING,
                )
                fallback_embed.set_author(
                    name=message.author.display_name,
                    icon_url=(
                        message.author.avatar.url if message.author.avatar else None
                    ),
                )
                fallback_message = await message.channel.send(embed=fallback_embed)
                await asyncio.sleep(3)
                try:
                    await fallback_message.delete()
                except discord.NotFound:
                    pass

            views = EmbedFormatter.split_into_v2_views(response)
            no_pings = discord.AllowedMentions.none()

            for index, view in enumerate(views):
                if index == 0:
                    await message.reply(
                        view=view,
                        mention_author=False,
                        allowed_mentions=no_pings,
                    )
                else:
                    await message.channel.send(view=view, allowed_mentions=no_pings)

            await self.conversation_manager.add_message(user_id, "user", content)
            await self.conversation_manager.add_message(user_id, "assistant", response)

    @app_commands.command(
        name="imagine",
        description="🖼️ Сгенерировать изображение с помощью Puter AI",
    )
    @app_commands.describe(prompt="💬 Описание изображения", model="🤖 Модель (необязательно)")
    @app_commands.choices(
        model=[
            app_commands.Choice(name=name, value=value)
            for name, value in IMAGE_MODEL_CHOICES
        ]
    )
    async def imagine(
        self,
        interaction: discord.Interaction,
        prompt: str,
        model: Optional[str] = None,
    ) -> None:
        await interaction.response.defer(thinking=True)

        login = os.getenv("PUTER_LOGIN")
        password = os.getenv("PUTER_PASSWORD")
        if not login or not password:
            await interaction.followup.send(
                "❌ Ошибка: В `.env` не указано `PUTER_LOGIN` или `PUTER_PASSWORD`!",
                ephemeral=True,
            )
            return

        try:
            async with PuterClient() as client:
                await client.login(login, password)
                token = client.token
                image_result, last_error = await self.image_api.generate(
                    prompt=prompt,
                    token=token,
                    preferred_model=model,
                )

                if not image_result:
                    await interaction.followup.send(
                        "❌ **Генерация не удалась!**\n"
                        "Возможно, запрос заблокирован цензурой или API Puter временно недоступно.\n"
                        f"Последняя ошибка: `{last_error}`"
                    )
                    return

                import io

                ext = "jpg" if "jpeg" in image_result.content_type else "png"
                image_file = discord.File(
                    io.BytesIO(image_result.data),
                    filename=f"generated_image.{ext}",
                )

                embed = Embed(
                    title="🎨 Генерация завершена",
                    description=f"**Запрос:** {prompt}\n**Модель:** `{image_result.model}`",
                    color=Colors.SUCCESS,
                )
                embed.set_image(url=f"attachment://generated_image.{ext}")
                embed.set_footer(
                    text=f"Автор: {interaction.user.display_name}",
                    icon_url=interaction.user.display_avatar.url,
                )

                await interaction.followup.send(embed=embed, file=image_file)
        except Exception as exc:
            logger.error(f"Puter Global Error: {exc}")
            await interaction.followup.send(
                f"❌ **Критическая ошибка системы:** `{str(exc)}`",
                ephemeral=True,
            )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AISystem(bot))
