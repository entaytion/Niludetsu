import discord
from discord.ext import commands
from discord import app_commands
from typing import Dict, List, Optional
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.constants import Emojis
from Niludetsu.moderation.automod import AutoModManager

class ViolationsButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.primary,
            label="Нарушения",
            emoji="📊",
            custom_id="violations"
        )
        
    async def callback(self, interaction: discord.Interaction):
        modal = UserSelect()
        await interaction.response.send_modal(modal)

class ClearViolationsButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.danger,
            label="Очистить нарушения",
            emoji="🗑️",
            custom_id="clear_violations"
        )
        
    async def callback(self, interaction: discord.Interaction):
        modal = UserSelect(clear=True)
        await interaction.response.send_modal(modal)

class UserSelect(discord.ui.Modal, title="Выбор пользователя"):
    user_id = discord.ui.TextInput(
        label="ID пользователя",
        placeholder="Введите ID пользователя",
        required=True,
        min_length=17,
        max_length=20
    )
    
    def __init__(self, clear: bool = False):
        super().__init__()
        self.clear = clear
        
    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_id = int(self.user_id.value)
            member = interaction.guild.get_member(user_id)
            
            if not member:
                embed = Embed(
                    title=f"{Emojis.ERROR} Ошибка",
                    description="Пользователь не найден на сервере",
                    color="RED"
                )
                return await interaction.response.send_message(embed=embed, ephemeral=True)
                
            automod = interaction.client.get_cog("AutoMod")
            if not automod:
                embed = Embed(
                    title=f"{Emojis.ERROR} Ошибка",
                    description="Модуль автомодерации не загружен",
                    color="RED"
                )
                return await interaction.response.send_message(embed=embed, ephemeral=True)
                
            manager = AutoModManager(interaction.client)
            
            if self.clear:
                success = await manager.clear_violations(member.id, interaction.guild.id)
                if success:
                    embed = Embed(
                        title=f"{Emojis.SUCCESS} Нарушения очищены",
                        description=f"Все нарушения пользователя {member.mention} были очищены",
                        color="GREEN"
                    )
                else:
                    embed = Embed(
                        title=f"{Emojis.ERROR} Ошибка",
                        description="Не удалось очистить нарушения",
                        color="RED"
                    )
            else:
                violations = await manager.get_violations(member.id, interaction.guild.id)
                embed = manager.create_violations_embed(member, violations, automod.rules)
                
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except ValueError:
            embed = Embed(
                title=f"{Emojis.ERROR} Ошибка",
                description="Неверный формат ID пользователя",
                color="RED"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

class RuleButton(discord.ui.Button):
    def __init__(self, rule_name: str, rule_obj, is_enabled: bool = True):
        super().__init__(
            style=discord.ButtonStyle.green if is_enabled else discord.ButtonStyle.red,
            label=rule_obj.name,
            custom_id=f"rule_{rule_name}"
        )
        self.rule_name = rule_name
        self.rule_obj = rule_obj
        
    async def callback(self, interaction: discord.Interaction):
        view: ConfigView = self.view
        is_enabled = self.style == discord.ButtonStyle.green
        
        manager = AutoModManager(interaction.client)
        if is_enabled:
            success = await manager.add_exception(interaction.channel.id, self.rule_name)
            if success:
                self.style = discord.ButtonStyle.red
        else:
            success = await manager.remove_exception(interaction.channel.id, self.rule_name)
            if success:
                self.style = discord.ButtonStyle.green
                
        if not success:
            embed = Embed(
                title=f"{Emojis.ERROR} Ошибка",
                description="Не удалось обновить настройки правила",
                color="RED"
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
            
        await interaction.response.edit_message(view=self.view)

class ChannelSelect(discord.ui.ChannelSelect):
    def __init__(self):
        super().__init__(
            placeholder="Выберите канал для настройки",
            channel_types=[discord.ChannelType.text]
        )
        
    async def callback(self, interaction: discord.Interaction):
        view: ConfigView = self.view
        channel = self.values[0]
        
        manager = AutoModManager(interaction.client)
        exceptions = await manager.get_channel_exceptions(channel.id)
        
        # Обновляем состояние кнопок для выбранного канала
        for child in view.children:
            if isinstance(child, RuleButton):
                is_enabled = child.rule_name not in exceptions
                child.style = discord.ButtonStyle.green if is_enabled else discord.ButtonStyle.red
        
        embed = Embed(
            title=f"{Emojis.SETTINGS} Настройки автомодерации",
            description=f"Настройка правил для канала {channel.mention}\n\n"
                       f"🟢 - Правило включено\n"
                       f"🔴 - Правило отключено\n\n"
                       f"**Текущие правила:**\n",
            color="BLUE"
        )
        
        # Добавляем описание каждого правила
        for child in view.children:
            if isinstance(child, RuleButton):
                status = "✅ Включено" if child.style == discord.ButtonStyle.green else "❌ Отключено"
                embed.add_field(
                    name=f"{child.label}",
                    value=f"{child.rule_obj.description}\n{status}",
                    inline=False
                )
        
        await interaction.response.edit_message(embed=embed, view=view)

class ConfigView(discord.ui.View):
    def __init__(self, automod):
        super().__init__(timeout=300)
        self.automod = automod
        
        # Добавляем селектор каналов
        self.add_item(ChannelSelect())
        
        # Добавляем кнопки для каждого правила
        for rule_name, rule_obj in automod.rules.items():
            self.add_item(RuleButton(rule_name, rule_obj))
            
        # Добавляем кнопки управления нарушениями
        self.add_item(ViolationsButton())
        self.add_item(ClearViolationsButton())

class AutoModConfig(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(name="automod_settings", aliases=["amconfig"])
    @commands.has_permissions(administrator=True)
    async def automod_config(self, ctx):
        """Настройка автомодерации"""
        automod = self.bot.get_cog("AutoMod")
        if not automod:
            embed = Embed(
                title=f"{Emojis.ERROR} Ошибка",
                description="Модуль автомодерации не загружен",
                color="RED"
            )
            return await ctx.send(embed=embed)
            
        embed = Embed(
            title=f"{Emojis.SETTINGS} Настройка автомодерации",
            description="Выберите канал для настройки правил автомодерации\n\n"
                       "🟢 - Правило включено\n"
                       "🔴 - Правило отключено\n\n"
                       "**Доступные правила:**\n",
            color="BLUE"
        )
        
        # Добавляем описание каждого правила
        for rule_name, rule in automod.rules.items():
            embed.add_field(
                name=rule.name,
                value=rule.description,
                inline=False
            )
        
        view = ConfigView(automod)
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(AutoModConfig(bot)) 