import asyncio, discord, io
from discord.ext import commands
from Niludetsu import safe_fetch_user, safe_delete, delete_after
from Niludetsu.config import NOTIFICATION_CHANNEL_ID, OWNER_ID
from Niludetsu.development.Webhooks import Webhooks

class PrivateMessageCog(commands.Cog):
    """
    Ког для пересылки личных сообщений в баг-канал и ответа пользователям через !pm.
    """
    def __init__(self, bot):
        self.bot = bot
        self.webhooks = Webhooks(bot)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild and not message.author.bot:
            channel = self.bot.get_channel(NOTIFICATION_CHANNEL_ID)
            if not channel:
                return
            fields = [
                {"name": "ID пользователя", "value": str(message.author.id), "inline": True},
                {"name": "Профиль", "value": message.author.mention, "inline": True},
            ]
            image_url = message.attachments[0].url if message.attachments else None
            embed = discord.Embed(
                title="Новое личное сообщение",
                description=message.content or "[Без текста]",
                color=0x000001
            )
            for field in fields:
                embed.add_field(
                    name=field.get("name", ""),
                    value=field.get("value", ""),
                    inline=field.get("inline", False)
                )
            if image_url:
                embed.set_image(url=image_url)
            embed.set_author(name=str(message.author), icon_url=message.author.display_avatar.url)
            embed.set_footer(text=f"Для ответа используйте !pm {message.author.id}")
            await channel.send(embed=embed)

    def _is_role_id(self, value: str) -> bool:
        """Проверяет, является ли значение ID роли или упоминанием роли."""
        cleaned = value.replace("<@&", "").replace(">", "")
        return cleaned.isdigit() and (value.startswith("<@&") or len(cleaned) >= 17)

    @commands.command(name="pm", ignore_extra=True)
    async def pm(self, ctx, target_id: str = None, *, text: str = None):
        """
        Отправить личное сообщение пользователю или всем с ролью.
        !pm <user_id/role_id> <текст>
        Только для OWNER_ID.
        """
        if ctx.author.id != OWNER_ID:
            await ctx.message.delete()
            return

        if not target_id or (not text and not ctx.message.attachments):
            await ctx.message.add_reaction("❌")
            await ctx.send("❗ Использование: !pm <user_id/role_id> <текст или вложение>", delete_after=5)
            await delete_after(ctx.message)
            return

        # Чистим ID от ментьонов
        cleaned_id = target_id.replace("<@&", "").replace("<@", "").replace(">", "").replace("!", "")
        try:
            target_int = int(cleaned_id)
        except Exception:
            await ctx.message.add_reaction("❌")
            await ctx.send("❗ Некорректный ID.", delete_after=5)
            await delete_after(ctx.message)
            return

        # Проверяем, это роль или юзер
        is_role = target_id.startswith("<@&") or (not target_id.startswith("<@") and ctx.guild and ctx.guild.get_role(target_int) is not None)

        if is_role:
            await self._pm_role(ctx, target_int, text)
        else:
            await self._pm_user(ctx, target_int, text)

    async def _pm_user(self, ctx, user_id_int: int, text: str):
        """Отправка ПМ одному юзеру."""
        user = await safe_fetch_user(self.bot, user_id_int)
        if not user:
            await ctx.message.add_reaction("❌")
            await ctx.send("❗ Пользователь не найден.", delete_after=5)
            await delete_after(ctx.message)
            return
        try:
            files = [await a.to_file() for a in ctx.message.attachments]
            await user.send(text, files=files if files else None)
            await ctx.message.add_reaction("✅")
        except discord.Forbidden:
            await ctx.message.add_reaction("❌")
        await delete_after(ctx.message)

    async def _pm_role(self, ctx, role_id: int, text: str):
        """Отправка ПМ всем участникам с указанной ролью."""
        if not ctx.guild:
            await ctx.send("❗ Эта команда работает только на сервере.", delete_after=5)
            return

        role = ctx.guild.get_role(role_id)
        if not role:
            await ctx.message.add_reaction("❌")
            await ctx.send("❗ Роль не найдена.", delete_after=5)
            await delete_after(ctx.message)
            return

        members = [m for m in role.members if not m.bot]
        if not members:
            await ctx.message.add_reaction("❌")
            await ctx.send("❗ Нет участников с этой ролью.", delete_after=5)
            await delete_after(ctx.message)
            return

        # Отправляем статус
        status_msg = await ctx.send(f"⏳ Отправка сообщений {len(members)} участникам с ролью **{role.name}**...")

        success = []
        failed = []

        # Download attachments into memory once
        attachment_bytes = []
        for a in ctx.message.attachments:
            try:
                b = await a.read()
                attachment_bytes.append((b, a.filename))
            except Exception:
                pass

        for member in members:
            try:
                files = [discord.File(io.BytesIO(b), filename=name) for b, name in attachment_bytes] if attachment_bytes else None
                await member.send(text, files=files)
                success.append(member)
            except (discord.Forbidden, discord.HTTPException):
                failed.append(member)
            await asyncio.sleep(0.5)

        success_text = ", ".join([m.mention for m in success]) if success else "—"
        failed_text = ", ".join([m.mention for m in failed]) if failed else "—"
        
        if len(success_text) > 1020:
            success_text = success_text[:1000] + "... (обрізано)"
        if len(failed_text) > 1020:
            failed_text = failed_text[:1000] + "... (обрізано)"

        embed = discord.Embed(
            title="📨 Массовая рассылка завершена",
            description=f'Сообщение было отправлено для пользователей с ролью **"{role.name}"**',
            color=0x2ecc71 if not failed else 0xe74c3c
        )
        embed.add_field(name=f"✅ Успешно ({len(success)})", value=success_text, inline=False)
        embed.add_field(name=f"❌ Неуспешно ({len(failed)})", value=failed_text, inline=False)
        embed.set_footer(text=f"Запросил: {ctx.author}", icon_url=ctx.author.display_avatar.url)

        await status_msg.delete()
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(PrivateMessageCog(bot)) 

