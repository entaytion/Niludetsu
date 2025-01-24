import discord
from discord.ext import commands
from discord import app_commands
from utils import create_embed
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
    if member is None:
        return "🔴 Не на сервере"
    if member.status == discord.Status.online:
        return "🟢 В сети"
    elif member.status == discord.Status.idle:
        return "🟡 Неактивен"
    elif member.status == discord.Status.dnd:
        return "🔴 Не беспокоить"
    elif member.status == discord.Status.offline:
        return "⚫ Не в сети"
    return "Неизвестно"

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
        badges.append("<:discord_bravery:1332429970668257311> Bravery")  # Замените ID на реальный
    if flags.hypesquad_brilliance:
        badges.append("<:discord_brillance:1332429912782540852> Brilliance")  # Замените ID на реальный
    if flags.hypesquad_balance:
        badges.append("<:discord_balance:1332429979622965248> Balance")  # Замените ID на реальный
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
    @app_commands.describe(
        user="Пользователь, о котором вы хотите узнать информацию"
    )
    async def userinfo(
        self,
        interaction: discord.Interaction,
        user: discord.User = None
    ):
        try:
            await interaction.response.defer()
            
            # Если пользователь не указан, показываем информацию об авторе команды
            target_user = user or interaction.user
            target_member = interaction.guild.get_member(target_user.id)

            # Создаем эмбед
            embed = create_embed(
                title=f"Информация о пользователе {target_user.name}",
                thumbnail_url=target_user.display_avatar.url
            )

            # Основная информация
            embed.add_field(
                name="📋 Основная информация",
                value=(
                    f"**Имя:** {target_user.name}\n"
                    f"**Тег:** {target_user}\n"
                    f"**ID:** {target_user.id}\n"
                    f"**Статус:** {get_member_status(target_member)}\n"
                    f"**Бот:** {'Да' if target_user.bot else 'Нет'}\n"
                    f"**Создан:** {format_date(target_user.created_at)}\n"
                    f"**Баннер:** {'Есть' if target_user.banner else 'Нет'}"
                ),
                inline=False
            )

            # Значки пользователя
            badges = get_user_badges(target_user)
            embed.add_field(
                name="🏅 Значки",
                value="\n".join(badges),
                inline=False
            )

            # Информация о пользователе на сервере (если есть)
            if target_member:
                roles = [role.mention for role in target_member.roles[1:]]  # Исключаем @everyone
                
                member_info = (
                    f"**Никнейм:** {target_member.nick or 'Не установлен'}\n"
                    f"**Присоединился:** {format_date(target_member.joined_at)}\n"
                    f"**Высшая роль:** {target_member.top_role.mention if len(roles) > 0 else 'Нет ролей'}\n"
                    f"**Роли [{len(roles)}]:** {' '.join(roles) if roles else 'Нет ролей'}\n"
                    f"**Буст сервера:** {'Да' if target_member.premium_since else 'Нет'}"
                )
                
                embed.add_field(
                    name="📊 Информация на сервере",
                    value=member_info,
                    inline=False
                )

                # Разрешения пользователя
                key_permissions = []
                permissions = target_member.guild_permissions
                if permissions.administrator:
                    key_permissions.append("👑 Администратор")
                if permissions.manage_guild:
                    key_permissions.append("⚙️ Управление сервером")
                if permissions.ban_members:
                    key_permissions.append("🔨 Бан участников")
                if permissions.kick_members:
                    key_permissions.append("👢 Кик участников")
                if permissions.manage_channels:
                    key_permissions.append("🔧 Управление каналами")
                if permissions.manage_roles:
                    key_permissions.append("📝 Управление ролями")
                
                if key_permissions:
                    embed.add_field(
                        name="🔑 Ключевые разрешения",
                        value="\n".join(key_permissions),
                        inline=False
                    )

                # Активности пользователя
                activities = get_member_activities(target_member)
                if activities:
                    embed.add_field(
                        name="🎯 Активности",
                        value="\n".join(activities),
                        inline=False
                    )

                # Устройство, с которого пользователь сидит
                platforms = []
                if target_member.desktop_status != discord.Status.offline:
                    platforms.append("💻 Компьютер")
                if target_member.mobile_status != discord.Status.offline:
                    platforms.append("📱 Телефон")
                if target_member.web_status != discord.Status.offline:
                    platforms.append("🌐 Браузер")
                
                if platforms:
                    embed.add_field(
                        name="📱 Устройства",
                        value="\n".join(platforms),
                        inline=False
                    )

            # Добавляем футер с временем запроса
            embed.set_footer(text=f"Запрошено {interaction.user.name}")
            embed.timestamp = datetime.now()

            # Отправляем сообщение
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            print(f"Ошибка в команде userinfo: {str(e)}")
            await interaction.followup.send("Произошла ошибка при выполнении команды.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(UserInfo(bot))