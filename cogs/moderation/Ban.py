import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

from Niludetsu import (
    Embed,
    Emojis,
    admin_only,
    cooldown,
    Database,
    Tables
)

class UnbanButton(discord.ui.Button):
    def __init__(self, user_id: int):
        super().__init__(style=discord.ButtonStyle.success, label="Разбанить", emoji="🔓")
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        try:
            user = await interaction.client.fetch_user(self.user_id)
            await interaction.guild.unban(user, reason=f"Разбан от {interaction.user}")
            
            # Создаем запись в базе данных о разбане
            db = Database()
            await db.init()
            
            await db.insert(
                Tables.MODERATION,
                {
                    "user_id": str(self.user_id),
                    "guild_id": str(interaction.guild_id),
                    "moderator_id": str(interaction.user.id),
                    "type": "unban",
                    "reason": f"Разбан через кнопку от {interaction.user}",
                    "active": False
                }
            )
            
            unban_embed = Embed(
                title=f"{Emojis.UNBAN} Пользователь разбанен",
                color="GREEN"
            )
            
            unban_embed.set_thumbnail(url=user.display_avatar.url)
            unban_embed.add_field(
                name=f"{Emojis.USER} Пользователь",
                value=f"{user.mention} ({user})",
                inline=True
            )
            unban_embed.add_field(
                name=f"{Emojis.SHIELD} Модератор",
                value=interaction.user.mention,
                inline=True
            )
            unban_embed.set_footer(text=f"ID пользователя: {user.id}")
            
            await interaction.response.send_message(embed=unban_embed)
            
            try:
                dm_embed = Embed(
                    title=f"{Emojis.UNBAN} Вы были разбанены",
                    color="GREEN"
                )
                dm_embed.add_field(
                    name=f"{Emojis.SERVER} Сервер",
                    value=interaction.guild.name,
                    inline=True
                )
                dm_embed.add_field(
                    name=f"{Emojis.SHIELD} Модератор",
                    value=str(interaction.user),
                    inline=True
                )
                await user.send(embed=dm_embed)
            except discord.Forbidden:
                pass
                
        except discord.NotFound:
            await interaction.response.send_message(
                embed=Embed(
                    title=f"{Emojis.ERROR} Ошибка",
                    description="Пользователь не найден!",
                    color="RED"
                ),
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=Embed(
                    title=f"{Emojis.ERROR} Ошибка прав",
                    description="У меня недостаточно прав для разбана пользователей!",
                    color="RED"
                ),
                ephemeral=True
            )

class BanView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=None)
        self.add_item(UnbanButton(user_id))

class Ban(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = Database()

    async def cog_load(self):
        """Инициализация базы данных при загрузке кога"""
        await self.db.init()

    @app_commands.command(name="ban", description="Забанить пользователя на сервере")
    @app_commands.describe(
        user="Пользователь для бана",
        reason="Причина бана",
        delete_days="Удалить сообщения пользователя за последние X дней (0-7)",
        duration="Длительность бана (например: 1d, 7d, 30d). Оставьте пустым для перманентного"
    )
    @admin_only()
    @cooldown(seconds=5)
    async def ban(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        reason: str = "Причина не указана",
        delete_days: app_commands.Range[int, 0, 7] = 0,
        duration: Optional[str] = None
    ):
        if user.id == interaction.user.id:
            return await interaction.response.send_message(
                embed=Embed(
                    title=f"{Emojis.ERROR} Ошибка",
                    description="Вы не можете забанить самого себя!",
                    color="RED"
                ),
                ephemeral=True
            )

        if user.id == self.bot.user.id:
            return await interaction.response.send_message(
                embed=Embed(
                    title=f"{Emojis.ERROR} Ошибка",
                    description="Я не могу забанить самого себя!",
                    color="RED"
                ),
                ephemeral=True
            )

        if user.top_role >= interaction.user.top_role:
            return await interaction.response.send_message(
                embed=Embed(
                    title=f"{Emojis.ERROR} Ошибка",
                    description="Вы не можете забанить участника с ролью выше или равной вашей!",
                    color="RED"
                ),
                ephemeral=True
            )

        try:
            # Парсим длительность бана
            expires_at = None
            if duration:
                time_units = {"d": 86400, "h": 3600, "m": 60, "s": 1}
                total_seconds = 0
                
                amount = ""
                for char in duration:
                    if char.isdigit():
                        amount += char
                    elif char.lower() in time_units:
                        total_seconds += int(amount) * time_units[char.lower()]
                        amount = ""
                
                if total_seconds > 0:
                    expires_at = (discord.utils.utcnow() + discord.utils.timedelta(seconds=total_seconds)).isoformat()

            # Создаем запись в базе данных
            await self.db.insert(
                Tables.MODERATION,
                {
                    "user_id": str(user.id),
                    "guild_id": str(interaction.guild_id),
                    "moderator_id": str(interaction.user.id),
                    "type": "ban",
                    "reason": reason,
                    "expires_at": expires_at,
                    "active": True
                }
            )
            
            ban_embed = Embed(
                title=f"{Emojis.BAN} Бан пользователя",
                color="RED"
            )
            
            ban_embed.set_thumbnail(url=user.display_avatar.url)
            ban_embed.add_field(
                name=f"{Emojis.USER} Пользователь",
                value=f"{user.mention} ({user})",
                inline=True
            )
            ban_embed.add_field(
                name=f"{Emojis.SHIELD} Модератор",
                value=interaction.user.mention,
                inline=True
            )
            ban_embed.add_field(
                name=f"{Emojis.REASON} Причина",
                value=f"```{reason}```",
                inline=False
            )
            if delete_days > 0:
                ban_embed.add_field(
                    name=f"{Emojis.TIME} Удаление сообщений",
                    value=f"За последние `{delete_days}` дней",
                    inline=False
                )
            if duration:
                ban_embed.add_field(
                    name=f"{Emojis.TIME} Длительность",
                    value=f"`{duration}`",
                    inline=False
                )
            ban_embed.set_footer(text=f"ID пользователя: {user.id}")
            
            try:
                dm_embed = Embed(
                    title=f"{Emojis.BAN} Вы были забанены",
                    color="RED"
                )
                dm_embed.add_field(
                    name=f"{Emojis.SERVER} Сервер",
                    value=interaction.guild.name,
                    inline=True
                )
                dm_embed.add_field(
                    name=f"{Emojis.SHIELD} Модератор",
                    value=str(interaction.user),
                    inline=True
                )
                dm_embed.add_field(
                    name=f"{Emojis.REASON} Причина",
                    value=f"```{reason}```",
                    inline=False
                )
                if duration:
                    dm_embed.add_field(
                        name=f"{Emojis.TIME} Длительность",
                        value=f"`{duration}`",
                        inline=False
                    )
                await user.send(embed=dm_embed)
            except discord.Forbidden:
                pass
            
            await user.ban(reason=reason, delete_message_days=delete_days)
            await interaction.response.send_message(embed=ban_embed, view=BanView(user.id))
            
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=Embed(
                    title=f"{Emojis.ERROR} Ошибка прав",
                    description=f"У меня недостаточно прав для бана {user.mention}!",
                    color="RED"
                )
            )

async def setup(bot: commands.Bot):
    await bot.add_cog(Ban(bot)) 