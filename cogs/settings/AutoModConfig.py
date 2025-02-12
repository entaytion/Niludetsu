import discord
from discord.ext import commands
from discord import app_commands
from typing import Dict, List, Optional
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.constants import Emojis

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
        
        if is_enabled:
            await view.automod.add_exception(interaction.channel.id, self.rule_name)
            self.style = discord.ButtonStyle.red
        else:
            await view.automod.remove_exception(interaction.channel.id, self.rule_name)
            self.style = discord.ButtonStyle.green
            
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
        
        # Обновляем состояние кнопок для выбранного канала
        for child in view.children:
            if isinstance(child, RuleButton):
                is_enabled = not (channel.id in view.automod.exceptions and 
                                child.rule_name in view.automod.exceptions[channel.id])
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
    def __init__(self, automod, timeout: float = 180):
        super().__init__(timeout=timeout)
        self.automod = automod
        
        # Добавляем селектор каналов
        self.add_item(ChannelSelect())
        
        # Добавляем кнопки для каждого правила
        for rule_name, rule_obj in automod.rules.items():
            self.add_item(RuleButton(rule_name, rule_obj))

class AutoModConfig(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(name="automodconfig", aliases=["amc"])
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
            description="Выберите канал и настройте правила автомодерации\n\n"
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
        
    @commands.command(name="violations", aliases=["av"])
    @commands.has_permissions(administrator=True)
    async def show_violations(self, ctx, user: discord.Member):
        """Показать нарушения пользователя"""
        automod = self.bot.get_cog("AutoMod")
        if not automod:
            embed = Embed(
                title=f"{Emojis.ERROR} Ошибка",
                description="Модуль автомодерации не загружен",
                color="RED"
            )
            return await ctx.send(embed=embed)
            
        if user.id not in automod.violations or not automod.violations[user.id]:
            embed = Embed(
                title=f"{Emojis.INFO} История нарушений",
                description=f"У {user.mention} нет нарушений",
                color="BLUE"
            )
        else:
            embed = Embed(
                title=f"{Emojis.INFO} История нарушений",
                description=f"Нарушения {user.mention}:",
                color="BLUE"
            )
            
            for rule_name, count in automod.violations[user.id].items():
                rule = automod.rules[rule_name]
                embed.add_field(
                    name=f"{Emojis.DOT} {rule.name}",
                    value=f"Количество: `{count}`\nПоследнее наказание: `{rule.punishment.get(count, 'warn')}`",
                    inline=False
                )
                
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AutoModConfig(bot)) 