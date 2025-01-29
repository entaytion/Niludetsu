# --- Импорт библиотек ---
from pypresence import Presence
import time
import discord
from discord.ext import commands
import os
import yaml
import asyncio
import traceback
from typing import Union
# --- Импорты из Niludetsu ---
from Niludetsu.utils.cog_loader import cog_loader
from Niludetsu.utils.config_loader import bot_state
from Niludetsu.utils.command_sync import CommandSync
from Niludetsu.utils.embed import create_embed
from Niludetsu.utils.database import create_tables
from Niludetsu.core.server_checker import ServerChecker
from Niludetsu.core.level_system import LevelSystem

# --- Discord Bot setup ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# --- Загрузка конфигурации ---
with open('config/config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# RPC (Rich Presence) setup
client_id = config['bot']['client_id']
rpc = None

# Инициализируем системные компоненты
command_sync = CommandSync(bot)
server_checker = None
level_system = None

# --- RPC (Rich Presence) ---
async def update_presence():
    global rpc
    try:
        rpc = Presence(client_id)
        await asyncio.to_thread(rpc.connect)
        start_time = time.time()
        await asyncio.to_thread(
            rpc.update,
            state="Creating a Discord bot!",
            details="In development...",
            start=start_time,
            large_image="bot_icon",
            large_text="Bot in action!",
            buttons=[
                {"label": "Server", "url": "https://discord.gg/HxwZ6ceKKj"},
                {"label": "Site", "url": "https://niludetsu.vercel.app"},
            ],
        )
        print("✅ Rich Presence активирован!")
    except Exception as e:
        print(f"❌ Ошибка при активации Rich Presence: {e}")
        traceback.print_exc()

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

            error_embed = discord.Embed(
                title="🚫 Ошибка команды",
                description=f"```py\n{str(error.__class__.__name__)}: {str(error)}\n```",
                color=discord.Color.red(),
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
    """Обработчик ошибок обычных команд"""
    try:
        # Отправляем сообщение пользователю
        error_message = "Произошла ошибка при выполнении команды!"
        
        # Если это пользовательская ошибка, показываем её текст
        if isinstance(error, commands.UserInputError):
            error_message = str(error)
        
        error_embed = discord.Embed(
            description=error_message,
            color=discord.Color.red()
        )
        await ctx.send(embed=error_embed, delete_after=10)
        
        # Логируем ошибку
        await log_command_error(ctx, error)
        
    except Exception as e:
        print(f"❌ Ошибка при обработке ошибки: {e}")
        traceback.print_exc()

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: commands.CommandError):
    """Обработчик ошибок slash-команд"""
    try:
        # Отправляем сообщение пользователю
        error_message = "Произошла ошибка при выполнении команды!"
        
        # Если это пользовательская ошибка, показываем её текст
        if isinstance(error, commands.UserInputError):
            error_message = str(error)
        
        error_embed = discord.Embed(
            description=error_message,
            color=discord.Color.red()
        )
        
        if not interaction.response.is_done():
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
        else:
            await interaction.followup.send(embed=error_embed, ephemeral=True)
        
        # Логируем ошибку
        await log_command_error(interaction, error)
        
    except Exception as e:
        print(f"❌ Ошибка при обработке ошибки: {e}")
        traceback.print_exc()

# --- Создание файлов по умолчанию ---
async def create_default_files():
    try:
        if not os.path.exists('config'):
            os.makedirs('config')
            
        if not os.path.exists('config/database.db'):
            open('config/database.db', 'w').close()
            
        if not os.path.exists('config/hash.yaml'):
            with open('config/hash.yaml', 'w', encoding='utf-8') as f:
                yaml.dump({}, f)

        if not os.path.exists('config/config.yaml'):
            from Niludetsu.utils.default_config import default_config
            with open('config/config.yaml', 'w', encoding='utf-8') as f:
                yaml.dump(default_config, f, allow_unicode=True)
    except Exception as e:
        print(f"❌ Ошибка при создании файлов: {e}")
        traceback.print_exc()

# --- Основные события ---
@bot.event
async def setup_hook():
    try:
        global server_checker, level_system
        bot_state.reset()
        await create_default_files()
        create_tables()  # Создаем/обновляем таблицы
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
        await update_presence() 
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

bot.run(config['bot']['main_token'])

# --- Запуск ботов параллельно ---
# --- Unreleased ---
""" async def run_bots():
    client = commands.Bot(command_prefix='!', intents=discord.Intents.all())
    client2 = commands.Bot(command_prefix='.', intents=discord.Intents.all())
    
    try:
        await asyncio.gather(
            client.start(config['bot']['main_token']),
            client2.start(config['bot']['voice_token'])
        )
    except KeyboardInterrupt:
        await client.close()
        await client2.close()

if __name__ == '__main__':
    asyncio.run(run_bots()) """