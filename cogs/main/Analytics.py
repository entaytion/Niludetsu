import discord, psutil, platform, typing, io, time
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
from collections import Counter
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from Niludetsu import BotAnalytics, ServerAnalytics, RolesAnalytics, ChannelsAnalytics, MessageAnalytics, Embed, Emojis

# Добавляем кастомный шрифт
plt.rcParams['font.family'] = 'sans-serif'
custom_font = fm.FontProperties(fname='data/fonts/TTNormsPro-Bold.ttf')

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
        self.bot_analytics = BotAnalytics(bot)
        self.server_analytics = ServerAnalytics(bot)
        self.roles_analytics = RolesAnalytics(bot)
        self.channels_analytics = ChannelsAnalytics(bot)
        self.message_analytics = MessageAnalytics(bot)
        
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
        fig.tight_layout()
        
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
        embed, file = await self.server_analytics.generate_analytics(guild)
        
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

        embed = await self.bot_analytics.generate_analytics(ctx)
        
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

        guild = ctx.guild if not is_interaction else ctx.guild
        embed, file = await self.roles_analytics.generate_analytics(guild)
        
        if is_interaction:
            await ctx.followup.send(embed=embed, file=file)
        else:
            await ctx.send(embed=embed, file=file)
    
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

        guild = ctx.guild if not is_interaction else ctx.guild
        embed, file = await self.channels_analytics.generate_analytics(guild)
        
        if is_interaction:
            await ctx.followup.send(embed=embed, file=file)
        else:
            await ctx.send(embed=embed, file=file)

    # Команда с префиксом для message_analytics
    @commands.command(name="amessages", description="Показать аналитику сообщений")
    async def messages_prefix(self, ctx):
        """Показывает аналитику сообщений сервера (команда с префиксом)"""
        await self._show_message_analytics(ctx)

    @analytics_group.command(name="messages", description="Показать аналитику сообщений")
    async def messages_slash(self, interaction: discord.Interaction):
        """Показывает аналитику сообщений сервера (слэш-команда)"""
        await self._show_message_analytics(interaction)

    async def _show_message_analytics(self, ctx):
        """Общая логика для показа аналитики сообщений"""
        is_interaction = isinstance(ctx, discord.Interaction)
        if is_interaction:
            await ctx.response.defer()
        else:
            await ctx.defer()

        guild = ctx.guild if not is_interaction else ctx.guild
        embed, file = await self.message_analytics.generate_analytics(guild)
        
        if is_interaction:
            await ctx.followup.send(embed=embed, file=file)
        else:
            await ctx.send(embed=embed, file=file)

async def setup(bot):
    await bot.add_cog(Analytics(bot)) 