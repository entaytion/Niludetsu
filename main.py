import discord
from discord import app_commands
from discord.ext import commands
import os
import importlib
import json
import asyncio

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# Загружаем конфигурацию
with open('config/config.json', 'r') as f:
    config = json.load(f)

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
                
    if not os.path.exists('config/config.json'):
        default_config = {
            "TOKEN": "YOUR_BOT_TOKEN_HERE",
            "WEATHER_API_KEY": "YOUR_WEATHER_API_KEY_HERE",
            "DETECT_LANG_API_KEY": "YOUR_DETECT_LANG_API_KEY_HERE",
            "LAVALINK": {
                "host": "localhost",
                "port": 2333,
                "password": "youshallnotpass",
                "region": "europe"
            },
            "LOG_CHANNEL_ID": "ID",
            "MOD_ROLE_ID": "ID",
            "VOICE_CHANNEL_ID": "ID",
            "VOICE_CHAT_ID": "ID",
            "MESSAGE_VOICE_CHAT_ID": "ID",
            "TICKET_SYSTEM": {
                "CATEGORY_ID": "ID",
                "SUPPORT_ROLE_ID": "ID",
                "LOGS_CHANNEL_ID": "ID",
                "PANEL_CHANNEL_ID": "ID",
                "PANEL_MESSAGE_ID": "ID"
            },
            "FORM_MESSAGE_ID": "ID",
            "APPLICATIONS_CHANNEL_ID": "ID",
            "IDEAS_CHANNEL_ID": "ID",
            "COMPLAINTS_CHANNEL_ID": "ID",
            "IDEAS_MESSAGE_ID": "ID",
            "COMPLAINTS_MESSAGE_ID": "ID"
        }
        with open('config/config.json', 'w') as f:
            json.dump(default_config, f, indent=4)

# Добавляем глобальный обработчик ошибок
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    # Получаем экземпляр логгера
    logs_cog = bot.get_cog('Logs')
    if logs_cog:
        await logs_cog.on_app_command_error(interaction, error)
    else:
        # Если логгер не найден, просто отправляем сообщение об ошибке
        await interaction.response.send_message("Произошла ошибка при выполнении команды!", ephemeral=True)

@bot.event
async def setup_hook():
    await create_default_files()
    await load_cogs()

bot.run(config['TOKEN'])