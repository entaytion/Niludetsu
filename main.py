# --- Импорт библиотек ---
import time, os, discord, yaml, asyncio, traceback, discord
from dotenv import load_dotenv
from discord.ext import commands
from typing import Union
# --- Импорты из Niludetsu ---
from Niludetsu import CogLoader, BotState, CommandSync, Embed, Database, LevelSystem
load_dotenv()
token = os.getenv("MAIN_TOKEN")

# --- Discord Bot setup ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
print("✅ Discord интенты настроены")

# --- Загрузка конфигурации ---
async def load_config():
    try:
        db = Database()
        config = await db.fetch_all("SELECT category, key, value FROM settings")
        config_dict = {}
        for row in config:
            if row['category'] not in config_dict:
                config_dict[row['category']] = {}
            config_dict[row['category']][row['key']] = row['value']
        return config_dict
    except Exception as e:
        print(f"❌ Ошибка при загрузке конфигурации из базы данных: {e}")
        raise

try:
    config = asyncio.run(load_config())
    print("✅ Конфигурация успешно загружена из базы данных")
except Exception as e:
    print(f"❌ Ошибка при загрузке конфигурации из базы данных: {e}")
    raise

# Инициализируем системные компоненты
try:
    command_sync = CommandSync(bot)
    server_checker = None
    level_system = None
except Exception as e:
    print(f"❌ Ошибка при инициализации системных компонентов: {e}")
    raise

# --- Загрузка когов ---
async def load_cogs():
    loaded_count = 0
    error_count = 0
    
    for folder in os.listdir("cogs"):
        if os.path.isdir(f"cogs/{folder}"):
            for filename in os.listdir(f"cogs/{folder}"):
                if filename.endswith(".py"):
                    cog_path = f"{folder}/{filename[:-3]}"
                    try:
                        await bot.load_extension(f"cogs.{folder}.{filename[:-3]}")
                        CogLoader.add_loaded_cog(cog_path, success=True)
                        loaded_count += 1
                    except Exception as e:
                        error_msg = str(e)
                        print(f"❌ Ошибка при загрузке кога {cog_path}: {error_msg}")
                        traceback.print_exc()
                        CogLoader.add_loaded_cog(cog_path, success=False, error=error_msg)
                        error_count += 1
                        
    print(f"📊 Загрузка когов завершена. Успешно: {loaded_count}, Ошибок: {error_count}")

# --- Обработчик ошибок ---
async def log_command_error(ctx_or_interaction: Union[commands.Context, discord.Interaction], error: commands.CommandError):
    """Логирование ошибок команд бота"""
    try:
        log_channel = bot.get_channel(int(config['logging']['main_channel']))
        if log_channel:
            # Определяем тип контекста и получаем нужные данные
            if isinstance(ctx_or_interaction, discord.Interaction):
                user = ctx_or_interaction.user
                channel = ctx_or_interaction.channel
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

            error_text = f"{str(error.__class__.__name__)}: {str(error)}"
            print(f"❌ Ошибка в команде {command_name}: {error_text}")

            error_embed = Embed.error(
                description=f"```py\n{error_text}\n```",
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
        BotState.reset()
        db = Database()
        await db.init()
        bot.db = db
        await load_cogs()
        level_system = LevelSystem(bot)
        
    except Exception as e:
        print(f"❌ Критическая ошибка в setup_hook: {e}")
        traceback.print_exc()
        raise

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
        print("🔄 Синхронизация команд...")
        await command_sync.sync_commands()
        print("✅ Команды успешно синхронизированы")
        CogLoader.print_loaded_cogs()
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
        traceback.print_exc()

@bot.event
async def on_error(event, *args, **kwargs):
    """Глобальный обработчик ошибок"""
    print(f"❌ Ошибка в событии {event}: {traceback.format_exc()}")

if __name__ == "__main__":
    try:
        print("🔄 Запуск бота...")
        bot.run(token)
    except Exception as e:
        print(f"❌ Критическая ошибка при запуске бота: {e}")
        raise