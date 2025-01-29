import discord
from discord import app_commands
from discord.ext import commands
import psutil
import platform
from datetime import datetime, timedelta
import typing
from collections import Counter
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import io
import time
from Niludetsu.utils.embed import create_embed
from Niludetsu.utils.emojis import EMOJIS

# Добавляем кастомный шрифт
plt.rcParams['font.family'] = 'sans-serif'
custom_font = fm.FontProperties(fname='config/fonts/TTNormsPro-Bold.ttf')

# Настройка стиля для всех графиков
plt.style.use('dark_background')
plt.rcParams['axes.facecolor'] = '#2F3136'
plt.rcParams['figure.facecolor'] = '#2F3136'
plt.rcParams['text.color'] = '#FFFFFF'
plt.rcParams['axes.labelcolor'] = '#FFFFFF'
plt.rcParams['xtick.color'] = '#FFFFFF'
plt.rcParams['ytick.color'] = '#FFFFFF'
plt.rcParams['grid.color'] = '#40444B'

# Цветовая схема
COLORS = {
    'primary': '#ED4245',    # Основной красный цвет Discord
    'secondary': '#FF6B6B',  # Светло-красный
    'accent': '#FF4B4B',     # Акцентный красный
    'background': '#2F3136', # Тёмный фон
    'text': '#FFFFFF',       # Белый текст
    'grid': '#40444B'        # Цвет сетки
}

class FakeInteraction:
    """Класс для эмуляции discord.Interaction при использовании префикс-команд"""
    def __init__(self, ctx):
        self.guild = ctx.guild
        self.channel = ctx.channel
        self.user = ctx.author
        self.response = self
        self.followup = ctx
        self.client = ctx.bot

    async def defer(self):
        pass

    async def send_message(self, *args, **kwargs):
        await self.channel.send(*args, **kwargs)

