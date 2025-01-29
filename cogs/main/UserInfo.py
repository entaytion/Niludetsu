import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu.utils.embed import create_embed
from Niludetsu.core.base import EMOJIS
from datetime import datetime
import humanize
import pytz

def format_date(date):
    if date is None:
        return "Недоступно"
    # Переводим в московское время
    moscow_tz = pytz.timezone('Europe/Moscow')
    date = date.astimezone(moscow_tz)
    # Форматируем дату
    return f"<t:{int(date.timestamp())}:F> (<t:{int(date.timestamp())}:R>)"

def get_member_status(member):
    status_emoji = {
        discord.Status.online: "🟢 В сети",
        discord.Status.idle: "🟡 Неактивен",
        discord.Status.dnd: "🔴 Не беспокоить",
        discord.Status.offline: "⚫ Не в сети"
    }
    return status_emoji.get(member.status, "❓ Неизвестно")

def get_user_badges(user):
    badges = []
    flags = user.public_flags
    
    if user.bot:
        badges.append("🤖 Бот")
    if flags.staff:
        badges.append("👨‍💼 Сотрудник Discord")
    if flags.partner:
        badges.append("🤝 Партнер")
    if flags.hypesquad:
        badges.append("💠 HypeSquad Events")
    if flags.bug_hunter:
        badges.append("🐛 Охотник за багами")
    if flags.bug_hunter_level_2:
        badges.append("🐛 Охотник за багами 2 уровня")
    if flags.hypesquad_bravery:
        badges.append("<:discord_bravery:1332429970668257311> Bravery")
    if flags.hypesquad_brilliance:
        badges.append("<:discord_brillance:1332429912782540852> Brilliance") 
    if flags.hypesquad_balance:
        badges.append("<:discord_balance:1332429979622965248> Balance")
    if flags.early_supporter:
        badges.append("👑 Ранний поддержавший")
    if flags.verified_bot_developer:
        badges.append("👨‍💻 Разработчик ботов")
    if flags.active_developer:
        badges.append("👨‍💻 Активный разработчик")
    if flags.system:
        badges.append("⚙️ Система Discord")
    if flags.team_user:
        badges.append("👥 Участник команды")
    if flags.verified_bot:
        badges.append("✅ Проверенный бот")
    
    return badges if badges else ["Нет значков"]

def get_member_activities(member):
    if not member or not member.activities:
        return None
    
    activities = []
    for activity in member.activities:
        if activity.type == discord.ActivityType.playing:
            details = getattr(activity, 'details', None)
            state = getattr(activity, 'state', None)
            activity_info = f"🎮 Играет в {activity.name}"
            if details:
                activity_info += f"\n└ {details}"
            if state:
                activity_info += f"\n└ {state}"
            activities.append(activity_info)
        elif activity.type == discord.ActivityType.streaming:
            activities.append(f"📺 Стримит {activity.name}\n└ {activity.url}")
        elif activity.type == discord.ActivityType.listening and isinstance(activity, discord.Spotify):
            activities.append(f"🎵 Слушает Spotify\n└ {activity.title} - {activity.artist}\n└ Альбом: {activity.album}")
        elif activity.type == discord.ActivityType.watching:
            activities.append(f"👀 Смотрит {activity.name}")
        elif activity.type == discord.ActivityType.competing:
            activities.append(f"🏆 Соревнуется в {activity.name}")
        elif activity.type == discord.ActivityType.custom:
            if activity.emoji:
                activities.append(f"{activity.emoji} {activity.name}")
            else:
                activities.append(activity.name)
    
    return activities

class UserInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="userinfo", description="Показать информацию о пользователе")
    @app_commands.describe(user="Пользователь, о котором нужна информация")
    async def userinfo(self, interaction: discord.Interaction, user: discord.Member = None):
        await interaction.response.defer()
        
        member = user or interaction.user
        
        # Получаем роли пользователя
        roles = [role.mention for role in member.roles if role.name != "@everyone"]
        roles.reverse()
        
        # Получаем даты
        created_at = int(member.created_at.timestamp())
        joined_at = int(member.joined_at.timestamp()) if member.joined_at else None
        
        # Получаем статус и активности
        status = get_member_status(member)
        activities = get_member_activities(member)
        badges = get_user_badges(member)
        
        # Создаем эмбед
        embed = create_embed(
            title=f"Информация о пользователе {member.name}",
            color=member.color.value if member.color != discord.Color.default() else 0x2b2d31
        )
        
        # Добавляем основную информацию
        embed.add_field(
            name="📋 Основная информация",
            value=f"{EMOJIS['DOT']} **ID:** {member.id}\n"
                  f"{EMOJIS['DOT']} **Имя:** {member.name}\n"
                  f"{EMOJIS['DOT']} **Никнейм:** {member.display_name}\n"
                  f"{EMOJIS['DOT']} **Бот:** {'Да' if member.bot else 'Нет'}\n"
                  f"{EMOJIS['DOT']} **Создан:** <t:{created_at}:D> (<t:{created_at}:R>)",
            inline=False
        )
        
        # Информация о присоединении к серверу
        if joined_at:
            embed.add_field(
                name="📥 Информация о присоединении",
                value=f"{EMOJIS['DOT']} **Присоединился:** <t:{joined_at}:D> (<t:{joined_at}:R>)\n"
                      f"{EMOJIS['DOT']} **Позиция присоединения:** #{sorted(interaction.guild.members, key=lambda m: m.joined_at or datetime.max).index(member) + 1}",
                inline=False
            )
        
        # Добавляем значки
        if badges:
            embed.add_field(
                name="🏅 Значки",
                value="\n".join(badges),
                inline=False
            )
        
        # Добавляем роли
        if roles:
            embed.add_field(
                name=f"👑 Роли ({len(roles)})",
                value=" ".join(roles) if len(" ".join(roles)) < 1024 else f"Слишком много ролей ({len(roles)})",
                inline=False
            )
        
        # Добавляем статус и активности
        embed.add_field(
            name="📊 Статус",
            value=status,
            inline=True
        )
        
        if activities:
            embed.add_field(
                name="🎮 Активности",
                value="\n\n".join(activities),
                inline=False
            )
        
        # Устанавливаем миниатюру и футер
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(
            text=f"Запросил {interaction.user.name}",
            icon_url=interaction.user.display_avatar.url
        )
        
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(UserInfo(bot))