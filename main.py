import discord
from discord import app_commands
from discord.ext import commands
import os
import importlib
import yaml
import asyncio

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# Загружаем конфигурацию
with open('config/config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

async def load_cogs():
    for folder in os.listdir("cogs"):
        if os.path.isdir(f"cogs/{folder}"):
            for filename in os.listdir(f"cogs/{folder}"):
                if filename.endswith(".py"):
                    try:
                        await bot.load_extension(f"cogs.{folder}.{filename[:-3]}")
                        print(f"✅ Загружено расширение cogs: {folder}/{filename[:-3]}")
                    except Exception as e:
                        print(f"❌ Ошибка при загрузке расширения: {folder}/{filename[:-3]}: {str(e)}")

@bot.event
async def on_ready():
    print(f"✅ Бот {bot.user} успешно запущен!")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Синхронизировано {len(synced)} команд")
    except Exception as e:
        print(f"❌ Ошибка при синхронизации команд: {e}")

async def create_default_files():
    if not os.path.exists('config'):
        os.makedirs('config')
        
    if not os.path.exists('config/database.db'):
        open('config/database.db', 'w').close()

# Добавляем глобальный обработчик ошибок
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    # Получаем экземпляр логгера
    logs_cog = bot.get_cog('Logs')
    if logs_cog:
        await logs_cog.on_app_command_error(interaction, error)
    else:
        # Если логгер не найден, просто отправляем сообщение об ошибке
        await interaction.response.send_message("Произошла ошибка при выполнении команды!")

@bot.event
async def setup_hook():
    await create_default_files()
    await load_cogs()

bot.run(config['bot']['token'])