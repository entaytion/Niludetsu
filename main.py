# --- Импорт библиотек ---
import time
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import yaml
import asyncio
import traceback
from typing import Union
# --- Импорты из Niludetsu ---
from Niludetsu.utils.cog_loader import cog_loader
from Niludetsu.utils.config_loader import bot_state
from Niludetsu.utils.command_sync import CommandSync
from Niludetsu.utils.embed import Embed
from Niludetsu.database.db import Database
from Niludetsu.core.server_checker import ServerChecker
from Niludetsu.core.level_system import LevelSystem

# --- Discord Bot setup ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# --- Загрузка конфигурации ---
load_dotenv()  # Загружаем переменные из .env
with open('data/config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# Инициализируем системные компоненты
command_sync = CommandSync(bot)
server_checker = None
level_system = None

# --- Загрузка когов ---
async def load_cogs():
    for folder in os.listdir("cogs"):
        if os.path.isdir(f"cogs/{folder}"):
            for filename in os.listdir(f"cogs/{folder}"):
                if filename.endswith(".py"):
                    cog_path = f"{folder}/{filename[:-3]}"
                    try:
                        await bot.load_extension(f"cogs.{folder}.{filename[:-3]}")
                        cog_loader.add_loaded_cog(cog_path, success=True)
                    except Exception as e:
                        error_msg = str(e)
                        print(f"❌ Ошибка при загрузке кога {cog_path}:")
                        traceback.print_exc()
                        cog_loader.add_loaded_cog(cog_path, success=False, error=error_msg)

# --- Обработчик ошибок и логирование ---
async def log_command_error(ctx_or_interaction: Union[commands.Context, discord.Interaction], error: commands.CommandError):
    """Логирование ошибок команд бота"""
    try:
        log_channel = bot.get_channel(int(config['logging']['main_channel']))
        if log_channel:
            # Определяем тип контекста и получаем нужные данные
            if isinstance(ctx_or_interaction, discord.Interaction):
                user = ctx_or_interaction.user
                channel = ctx_or_interaction.channel
                # Получаем полное имя команды, включая группу
                if ctx_or_interaction.command:
                    if hasattr(ctx_or_interaction.command, 'parent') and ctx_or_interaction.command.parent:
                        command_name = f"/{ctx_or_interaction.command.parent.name} {ctx_or_interaction.command.name}"
                    else:
                        command_name = f"/{ctx_or_interaction.command.name}"
                else:
                    command_name = "/Неизвестно"
            else:
                user = ctx_or_interaction.author
                channel = ctx_or_interaction.channel
                if ctx_or_interaction.command:
                    command_name = f"{ctx_or_interaction.prefix}{ctx_or_interaction.command.qualified_name}"
                else:
                    command_name = f"{ctx_or_interaction.prefix}Неизвестно"

            error_embed = Embed.error(
                description=f"```py\n{str(error.__class__.__name__)}: {str(error)}\n```",
                timestamp=discord.utils.utcnow()
            )
            error_embed.add_field(
                name="Команда", 
                value=f"`{command_name}`", 
                inline=True
            )
            error_embed.add_field(
                name="Пользователь", 
                value=f"{user.mention}\n(`{user.id}`)", 
                inline=True
            )
            error_embed.add_field(
                name="Канал", 
                value=f"{channel.mention}\n(`{channel.id}`)", 
                inline=True
            )
            
            # Всегда добавляем traceback для более подробной информации
            trace = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
            if len(trace) > 1000:
                trace = trace[:997] + "..."
            error_embed.add_field(
                name="Traceback",
                value=f"```py\n{trace}\n```",
                inline=False
            )
            
            # Отправляем пинг создателя и эмбед
            owner_id = config['settings']['owner_id']
            await log_channel.send(f"<@{owner_id}>", embed=error_embed)
            
            # Выводим ошибку в консоль для отладки
            print(f"\n❌ Ошибка в команде {command_name}:")
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ Ошибка при логировании: {e}")
        traceback.print_exc()

@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    if isinstance(error, commands.CommandNotFound):
        return  # Игнорируем ошибку отсутствующей команды
    await log_command_error(ctx, error)

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: commands.CommandError):
    """Обработчик ошибок slash-команд"""
    try:
        # Отправляем сообщение пользователю
        error_message = "Произошла ошибка при выполнении команды!"
        
        # Если это пользовательская ошибка, показываем её текст
        if isinstance(error, commands.UserInputError):
            error_message = str(error)
        
        error_embed = Embed.error(description=error_message)
        
        if not interaction.response.is_done():
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
        else:
            await interaction.followup.send(embed=error_embed, ephemeral=True)
        
        # Логируем ошибку
        await log_command_error(interaction, error)
        
    except Exception as e:
        print(f"❌ Ошибка при обработке ошибки: {e}")
        traceback.print_exc()

