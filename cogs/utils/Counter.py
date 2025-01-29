import discord
from discord.ext import commands
from discord import app_commands
import yaml
import re
from Niludetsu.utils.embed import create_embed
from Niludetsu.utils.emojis import EMOJIS
from Niludetsu.utils.decorators import command_cooldown

class Counter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.counter_channels = set()
        self.last_number = {}  # {channel_id: last_number}
        self.load_channels()

    def load_channels(self):
        """Загрузка каналов из конфигурации"""
        try:
            with open('config/config.yaml', 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                if 'counter' in config and 'channels' in config['counter']:
                    self.counter_channels = set(config['counter']['channels'])
                    for channel_id in self.counter_channels:
                        self.last_number[channel_id] = 0
        except Exception as e:
            print(f"❌ Ошибка при загрузке каналов счетчика: {e}")

    def save_channels(self):
        """Сохранение каналов в конфигурацию"""
        try:
            with open('config/config.yaml', 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if 'counter' not in config:
                config['counter'] = {}
            
            config['counter']['channels'] = list(self.counter_channels)
            
            with open('config/config.yaml', 'w', encoding='utf-8') as f:
                yaml.dump(config, f, indent=4)
        except Exception as e:
            print(f"❌ Ошибка при сохранении каналов счетчика: {e}")

    def evaluate_expression(self, expression: str) -> int:
        """Вычисление математического выражения"""
        try:
            # Удаляем все пробелы и проверяем на безопасность
            expression = expression.replace(' ', '')
            if not re.match(r'^[\d\+\-\*\/\(\)]*$', expression):
                return None
            
            result = eval(expression)
            if isinstance(result, (int, float)):
                return int(result)
            return None
        except:
            return None

    @app_commands.command(name="counter", description="Включить/выключить режим счетчика в канале")
    @app_commands.checks.has_permissions(administrator=True)
    @command_cooldown()
    async def counter(self, interaction: discord.Interaction):
        try:
            channel_id = interaction.channel.id
            
            if channel_id in self.counter_channels:
                self.counter_channels.remove(channel_id)
                if channel_id in self.last_number:
                    del self.last_number[channel_id]
                
                await interaction.response.send_message(
                    embed=create_embed(
                        title=f"{EMOJIS['SUCCESS']} Счетчик отключен",
                        description="Режим счетчика был отключен в этом канале.",
                        color="GREEN"
                    )
                )
            else:
                self.counter_channels.add(channel_id)
                self.last_number[channel_id] = 0
                
                await interaction.response.send_message(
                    embed=create_embed(
                        title=f"{EMOJIS['SUCCESS']} Счетчик включен",
                        description=(
                            "Режим счетчика активирован в этом канале.\n\n"
                            "**Правила:**\n"
                            "• Каждое следующее число должно быть на 1 больше предыдущего\n"
                            "• Можно использовать математические выражения (например: 5+5=10)\n"
                            "• Неправильные числа будут автоматически удалены\n"
                            "• Начинаем с 1!"
                        ),
                        color="GREEN"
                    )
                )
            
            self.save_channels()
            
        except Exception as e:
            await interaction.response.send_message(
                embed=create_embed(
                    title=f"{EMOJIS['ERROR']} Ошибка",
                    description=f"Произошла ошибка: {str(e)}",
                    color="RED"
                ),
                ephemeral=True
            )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.channel.id not in self.counter_channels:
            return

        try:
            # Проверяем, является ли сообщение числом или математическим выражением
            content = message.content.strip()
            
            # Пытаемся вычислить значение
            number = self.evaluate_expression(content)
            
            if number is None:
                await message.delete()
                return
            
            expected_number = self.last_number[message.channel.id] + 1
            
            if number != expected_number:
                await message.delete()
                return
            
            # Обновляем последнее число
            self.last_number[message.channel.id] = number
            
            # Добавляем реакцию
            await message.add_reaction("✅")
            
        except Exception as e:
            print(f"❌ Ошибка при обработке сообщения счетчика: {e}")

async def setup(bot):
    await bot.add_cog(Counter(bot)) 