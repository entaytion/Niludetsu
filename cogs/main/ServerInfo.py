import discord
from discord.ext import commands
from discord import app_commands
from utils import create_embed, EMOJIS
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
        try:
            await interaction.response.defer()
            guild = interaction.guild
            
            # Получаем информацию о каналах и участниках
            channels = self.count_channels(guild)
            member_status = self.get_member_status(guild)
            
            # Создаем основной эмбед
            embed = create_embed(
                title=f"ℹ️ Информация о сервере {guild.name}",
                description=f"{guild.description if guild.description else 'Описание отсутствует'}"
            )

            # Основная информация
            embed.add_field(
                name="📊 Основная информация",
                value=f"""
{EMOJIS['DOT']} **ID сервера**: `{guild.id}`
{EMOJIS['DOT']} **Владелец**: {guild.owner.mention} (`{guild.owner.id}`)
{EMOJIS['DOT']} **Создан**: <t:{int(guild.created_at.timestamp())}:F>
{EMOJIS['DOT']} **Уровень буста**: `{guild.premium_tier} уровень`
{EMOJIS['DOT']} **Бустов**: `{guild.premium_subscription_count}`
{EMOJIS['DOT']} **Уровень проверки**: `{get_server_level(guild.verification_level)}`
{EMOJIS['DOT']} **Регион**: `{str(guild.preferred_locale)}`
                """,
                inline=False
            )

            # Статистика участников
            bots = len([m for m in guild.members if m.bot])
            humans = guild.member_count - bots
            
            embed.add_field(
                name="👥 Участники",
                value=f"""
{EMOJIS['DOT']} **Всего**: `{guild.member_count}`
{EMOJIS['DOT']} **Людей**: `{humans}`
{EMOJIS['DOT']} **Ботов**: `{bots}`
{EMOJIS['DOT']} **Онлайн**: `{member_status['online']}`
{EMOJIS['DOT']} **Не активны**: `{member_status['idle']}`
{EMOJIS['DOT']} **Не беспокоить**: `{member_status['dnd']}`
{EMOJIS['DOT']} **Оффлайн**: `{member_status['offline']}`
                """,
                inline=True
            )

            # Статистика каналов
            embed.add_field(
                name="📝 Каналы",
                value=f"""
{EMOJIS['DOT']} **Всего**: `{channels['total']}`
{EMOJIS['DOT']} **Текстовых**: `{channels['text']}`
{EMOJIS['DOT']} **Голосовых**: `{channels['voice']}`
{EMOJIS['DOT']} **Категорий**: `{channels['categories']}`
{EMOJIS['DOT']} **Трибун**: `{channels['stage']}`
{EMOJIS['DOT']} **Форумов**: `{channels['forum']}`
{EMOJIS['DOT']} **Новостных**: `{channels['news']}`
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
            emoji_stats = f"{EMOJIS['DOT']} **Обычные**: `{len([e for e in guild.emojis if not e.animated])}/{guild.emoji_limit}`\n"
            emoji_stats += f"{EMOJIS['DOT']} **Анимированные**: `{len([e for e in guild.emojis if e.animated])}/{guild.emoji_limit}`\n"
            emoji_stats += f"{EMOJIS['DOT']} **Стикеры**: `{len(guild.stickers)}/{guild.sticker_limit}`"
            
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

        except Exception as e:
            await interaction.followup.send(f"❌ Произошла ошибка: {str(e)}")

async def setup(bot):
    await bot.add_cog(ServerInfo(bot)) 