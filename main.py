from pypresence import Presence
import time
import discord
from discord.ext import commands
import os
import yaml
import asyncio
import hashlib

# Discord Bot setup
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# Загружаем конфигурацию
with open('config/config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# RPC (Rich Presence) setup
client_id = config['bot']['client_id']
rpc = None

def load_command_hashes():
    """Загружает хеши команд из файла"""
    try:
        with open('config/hash.yaml', 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}

def save_command_hashes(hashes):
    """Сохраняет хеши команд в файл"""
    with open('config/hash.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(hashes, f, default_flow_style=False, allow_unicode=True)

# Загружаем хеши команд
command_hashes = load_command_hashes()

def get_command_hash(command):
    """Создает стабильный хеш команды на основе её свойств"""
    command_data = [
        command.name,
        command.description,
    ]
    
    # Обработка параметров
    if hasattr(command, 'parameters'):
        params = []
        for param in command.parameters:
            params.append((param.name, str(param.type), getattr(param, 'description', '')))
        command_data.append(str(sorted(params)))
    
    # Обработка choices
    if hasattr(command, 'choices'):
        command_data.append(str(sorted([choice.name for choice in command.choices])))
    
    # Обработка permissions
    if hasattr(command, 'default_permissions'):
        command_data.append(str(command.default_permissions))
    
    return hashlib.md5(str(command_data).encode()).hexdigest()

async def sync_commands():
    """Синхронизирует только измененные команды"""
    try:
        # Получаем текущие команды и их хеши
        current_commands = {cmd.name: get_command_hash(cmd) for cmd in bot.tree.get_commands()}

        # Определяем, какие команды изменились или новые
        commands_to_sync = []
        for name, hash_value in current_commands.items():
            if name not in command_hashes or command_hashes[name] != hash_value:
                commands_to_sync.append(name)
                command_hashes[name] = hash_value

        # Удаляем хеши для удаленных команд
        removed_commands = []
        for name in list(command_hashes.keys()):
            if name not in current_commands:
                del command_hashes[name]
                removed_commands.append(name)

        # Синхронизируем измененные команды
        if commands_to_sync or removed_commands:
            print(f"🔄 Синхронизация измененных команд: {commands_to_sync}")
            await bot.tree.sync()
            save_command_hashes(command_hashes)
            print(f"✅ Синхронизация завершена. Изменено: {len(commands_to_sync)} | Удалено: {len(removed_commands)}")
        else:
            print("✅ Все команды актуальны, синхронизация не требуется.")

    except Exception as e:
        print(f"❌ Ошибка при синхронизации команд: {e}")

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

# Обработчик ошибок
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: commands.CommandError):
    await interaction.response.send_message("Произошла ошибка при выполнении команды!")

async def create_default_files():
    if not os.path.exists('config'):
        os.makedirs('config')
        
    if not os.path.exists('config/database.db'):
        open('config/database.db', 'w').close()
        
    if not os.path.exists('config/hash.yaml'):
        with open('config/hash.yaml', 'w', encoding='utf-8') as f:
            yaml.dump({}, f)

@bot.event
async def setup_hook():
    await create_default_files()
    await load_cogs()

@bot.event
async def on_ready():
    print(f"✅ Бот {bot.user} успешно запущен!")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name="Создаём вайб на Discord!"
        )
    )
    await sync_commands()
    await update_presence()

bot.run(config['bot']['token'])