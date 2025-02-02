import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.constants import Emojis
from datetime import datetime
from typing import Optional

def get_server_level(verification_level):
    levels = {
        discord.VerificationLevel.none: "Отсутствует",
        discord.VerificationLevel.low: "Низкий",
        discord.VerificationLevel.medium: "Средний",
        discord.VerificationLevel.high: "Высокий",
        discord.VerificationLevel.highest: "Очень высокий"
    }
    return levels.get(verification_level, "Неизвестно")

class ServerInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def count_channels(self, guild):
        """Подсчет каналов по категориям"""
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        stage_channels = len(guild.stage_channels)
        forum_channels = len([c for c in guild.channels if isinstance(c, discord.ForumChannel)])
        announcement_channels = len([c for c in guild.text_channels if c.is_news()])
        
        return {
            "text": text_channels,
            "voice": voice_channels,
            "categories": categories,
            "stage": stage_channels,
            "forum": forum_channels,
            "news": announcement_channels,
            "total": text_channels + voice_channels + stage_channels + forum_channels
        }

    def get_member_status(self, guild):
        """Подсчет статусов участников"""
        online = len([m for m in guild.members if m.status == discord.Status.online])
        idle = len([m for m in guild.members if m.status == discord.Status.idle])
        dnd = len([m for m in guild.members if m.status == discord.Status.dnd])
        offline = len([m for m in guild.members if m.status == discord.Status.offline])
        
        return {
            "online": online,
            "idle": idle,
            "dnd": dnd,
            "offline": offline
        }

    @app_commands.command(name="serverinfo", description="Показать информацию о сервере")
    async def serverinfo(self, interaction: discord.Interaction):
        await interaction.response.defer()
        guild = interaction.guild
        
        # Получаем информацию о каналах и участниках
        channels = self.count_channels(guild)
        member_status = self.get_member_status(guild)
        
        # Создаем основной эмбед
        embed=Embed(
            title=f"ℹ️ Информация о сервере {guild.name}",
            description=f"{guild.description if guild.description else 'Описание отсутствует'}",
            color="DEFAULT"
        )

        # Основная информация
        embed.add_field(
            name="📊 Основная информация",
            value=f"""
{Emojis.DOT} **ID сервера**: `{guild.id}`
{Emojis.DOT} **Владелец**: {guild.owner.mention} (`{guild.owner.id}`)
{Emojis.DOT} **Создан**: <t:{int(guild.created_at.timestamp())}:F>
{Emojis.DOT} **Уровень буста**: `{guild.premium_tier} уровень`
{Emojis.DOT} **Бустов**: `{guild.premium_subscription_count}`
{Emojis.DOT} **Уровень проверки**: `{get_server_level(guild.verification_level)}`
{Emojis.DOT} **Регион**: `{str(guild.preferred_locale)}`
            """,
            inline=False
        )

        # Статистика участников
        bots = len([m for m in guild.members if m.bot])
        humans = guild.member_count - bots
        
        embed.add_field(
            name="👥 Участники",
            value=f"""
{Emojis.DOT} **Всего**: `{guild.member_count}`
{Emojis.DOT} **Людей**: `{humans}`
{Emojis.DOT} **Ботов**: `{bots}`
{Emojis.DOT} **Онлайн**: `{member_status['online']}`
{Emojis.DOT} **Не активны**: `{member_status['idle']}`
{Emojis.DOT} **Не беспокоить**: `{member_status['dnd']}`
{Emojis.DOT} **Оффлайн**: `{member_status['offline']}`
            """,
            inline=True
        )

        # Статистика каналов
        embed.add_field(
            name="📝 Каналы",
            value=f"""
{Emojis.DOT} **Всего**: `{channels['total']}`
{Emojis.DOT} **Текстовых**: `{channels['text']}`
{Emojis.DOT} **Голосовых**: `{channels['voice']}`
{Emojis.DOT} **Категорий**: `{channels['categories']}`
{Emojis.DOT} **Трибун**: `{channels['stage']}`
{Emojis.DOT} **Форумов**: `{channels['forum']}`
{Emojis.DOT} **Новостных**: `{channels['news']}`
            """,
            inline=True
        )

        # Безопасность и модерация
        features = [f"`{feature.replace('_', ' ').title()}`" for feature in guild.features]
        embed.add_field(
            name="🛡️ Функции сервера",
            value=f"{', '.join(features) if features else '`Отсутствуют`'}",
            inline=False
        )

        # Эмодзи и стикеры
        emoji_stats = f"{Emojis.DOT} **Обычные**: `{len([e for e in guild.emojis if not e.animated])}/{guild.emoji_limit}`\n"
        emoji_stats += f"{Emojis.DOT} **Анимированные**: `{len([e for e in guild.emojis if e.animated])}/{guild.emoji_limit}`\n"
        emoji_stats += f"{Emojis.DOT} **Стикеры**: `{len(guild.stickers)}/{guild.sticker_limit}`"
        
        embed.add_field(
            name="😀 Эмодзи и стикеры",
            value=emoji_stats,
            inline=False
        )

        # Роли
        roles = [role for role in guild.roles if not role.is_default()]
        roles.reverse()  # Сортируем роли по иерархии
        role_count = len(roles)
        
        if role_count > 0:
            roles_str = " ".join([role.mention for role in roles[:20]])  # Первые 20 ролей
            if role_count > 20:
                roles_str += f"\n*и еще {role_count - 20} ролей...*"
        else:
            roles_str = "`Отсутствуют`"

        embed.add_field(
            name=f"👑 Роли [{role_count}]",
            value=roles_str,
            inline=False
        )

        # Добавляем иконку сервера
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        # Добавляем баннер сервера
        if guild.banner:
            embed.set_image(url=guild.banner.url)

        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ServerInfo(bot)) 