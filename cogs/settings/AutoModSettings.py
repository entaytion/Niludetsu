import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.constants import Emojis
from Niludetsu.database.db import Database
from typing import Optional

class RuleButton(discord.ui.Button):
    def __init__(self, rule_name: str, is_enabled: bool):
        super().__init__(
            style=discord.ButtonStyle.green if is_enabled else discord.ButtonStyle.red,
            label=f"{'✓' if is_enabled else '✗'} {rule_name}",
            custom_id=f"rule_{rule_name.lower()}"
        )
        self.rule_name = rule_name
        self.is_enabled = is_enabled

    async def callback(self, interaction: discord.Interaction):
        view: AutoModConfigView = self.view
        self.is_enabled = not self.is_enabled
        self.style = discord.ButtonStyle.green if self.is_enabled else discord.ButtonStyle.red
        self.label = f"{'✓' if self.is_enabled else '✗'} {self.rule_name}"
        
        # Обновляем настройки в базе данных
        if not self.is_enabled:
            await view.cog.db.execute(
                """
                INSERT INTO automod_exceptions (channel_id, rule_name)
                VALUES (?, ?)
                """,
                str(view.channel_id), self.rule_name.lower()
            )
        else:
            await view.cog.db.execute(
                """
                DELETE FROM automod_exceptions 
                WHERE channel_id = ? AND rule_name = ?
                """,
                str(view.channel_id), self.rule_name.lower()
            )
        
        await interaction.response.edit_message(view=self.view)

class ChannelSelect(discord.ui.ChannelSelect):
    def __init__(self):
        super().__init__(
            placeholder="Выберите канал для настройки",
            channel_types=[discord.ChannelType.text, discord.ChannelType.forum]
        )

    async def callback(self, interaction: discord.Interaction):
        view: AutoModConfigView = self.view
        view.channel_id = self.values[0].id
        
        # Загружаем исключения для выбранного канала
        exceptions = await view.cog.db.fetch_all(
            "SELECT rule_name FROM automod_exceptions WHERE channel_id = ?",
            str(view.channel_id)
        )
        disabled_rules = [exc['rule_name'] for exc in exceptions]
            
        # Обновляем состояние кнопок
        for child in view.children:
            if isinstance(child, RuleButton):
                child.is_enabled = child.rule_name.lower() not in disabled_rules
                child.style = discord.ButtonStyle.green if child.is_enabled else discord.ButtonStyle.red
                child.label = f"{'✓' if child.is_enabled else '✗'} {child.rule_name}"
        
        await interaction.response.edit_message(
            embed=Embed(
                title=f"{Emojis.SETTINGS} Настройки автомодерации",
                description=f"Настройка правил для канала {self.values[0].mention}\nНажмите на кнопку, чтобы включить/отключить правило",
                color="BLUE"
            ),
            view=view
        )

class AutoModConfigView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=300)
        self.cog = cog
        self.channel_id = None
        
        # Добавляем селектор каналов
        self.add_item(ChannelSelect())
        
        # Добавляем кнопки для каждого правила
        rules = [
            "Спам", "Капс", "Ссылки", "Плохие слова",
            "Спам упоминаний", "Спам эмодзи", "Спам переносов"
        ]
        
        for rule in rules:
            self.add_item(RuleButton(rule, True))

class AutoModSettings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()

    async def automod_settings(self, interaction: discord.Interaction):
        """Открывает меню настроек автомодерации"""
        embed = Embed(
            title=f"{Emojis.SETTINGS} Настройки автомодерации",
            description="Выберите канал для настройки правил автомодерации",
            color="BLUE"
        )
        
        view = AutoModConfigView(self)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(AutoModSettings(bot)) 