# --- Основные события ---
@bot.event
async def setup_hook():
    try:
        global server_checker, level_system
        bot_state.reset()
        
        # Инициализируем базу данных и создаем пул подключений
        db = Database()
        await db.init()
        bot.pool = db.pool
        
        await load_cogs()
        
        # Инициализируем системные компоненты
        server_checker = ServerChecker(bot)
        level_system = LevelSystem(bot)
    except Exception as e:
        print(f"❌ Ошибка в setup_hook: {e}")
        traceback.print_exc()

@bot.event
async def on_ready():
    try:
        print(f"✅ Бот {bot.user} успешно запущен!")
        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name="Создаём вайб на Discord!"
            )
        )
        await command_sync.sync_commands()
        cog_loader.print_loaded_cogs()
    except Exception as e:
        print(f"❌ Ошибка в on_ready: {e}")
        traceback.print_exc()

@bot.event
async def on_message(message):
    try:
        if level_system:
            await level_system.process_message(message)
        await bot.process_commands(message)
    except Exception as e:
        print(f"❌ Ошибка при обработке сообщения: {e}")
        traceback.print_exc()

class HelpView(discord.ui.View):
    def __init__(self, commands_list: list, per_page: int = 10):
        super().__init__(timeout=60)
        self.commands = commands_list
        self.per_page = per_page
        self.current_page = 0
        self.total_pages = len(commands_list) // per_page + (1 if len(commands_list) % per_page else 0)

    def get_current_page_content(self):
        start = self.current_page * self.per_page
        end = start + self.per_page
        return self.commands[start:end]

    @discord.ui.button(label="◀️", style=discord.ButtonStyle.gray)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            await self.update_message(interaction)

    @discord.ui.button(label="▶️", style=discord.ButtonStyle.gray)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            await self.update_message(interaction)

    async def update_message(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Команды с префиксом",
            description=f"Страница {self.current_page + 1}/{self.total_pages}",
            color=discord.Color.blue()
        )
        
        current_page = self.get_current_page_content()
        commands_text = ""
        for cmd, help_text in current_page:
            commands_text += f"`!{cmd}` - {help_text}\n"
        
        embed.add_field(name="Команды", value=commands_text or "Нет доступных команд", inline=False)
        await interaction.response.edit_message(embed=embed, view=self)

@bot.command(name="aehelp")
@commands.is_owner()
async def aehelp(ctx):
    """Показывает все команды с префиксом для создателя бота"""
    # Собираем только команды с префиксом (не слэш-команды)
    prefix_commands = []
    for cmd in bot.commands:
        if not cmd.hidden:  # Пропускаем скрытые команды
            help_text = cmd.help or 'Нет описания'
            prefix_commands.append((cmd.name, help_text))
    
    prefix_commands.sort(key=lambda x: x[0])  # Сортируем по имени команды
    
    if not prefix_commands:
        embed = discord.Embed(
            title="Команды с префиксом",
            description="Нет доступных команд",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
        return

    view = HelpView(prefix_commands)
    
    embed = discord.Embed(
        title="Команды с префиксом",
        description=f"Страница 1/{view.total_pages}",
        color=discord.Color.blue()
    )
    
    current_page = view.get_current_page_content()
    commands_text = ""
    for cmd, help_text in current_page:
        commands_text += f"`!{cmd}` - {help_text}\n"
    
    embed.add_field(name="Команды", value=commands_text, inline=False)
    await ctx.send(embed=embed, view=view)

bot.run(os.getenv('MAIN_TOKEN'))  # Используем токен из .env файла