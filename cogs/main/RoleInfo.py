import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from typing import Optional
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.constants import Emojis

class RoleInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="roleinfo", description="Получить детальную информацию о роли")
    @app_commands.describe(role="Роль, о которой вы хотите узнать информацию")
    async def roleinfo(self, interaction: discord.Interaction, role: discord.Role):
        # Создаем базовый эмбед
        embed=Embed(
            title=f"Информация о роли {role.name}",
            color=role.color.value if role.color != discord.Color.default() else 0x2b2d31
        )

        # Базовая информация
        embed.add_field(
            name="📋 Основная информация",
            value=f"{Emojis.DOT} **Название:** {role.name}\n"
                  f"{Emojis.DOT} **ID:** {role.id}\n"
                  f"{Emojis.DOT} **Цвет:** {str(role.color)}\n"
                  f"{Emojis.DOT} **Позиция:** {role.position} из {len(interaction.guild.roles)}\n"
                  f"{Emojis.DOT} **Создана:** <t:{int(role.created_at.timestamp())}:R>\n"
                  f"{Emojis.DOT} **Отображается отдельно:** {':white_check_mark:' if role.hoist else ':x:'}\n"
                  f"{Emojis.DOT} **Управляется ботом:** {':white_check_mark:' if role.is_bot_managed() else ':x:'}\n"
                  f"{Emojis.DOT} **Интеграция:** {':white_check_mark:' if role.is_integration() else ':x:'}\n"
                  f"{Emojis.DOT} **Премиум роль:** {':white_check_mark:' if role.is_premium_subscriber() else ':x:'}",
            inline=False
        )

        # Количество участников
        members_with_role = len(role.members)
        online_members = len([m for m in role.members if m.status != discord.Status.offline])
        
        embed.add_field(
            name="👥 Участники",
            value=f"{Emojis.DOT} **Всего:** {members_with_role}\n"
                  f"{Emojis.DOT} **Онлайн:** {online_members}\n"
                  f"{Emojis.DOT} **Процент от сервера:** {round((members_with_role / len(interaction.guild.members)) * 100, 2)}%",
            inline=False
        )

        # Разрешения
        permissions = []
        for perm, value in role.permissions:
            if value:
                formatted_perm = perm.replace('_', ' ').title()
                permissions.append(f"{Emojis.SUCCESS} {formatted_perm}")
        
        # Разделяем разрешения на группы по 15
        perm_chunks = [permissions[i:i + 15] for i in range(0, len(permissions), 15)]
        
        for i, chunk in enumerate(perm_chunks, 1):
            embed.add_field(
                name=f"🔒 Разрешения (Часть {i})",
                value='\n'.join(chunk) if chunk else "Нет разрешений",
                inline=False
            )

        # Упоминание и тег
        embed.add_field(
            name="💬 Упоминание",
            value=f"{Emojis.DOT} **Можно упоминать:** {':white_check_mark:' if role.mentionable else ':x:'}\n"
                  f"{Emojis.DOT} **Упоминание:** {role.mention}",
            inline=False
        )

        # Добавляем иконку роли и футер
        if role.icon:
            embed.set_thumbnail(url=role.icon.url)
            
        embed.set_footer(
            text=f"Запросил {interaction.user.name}",
            icon_url=interaction.user.display_avatar.url
        )

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(RoleInfo(bot))