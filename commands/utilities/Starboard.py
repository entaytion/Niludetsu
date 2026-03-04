import discord
from discord.ext import commands
from Niludetsu import Embed, Time
from Niludetsu.config import SERVERS, STARBOARD_CHANNEL_ID, STARBOARD_MIN_STARS, STARBOARD_EMOJI

class Starboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.star_emoji = STARBOARD_EMOJI
        self.min_stars = STARBOARD_MIN_STARS
        self.time_service = Time()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Обработчик добавления реакций"""
        # Проверяем, что это ваш сервер
        if payload.guild_id != SERVERS["MAIN_ID"]:
            return

        # Проверяем, что канал starboard настроен
        if not STARBOARD_CHANNEL_ID:
            return

        if str(payload.emoji) != self.star_emoji:
            return

        channel = self.bot.get_channel(payload.channel_id)
        if not channel:
            return

        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.NotFound:
            return

        # Получаем количество звезд на сообщении
        star_reaction = discord.utils.get(message.reactions, emoji=self.star_emoji)
        if not star_reaction or star_reaction.count < self.min_stars:
            return

        # Получаем канал starboard
        starboard_channel = self.bot.get_channel(STARBOARD_CHANNEL_ID)
        if not starboard_channel:
            return

        # Создаем эмбед
        content = message.content
        image_url = None
        thumbnail_url = None
        additional_attachments = []

        # Проверяем есть ли эмбеды в сообщении
        if message.embeds:
            embed_data = message.embeds[0]
            if embed_data.description:
                content = f"{content}\n{embed_data.description}" if content else embed_data.description
            if embed_data.image:
                image_url = embed_data.image.url
            elif embed_data.thumbnail:
                thumbnail_url = embed_data.thumbnail.url

        embed = Embed.default(description=content or "*(без текста)*")

        # Добавляем автора и дату создания сообщения
        created_dt = self.time_service.ensure_datetime(message.created_at)
        created_at = self.time_service.format_datetime(created_dt, fmt="DD.MM.YYYY HH:mm")

        embed.set_author(
            name=f"{message.author.display_name} • {created_at}",
            icon_url=message.author.display_avatar.url if message.author.avatar else None
        )

        # Обрабатываем прикрепленные файлы
        if message.attachments:
            for i, attachment in enumerate(message.attachments):
                file_ext = attachment.filename.split('.')[-1].lower()

                # Основное изображение будет первым
                if i == 0:
                    if file_ext in ['png', 'jpg', 'jpeg', 'webp']:
                        image_url = attachment.url
                    elif file_ext in ['gif', 'mp4', 'webm', 'mov']:
                        thumbnail_url = attachment.url
                # Дополнительные вложения
                else:
                    additional_attachments.append((f"Источник {i+1}", attachment.url))

        # Устанавливаем изображение и миниатюру
        if image_url:
            embed.set_image(url=image_url)
        if thumbnail_url:
            embed.set_thumbnail(url=thumbnail_url)

        # Добавляем источник
        embed.add_field(
            name="Источник",
            value=f"[Перейти к сообщению]({message.jump_url})",
            inline=False
        )

        # Добавляем дополнительные источники если они есть
        for name, url in additional_attachments:
            embed.add_field(
                name=name,
                value=f"[Открыть]({url})",
                inline=True
            )

        embed.set_footer(text=f"{star_reaction.count} ⭐")

        # Проверяем, не было ли это сообщение уже опубликовано
        async for old_message in starboard_channel.history(limit=100):
            if old_message.embeds:
                for field in old_message.embeds[0].fields:
                    if field.name == "Источник" and message.jump_url in field.value:
                        # Обновляем количество звезд
                        new_embed = old_message.embeds[0].copy()
                        new_embed.set_footer(text=f"{star_reaction.count} ⭐")
                        await old_message.edit(embed=new_embed)
                        return

        # Публикуем новое сообщение
        await starboard_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        """Обработчик удаления реакций"""
        if not STARBOARD_CHANNEL_ID:
            return

        if str(payload.emoji) != self.star_emoji:
            return

        channel = self.bot.get_channel(payload.channel_id)
        if not channel:
            return

        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.NotFound:
            return

        # Получаем количество звезд на сообщении
        star_reaction = discord.utils.get(message.reactions, emoji=self.star_emoji)
        star_count = star_reaction.count if star_reaction else 0

        # Получаем канал starboard
        starboard_channel = self.bot.get_channel(STARBOARD_CHANNEL_ID)
        if not starboard_channel:
            return

        # Ищем сообщение в starboard
        async for old_message in starboard_channel.history(limit=100):
            if old_message.embeds:
                for field in old_message.embeds[0].fields:
                    if field.name == "Источник" and message.jump_url in field.value:
                        if star_count < self.min_stars:
                            # Удаляем сообщение, если звезд меньше минимума
                            await old_message.delete()
                        else:
                            # Обновляем количество звезд
                            new_embed = old_message.embeds[0].copy()
                            new_embed.set_footer(text=f"{star_count} ⭐")
                            await old_message.edit(embed=new_embed)
                        return

async def setup(bot):
    await bot.add_cog(Starboard(bot))