class Analytics(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()
        
    def get_bot_uptime(self):
        """Получить время работы бота"""
        current_time = time.time()
        difference = int(round(current_time - self.start_time))
        return str(timedelta(seconds=difference))

    def get_system_info(self):
        """Получить информацию о системе"""
        cpu_usage = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "cpu": cpu_usage,
            "memory": memory.percent,
            "disk": disk.percent,
            "python": platform.python_version(),
            "os": f"{platform.system()} {platform.release()}"
        }
        
    def style_plot(self, fig, ax):
        """Применяет единый стиль к графику"""
        fig.patch.set_facecolor(COLORS['background'])
        ax.set_facecolor(COLORS['background'])
        
        # Настройка сетки
        ax.grid(True, linestyle='--', alpha=0.2, color=COLORS['grid'])
        
        # Настройка шрифтов
        for text in ax.get_xticklabels() + ax.get_yticklabels():
            text.set_fontproperties(custom_font)
            text.set_color(COLORS['text'])
        
        # Настройка заголовков
        ax.title.set_fontproperties(custom_font)
        ax.xaxis.label.set_fontproperties(custom_font)
        ax.yaxis.label.set_fontproperties(custom_font)
        
        # Настройка цветов
        ax.spines['bottom'].set_color(COLORS['grid'])
        ax.spines['top'].set_color(COLORS['grid'])
        ax.spines['left'].set_color(COLORS['grid'])
        ax.spines['right'].set_color(COLORS['grid'])
        
        # Настройка отступов
        plt.tight_layout()
        
    analytics_group = app_commands.Group(name="analytics", description="Аналитика сервера и бота")
    
    # Команда с префиксом для server_analytics
    @commands.command(name="aserver", description="Показать подробную аналитику сервера")
    async def server_prefix(self, ctx):
        """Показывает подробную аналитику сервера (команда с префиксом)"""
        await self._show_server_analytics(ctx)

    @analytics_group.command(name="server", description="Показать подробную аналитику сервера")
    async def server_slash(self, interaction: discord.Interaction):
        """Показывает подробную аналитику сервера (слэш-команда)"""
        await self._show_server_analytics(interaction)

    async def _show_server_analytics(self, ctx):
        """Общая логика для показа аналитики сервера"""
        is_interaction = isinstance(ctx, discord.Interaction)
        if is_interaction:
            await ctx.response.defer()
        else:
            await ctx.defer()

        guild = ctx.guild if not is_interaction else ctx.guild
        
        # Основная статистика
        total_members = guild.member_count
        total_humans = len([m for m in guild.members if not m.bot])
        total_bots = len([m for m in guild.members if m.bot])
        
        # Статистика по статусам
        statuses = Counter([member.status for member in guild.members])
        
        # Статистика каналов
        total_channels = len(guild.channels)
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        forum_channels = len([c for c in guild.channels if isinstance(c, discord.ForumChannel)])
        stage_channels = len([c for c in guild.channels if isinstance(c, discord.StageChannel)])
        
        # Статистика ролей
        roles = len(guild.roles) - 1  # Исключаем @everyone
        
        # Статистика эмодзи и стикеров
        emojis = len(guild.emojis)
        animated_emojis = len([e for e in guild.emojis if e.animated])
        static_emojis = emojis - animated_emojis
        stickers = len(guild.stickers)
        
        # Уровень буста
        boost_level = guild.premium_tier
        boost_count = guild.premium_subscription_count
        boosters = len(guild.premium_subscribers)
        
        # Создаем основной эмбед
        embed = create_embed(
            title=f"{EMOJIS['STATS']} Аналитика сервера {guild.name}",
            description=f"{EMOJIS['INFO']} Подробная статистика сервера",
            fields=[
                {
                    "name": f"{EMOJIS['MEMBERS']} Участники",
                    "value": f"{EMOJIS['DOT']} **Всего:** `{total_members}`\n"
                            f"{EMOJIS['DOT']} **Людей:** `{total_humans}`\n"
                            f"{EMOJIS['DOT']} **Ботов:** `{total_bots}`\n"
                            f"{EMOJIS['DOT']} **Онлайн:** `{statuses[discord.Status.online]}`\n"
                            f"{EMOJIS['DOT']} **Не активен:** `{statuses[discord.Status.idle]}`\n"
                            f"{EMOJIS['DOT']} **Не беспокоить:** `{statuses[discord.Status.dnd]}`\n"
                            f"{EMOJIS['DOT']} **Оффлайн:** `{statuses[discord.Status.offline]}`",
                    "inline": True
                },
                {
                    "name": f"{EMOJIS['CHANNELS']} Каналы",
                    "value": f"{EMOJIS['DOT']} **Всего:** `{total_channels}`\n"
                            f"{EMOJIS['DOT']} **Текстовых:** `{text_channels}`\n"
                            f"{EMOJIS['DOT']} **Голосовых:** `{voice_channels}`\n"
                            f"{EMOJIS['DOT']} **Категорий:** `{categories}`\n"
                            f"{EMOJIS['DOT']} **Форумов:** `{forum_channels}`\n"
                            f"{EMOJIS['DOT']} **Трибун:** `{stage_channels}`",
                    "inline": True
                },
                {
                    "name": f"{EMOJIS['FEATURES']} Контент",
                    "value": f"{EMOJIS['DOT']} **Ролей:** `{roles}`\n"
                            f"{EMOJIS['DOT']} **Эмодзи:** `{emojis}`\n"
                            f"{EMOJIS['DOT']} **Анимированных:** `{animated_emojis}`\n"
                            f"{EMOJIS['DOT']} **Статичных:** `{static_emojis}`\n"
                            f"{EMOJIS['DOT']} **Стикеров:** `{stickers}`",
                    "inline": True
                },
                {
                    "name": f"{EMOJIS['BOOST']} Буст статус",
                    "value": f"{EMOJIS['DOT']} **Уровень:** `{boost_level}`\n"
                            f"{EMOJIS['DOT']} **Бустов:** `{boost_count}`\n"
                            f"{EMOJIS['DOT']} **Бустеров:** `{boosters}`\n"
                            f"{EMOJIS['DOT']} **До следующего уровня:** `{2 if boost_level == 0 else (7 if boost_level == 1 else (14 if boost_level == 2 else 0)) - boost_count if boost_level < 3 else 0} бустов`",
                    "inline": True
                },
                {
                    "name": f"{EMOJIS['SHIELD']} Безопасность",
                    "value": f"{EMOJIS['DOT']} **Уровень проверки:** `{guild.verification_level}`\n"
                            f"{EMOJIS['DOT']} **Фильтр контента:** `{guild.explicit_content_filter}`\n"
                            f"{EMOJIS['DOT']} **2FA для модерации:** `{'Включено' if guild.mfa_level else 'Выключено'}`\n"
                            f"{EMOJIS['DOT']} **Уровень NSFW:** `{guild.nsfw_level}`",
                    "inline": True
                },
                {
                    "name": f"{EMOJIS['SETTINGS']} Дополнительно",
                    "value": f"{EMOJIS['DOT']} **Владелец:** {guild.owner.mention}\n"
                            f"{EMOJIS['DOT']} **Регион:** `{str(guild.preferred_locale)}`\n"
                            f"{EMOJIS['DOT']} **Максимум участников:** `{guild.max_members}`\n"
                            f"{EMOJIS['DOT']} **Лимит файлов:** `{guild.filesize_limit // 1048576}MB`",
                    "inline": True
                }
            ],
            color="DEFAULT"
        )
        
        # Создаем график активности по дням недели
        fig, ax = plt.subplots(figsize=(10, 5))
        
        days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        member_joins = [0] * 7
        
        for member in guild.members:
            if member.joined_at:
                day = member.joined_at.weekday()
                member_joins[day] += 1
        
        bars = ax.bar(days, member_joins, color=COLORS['primary'])
        
        # Добавляем значения над столбцами
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}',
                   ha='center', va='bottom',
                   color=COLORS['text'],
                   fontproperties=custom_font)
        
        ax.set_title('Статистика присоединений по дням недели')
        ax.set_xlabel('День недели')
        ax.set_ylabel('Количество участников')
        
        self.style_plot(fig, ax)
        
        # Сохраняем график
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', transparent=True, dpi=300, bbox_inches='tight')
        buffer.seek(0)
        plt.close()
        
        # Создаем файл для отправки
        file = discord.File(buffer, filename='analytics.png')
        embed.set_image(url="attachment://analytics.png")
        
        # Добавляем информацию о создании сервера
        embed.set_footer(text=f"ID: {guild.id} • Сервер создан")
        embed.timestamp = guild.created_at
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        if is_interaction:
            await ctx.followup.send(embed=embed, file=file)
        else:
            await ctx.send(embed=embed, file=file)
    
    # Команда с префиксом для bot_analytics
    @commands.command(name="abot", description="Показать статистику бота")
    async def stats_prefix(self, ctx):
        """Показывает статистику бота (команда с префиксом)"""
        await self._show_bot_analytics(ctx)

    @analytics_group.command(name="bot", description="Показать статистику бота")
    async def bot_slash(self, interaction: discord.Interaction):
        """Показывает статистику бота (слэш-команда)"""
        await self._show_bot_analytics(interaction)

    async def _show_bot_analytics(self, ctx):
        """Общая логика для показа статистики бота"""
        is_interaction = isinstance(ctx, discord.Interaction)
        if is_interaction:
            await ctx.response.defer()
        else:
            await ctx.defer()

        # Получаем информацию о системе
        system_info = self.get_system_info()
        
        # Создаем эмбед
        embed = create_embed(
            title=f"{EMOJIS['BOT']} Статистика бота {self.bot.user.name}",
            description=f"{EMOJIS['INFO']} Многофункциональный бот для вашего сервера!"
        )
        
        # Основная статистика
        total_guilds = len(self.bot.guilds)
        total_users = sum(g.member_count for g in self.bot.guilds)
        
        embed.add_field(
            name=f"{EMOJIS['STATS']} Основная информация",
            value=f"{EMOJIS['DOT']} **Серверов:** `{total_guilds}`\n"
                  f"{EMOJIS['DOT']} **Пользователей:** `{total_users}`\n"
                  f"{EMOJIS['DOT']} **Команд:** `{len(self.bot.tree.get_commands())}`\n"
                  f"{EMOJIS['DOT']} **Пинг:** `{round(self.bot.latency * 1000)}ms`\n"
                  f"{EMOJIS['DOT']} **Аптайм:** `{self.get_bot_uptime()}`",
            inline=False
        )
        
        # Системная информация
        embed.add_field(
            name=f"{EMOJIS['PC']} Системная информация",
            value=f"{EMOJIS['DOT']} **ОС:** `{system_info['os']}`\n"
                  f"{EMOJIS['DOT']} **Python:** `{system_info['python']}`\n"
                  f"{EMOJIS['DOT']} **Discord.py:** `{discord.__version__}`\n"
                  f"{EMOJIS['DOT']} **CPU:** `{system_info['cpu']}%`\n"
                  f"{EMOJIS['DOT']} **RAM:** `{system_info['memory']}%`\n"
                  f"{EMOJIS['DOT']} **Диск:** `{system_info['disk']}%`",
            inline=False
        )
        
        # Ссылки
        embed.add_field(
            name=f"{EMOJIS['LINK']} Полезные ссылки",
            value=f"{EMOJIS['DOT']} [Сервер поддержки](https://discord.gg/HxwZ6ceKKj)\n"
                  f"{EMOJIS['DOT']} [GitHub](https://github.com/entaytion/Niludetsu)",
            inline=False
        )
        
        # Добавляем аватар бота
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        
        # Добавляем футер
        embed.set_footer(text=f"ID: {self.bot.user.id} • Создан")
        embed.timestamp = self.bot.user.created_at
        
        if is_interaction:
            await ctx.followup.send(embed=embed)
        else:
            await ctx.send(embed=embed)
    
    # Команда с префиксом для roles_analytics
    @commands.command(name="aroles", description="Показать аналитику ролей")
    async def roles_prefix(self, ctx):
        """Показывает аналитику ролей сервера (команда с префиксом)"""
        await self._show_roles_analytics(ctx)

    @analytics_group.command(name="roles", description="Показать аналитику ролей")
    async def roles_slash(self, interaction: discord.Interaction):
        """Показывает аналитику ролей сервера (слэш-команда)"""
        await self._show_roles_analytics(interaction)

    async def _show_roles_analytics(self, ctx):
        """Общая логика для показа аналитики ролей"""
        is_interaction = isinstance(ctx, discord.Interaction)
        if is_interaction:
            await ctx.response.defer()
        else:
            await ctx.defer()

        guild = ctx.guild
        
        # Собираем статистику по ролям
        role_stats = []
        for role in guild.roles[1:]:  # Пропускаем @everyone
            members_count = len(role.members)
            role_stats.append({
                'name': role.name,
                'members': members_count,
                'color': role.color,
                'hoisted': role.hoist,
                'mentionable': role.mentionable,
                'position': role.position,
                'managed': role.managed,
                'permissions': role.permissions
            })
        
        # Сортируем по количеству участников
        role_stats.sort(key=lambda x: x['members'], reverse=True)
        
        # Создаем график топ-10 ролей
        fig, ax = plt.subplots(figsize=(10, 5))
        
        top_roles = role_stats[:10]
        names = [r['name'] for r in top_roles]
        members = [r['members'] for r in top_roles]
        
        # Создаем градиент цветов от primary до secondary
        colors = [COLORS['primary']] * len(names)
        
        bars = ax.bar(names, members, color=colors)
        
        # Добавляем значения над столбцами
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}',
                   ha='center', va='bottom',
                   color=COLORS['text'],
                   fontproperties=custom_font)
        
        plt.xticks(rotation=45, ha='right')
        ax.set_title('Топ-10 ролей по количеству участников')
        ax.set_xlabel('Роли')
        ax.set_ylabel('Количество участников')
        
        self.style_plot(fig, ax)
        
        # Сохраняем график
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', transparent=True, dpi=300, bbox_inches='tight')
        buffer.seek(0)
        plt.close()
        
        # Создаем эмбед
        embed = create_embed(
            title=f"{EMOJIS['ROLES']} Аналитика ролей {guild.name}",
            description=f"{EMOJIS['INFO']} Подробная статистика ролей сервера"
        )
        
        # Общая статистика
        embed.add_field(
            name=f"{EMOJIS['STATS']} Общая статистика",
            value=f"{EMOJIS['DOT']} **Всего ролей:** `{len(guild.roles) - 1}`\n"
                  f"{EMOJIS['DOT']} **Отображаемых отдельно:** `{len([r for r in guild.roles if r.hoist])}`\n"
                  f"{EMOJIS['DOT']} **Упоминаемых:** `{len([r for r in guild.roles if r.mentionable])}`\n"
                  f"{EMOJIS['DOT']} **Управляемых:** `{len([r for r in guild.roles if r.managed])}`\n"
                  f"{EMOJIS['DOT']} **С цветом:** `{len([r for r in guild.roles if r.color != discord.Color.default()])}`",
            inline=False
        )
        
        # Топ-5 ролей
        top_5_text = "\n".join(f"{EMOJIS['DOT']} {i+1}. {role['name']}: `{role['members']} участников`" 
                              for i, role in enumerate(role_stats[:5]))
        embed.add_field(name=f"{EMOJIS['CROWN']} Топ-5 ролей", value=top_5_text, inline=False)
        
        # Роли с особыми правами
        admin_roles = len([r for r in guild.roles if r.permissions.administrator])
        mod_roles = len([r for r in guild.roles if any([
            r.permissions.kick_members,
            r.permissions.ban_members,
            r.permissions.manage_messages,
            r.permissions.manage_roles
        ])])
        
        embed.add_field(
            name=f"{EMOJIS['SHIELD']} Права доступа",
            value=f"{EMOJIS['DOT']} **Администраторы:** `{admin_roles}`\n"
                  f"{EMOJIS['DOT']} **Модераторы:** `{mod_roles}`",
            inline=False
        )
        
        embed.set_image(url="attachment://roles.png")
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        if is_interaction:
            await ctx.followup.send(embed=embed, file=discord.File(buffer, filename='roles.png'))
        else:
            await ctx.send(embed=embed, file=discord.File(buffer, filename='roles.png'))
    
    # Команда с префиксом для channels_analytics
    @commands.command(name="achannels", description="Показать аналитику каналов")
    async def channels_prefix(self, ctx):
        """Показывает аналитику каналов сервера (команда с префиксом)"""
        await self._show_channels_analytics(ctx)

    @analytics_group.command(name="channels", description="Показать аналитику каналов")
    async def channels_slash(self, interaction: discord.Interaction):
        """Показывает аналитику каналов сервера (слэш-команда)"""
        await self._show_channels_analytics(interaction)

    async def _show_channels_analytics(self, ctx):
        """Общая логика для показа аналитики каналов"""
        is_interaction = isinstance(ctx, discord.Interaction)
        if is_interaction:
            await ctx.response.defer()
        else:
            await ctx.defer()

        guild = ctx.guild
        
        # Собираем статистику по типам каналов
        text_channels = guild.text_channels
        voice_channels = guild.voice_channels
        categories = guild.categories
        forum_channels = [c for c in guild.channels if isinstance(c, discord.ForumChannel)]
        stage_channels = [c for c in guild.channels if isinstance(c, discord.StageChannel)]
        
        # Статистика по правам доступа
        private_text = len([c for c in text_channels if not c.permissions_for(guild.default_role).view_channel])
        private_voice = len([c for c in voice_channels if not c.permissions_for(guild.default_role).view_channel])
        
        # Создаем круговую диаграмму типов каналов
        fig, ax = plt.subplots(figsize=(10, 5))
        
        # Собираем только непустые категории
        channel_data = [
            ('Текстовые', len(text_channels)),
            ('Голосовые', len(voice_channels)),
            ('Форумы', len(forum_channels)),
            ('Трибуны', len(stage_channels)),
            ('Категории', len(categories))
        ]
        
        # Фильтруем только непустые категории
        channel_data = [(name, count) for name, count in channel_data if count > 0]
        
        # Разделяем данные
        channel_types, sizes = zip(*channel_data) if channel_data else ([], [])
        
        # Создаем градиент красных оттенков
        colors = ['#ED4245', '#FF6B6B', '#FF8585', '#FFA3A3', '#FFC1C1'][:len(channel_types)]
        
        # Создаем круговую диаграмму
        wedges, texts, autotexts = ax.pie(
            sizes, 
            labels=channel_types, 
            colors=colors, 
            autopct='%1.1f%%',
            pctdistance=0.85,
            labeldistance=1.1
        )
        
        # Настраиваем шрифты для меток и процентов
        plt.setp(autotexts, size=9, weight="bold")
        plt.setp(texts, size=10, weight="bold")
        
        for text in texts + autotexts:
            text.set_fontproperties(custom_font)
            text.set_color(COLORS['text'])
        
        ax.set_title('Распределение типов каналов')
        
        self.style_plot(fig, ax)
        
        # Сохраняем график
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', transparent=True, dpi=300, bbox_inches='tight')
        buffer.seek(0)
        plt.close()
        
        # Создаем эмбед
        embed = create_embed(
            title=f"{EMOJIS['CHANNELS']} Аналитика каналов {guild.name}",
            description=f"{EMOJIS['INFO']} Подробная статистика каналов сервера"
        )
        
        # Общая статистика
        embed.add_field(
            name=f"{EMOJIS['STATS']} Общая статистика",
            value=f"{EMOJIS['DOT']} **Всего каналов:** `{len(guild.channels)}`\n"
                  f"{EMOJIS['DOT']} **Текстовых:** `{len(text_channels)}`\n"
                  f"{EMOJIS['DOT']} **Голосовых:** `{len(voice_channels)}`\n"
                  f"{EMOJIS['DOT']} **Форумов:** `{len(forum_channels)}`\n"
                  f"{EMOJIS['DOT']} **Трибун:** `{len(stage_channels)}`\n"
                  f"{EMOJIS['DOT']} **Категорий:** `{len(categories)}`",
            inline=True
        )
        
        # Статистика по доступу
        embed.add_field(
            name=f"{EMOJIS['SHIELD']} Приватность",
            value=f"{EMOJIS['DOT']} **Приватных текстовых:** `{private_text}`\n"
                  f"{EMOJIS['DOT']} **Приватных голосовых:** `{private_voice}`\n"
                  f"{EMOJIS['DOT']} **Публичных текстовых:** `{len(text_channels) - private_text}`\n"
                  f"{EMOJIS['DOT']} **Публичных голосовых:** `{len(voice_channels) - private_voice}`",
            inline=True
        )
        
        # Дополнительная статистика
        news_channels = len([c for c in text_channels if c.is_news()])
        nsfw_channels = len([c for c in text_channels if c.is_nsfw()])
        slowmode_channels = len([c for c in text_channels if c.slowmode_delay > 0])
        
        embed.add_field(
            name=f"{EMOJIS['FEATURES']} Дополнительно",
            value=f"{EMOJIS['DOT']} **Новостных каналов:** `{news_channels}`\n"
                  f"{EMOJIS['DOT']} **NSFW каналов:** `{nsfw_channels}`\n"
                  f"{EMOJIS['DOT']} **Слоумод каналов:** `{slowmode_channels}`\n"
                  f"{EMOJIS['DOT']} **Тредов:** `{sum(len(c.threads) for c in text_channels)}`",
            inline=True
        )
        
        embed.set_image(url="attachment://channels.png")
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        if is_interaction:
            await ctx.followup.send(embed=embed, file=discord.File(buffer, filename='channels.png'))
        else:
            await ctx.send(embed=embed, file=discord.File(buffer, filename='channels.png'))

async def setup(bot):
    await bot.add_cog(Analytics(bot)) 