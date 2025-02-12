import discord
from discord.ext import commands
from discord import app_commands
from typing import Dict, List, Optional
from Niludetsu.moderation.rules import (
    SpamRule, CapsRule, LinksRule, BadWordsRule,
    MentionSpamRule, EmoteSpamRule, NewlineSpamRule
)
from Niludetsu.moderation.punishments import Punishment
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.constants import Emojis
from Niludetsu.database.db import Database

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
                       f"🔴 - Правило отключено",
            color="BLUE"
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

class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.punishment_handler = Punishment(bot)
        
        # Инициализация правил
        self.rules = {
            'spam': SpamRule(),
            'caps': CapsRule(),
            'links': LinksRule(),
            'bad_words': BadWordsRule(),
            'mention_spam': MentionSpamRule(),
            'emote_spam': EmoteSpamRule(),
            'newline_spam': NewlineSpamRule()
        }
        
        # Счетчик нарушений
        self.violations = {}  # {user_id: {rule_name: count}}
        self.exceptions = {}  # {channel_id: [rule_names]}
        
    async def _initialize(self):
        """Инициализация базы данных"""
        await self.db.init()
        await self.load_violations()
        await self.load_exceptions()
        
        # Добавляем исключение для канала партнёрств
        await self.add_exception(1125546967217471609, "links")
        
    async def load_violations(self):
        """Загрузка истории нарушений из базы данных"""
        try:
            results = await self.db.fetch_all(
                "SELECT user_id, rule_name, violations_count FROM automod_violations"
            )
            for row in results:
                user_id = int(row['user_id'])
                if user_id not in self.violations:
                    self.violations[user_id] = {}
                self.violations[user_id][row['rule_name']] = row['violations_count']
        except Exception as e:
            print(f"❌ Ошибка при загрузке нарушений: {e}")
            
    async def load_exceptions(self):
        """Загрузка исключений из базы данных"""
        try:
            results = await self.db.fetch_all(
                "SELECT channel_id, rule_name FROM automod_exceptions"
            )
            for row in results:
                channel_id = int(row['channel_id'])
                if channel_id not in self.exceptions:
                    self.exceptions[channel_id] = []
                self.exceptions[channel_id].append(row['rule_name'])
        except Exception as e:
            print(f"❌ Ошибка при загрузке исключений: {e}")
            
    async def save_violation(self, user_id: int, rule_name: str):
        """Сохранение нарушения в базу данных"""
        try:
            if user_id not in self.violations:
                self.violations[user_id] = {}
            if rule_name not in self.violations[user_id]:
                self.violations[user_id][rule_name] = 0
                
            self.violations[user_id][rule_name] += 1
            
            await self.db.execute(
                """
                INSERT OR REPLACE INTO automod_violations (user_id, rule_name, violations_count)
                VALUES (?, ?, ?)
                """,
                str(user_id), rule_name, self.violations[user_id][rule_name]
            )
        except Exception as e:
            print(f"❌ Ошибка при сохранении нарушения: {e}")
            
    async def add_exception(self, channel_id: int, rule_name: str):
        """Добавить исключение для канала"""
        try:
            await self.db.execute(
                """
                INSERT OR IGNORE INTO automod_exceptions (channel_id, rule_name)
                VALUES (?, ?)
                """,
                str(channel_id), rule_name
            )
            
            if channel_id not in self.exceptions:
                self.exceptions[channel_id] = []
            if rule_name not in self.exceptions[channel_id]:
                self.exceptions[channel_id].append(rule_name)
                
        except Exception as e:
            print(f"❌ Ошибка при добавлении исключения: {e}")
            
    async def remove_exception(self, channel_id: int, rule_name: str):
        """Удалить исключение для канала"""
        try:
            await self.db.execute(
                "DELETE FROM automod_exceptions WHERE channel_id = ? AND rule_name = ?",
                str(channel_id), rule_name
            )
            
            if channel_id in self.exceptions and rule_name in self.exceptions[channel_id]:
                self.exceptions[channel_id].remove(rule_name)
                
        except Exception as e:
            print(f"❌ Ошибка при удалении исключения: {e}")
            
    async def check_message(self, message: discord.Message) -> Optional[str]:
        """Проверка сообщения на нарушения"""
        if message.author.bot or message.author.guild_permissions.administrator:
            return None
            
        for rule_name, rule in self.rules.items():
            try:
                # Проверяем исключения
                if message.channel.id in self.exceptions and rule_name in self.exceptions[message.channel.id]:
                    continue
                    
                if await rule.check(message.content, user_id=message.author.id):
                    return rule_name
            except Exception as e:
                print(f"❌ Ошибка при проверке правила {rule_name}: {e}")
                
        return None
        
    async def handle_violation(self, message: discord.Message, rule_name: str):
        """Обработка нарушения"""
        try:
            # Сохраняем нарушение
            await self.save_violation(message.author.id, rule_name)
            
            # Получаем количество нарушений
            violation_count = self.violations.get(message.author.id, {}).get(rule_name, 0)
            
            # Получаем наказание
            rule = self.rules[rule_name]
            punishment = rule.punishment.get(violation_count, "warn")
            
            # Применяем наказание
            await self.punishment_handler.apply_punishment(
                message.author,
                punishment,
                f"Нарушение правила: {rule.description}"
            )
            
            # Создаем эмбед с информацией
            embed = await self.punishment_handler.get_punishment_embed(
                message.author,
                rule.name,
                punishment,
                rule.description
            )
            
            # Отправляем сообщение в канал логов
            log_channel = discord.utils.get(message.guild.channels, name="mod-logs")
            if log_channel:
                await log_channel.send(embed=embed)
                
            # Удаляем сообщение нарушителя
            await message.delete()
            
        except Exception as e:
            print(f"❌ Ошибка при обработке нарушения: {e}")
            
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Обработка новых сообщений"""
        if not message.guild:
            return
            
        rule_name = await self.check_message(message)
        if rule_name:
            await self.handle_violation(message, rule_name)
            
    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """Обработка редактирования сообщений"""
        if not after.guild or before.content == after.content:
            return
            
        rule_name = await self.check_message(after)
        if rule_name:
            await self.handle_violation(after, rule_name)
            
    automod_group = app_commands.Group(name="automod", description="Управление автомодерацией")
    
    @automod_group.command(name="status")
    @app_commands.checks.has_permissions(administrator=True)
    async def automod_status(self, interaction: discord.Interaction):
        """Показать статус автомодерации"""
        embed = Embed(
            title=f"{Emojis.SHIELD} Статус автомодерации",
            description="Текущие настройки и правила:",
            color="BLUE"
        )
        
        for rule_name, rule in self.rules.items():
            violations = sum(1 for user_violations in self.violations.values()
                           if rule_name in user_violations)
            
            embed.add_field(
                name=f"{Emojis.DOT} {rule.name}",
                value=f"Нарушений: `{violations}`\nОписание: {rule.description}",
                inline=False
            )
            
        await interaction.response.send_message(embed=embed)
        
    @automod_group.command(name="clear")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(user="Пользователь для очистки нарушений")
    async def automod_clear(self, interaction: discord.Interaction, user: discord.Member):
        """Очистить историю нарушений пользователя"""
        try:
            if user.id in self.violations:
                del self.violations[user.id]
                
            await self.db.execute(
                "DELETE FROM automod_violations WHERE user_id = ?",
                str(user.id)
            )
            
            embed = Embed(
                title=f"{Emojis.SUCCESS} История очищена",
                description=f"История нарушений для {user.mention} была очищена",
                color="GREEN"
            )
            
        except Exception as e:
            embed = Embed(
                title=f"{Emojis.ERROR} Ошибка",
                description=f"Не удалось очистить историю: {str(e)}",
                color="RED"
            )
            
        await interaction.response.send_message(embed=embed)
        
    @automod_group.command(name="violations")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(user="Пользователь для просмотра нарушений")
    async def automod_violations(self, interaction: discord.Interaction, user: discord.Member):
        """Показать историю нарушений пользователя"""
        if user.id not in self.violations or not self.violations[user.id]:
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
            
            for rule_name, count in self.violations[user.id].items():
                rule = self.rules[rule_name]
                embed.add_field(
                    name=f"{Emojis.DOT} {rule.name}",
                    value=f"Количество: `{count}`\nПоследнее наказание: `{rule.punishment.get(count, 'warn')}`",
                    inline=False
                )
                
        await interaction.response.send_message(embed=embed)
        
    @automod_group.command(name="exception")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        channel="Канал для исключения",
        rule="Правило для исключения",
        action="Действие (add/remove)"
    )
    async def automod_exception(
        self, 
        interaction: discord.Interaction, 
        channel: discord.TextChannel,
        rule: str,
        action: str
    ):
        """Управление исключениями автомодерации"""
        if rule not in self.rules:
            embed = Embed(
                title=f"{Emojis.ERROR} Ошибка",
                description=f"Правило `{rule}` не существует",
                color="RED"
            )
            return await interaction.response.send_message(embed=embed)
            
        try:
            if action.lower() == "add":
                await self.add_exception(channel.id, rule)
                action_text = "добавлено в"
            else:
                await self.remove_exception(channel.id, rule)
                action_text = "удалено из"
                
            embed = Embed(
                title=f"{Emojis.SUCCESS} Исключение обновлено",
                description=f"Правило `{rule}` {action_text} исключений для канала {channel.mention}",
                color="GREEN"
            )
            
        except Exception as e:
            embed = Embed(
                title=f"{Emojis.ERROR} Ошибка",
                description=f"Не удалось обновить исключение: {str(e)}",
                color="RED"
            )
            
        await interaction.response.send_message(embed=embed)

    @commands.command(name="automod")
    @commands.has_permissions(administrator=True)
    async def automod_config(self, ctx):
        """Настройка автомодерации"""
        embed = Embed(
            title=f"{Emojis.SETTINGS} Настройка автомодерации",
            description="Выберите канал и настройте правила автомодерации\n\n"
                       "🟢 - Правило включено\n"
                       "🔴 - Правило отключено",
            color="BLUE"
        )
        
        view = ConfigView(self)
        await ctx.send(embed=embed, view=view)
        
    @commands.command(name="violations")
    @commands.has_permissions(administrator=True)
    async def show_violations(self, ctx, user: discord.Member):
        """Показать нарушения пользователя"""
        if user.id not in self.violations or not self.violations[user.id]:
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
            
            for rule_name, count in self.violations[user.id].items():
                rule = self.rules[rule_name]
                embed.add_field(
                    name=f"{Emojis.DOT} {rule.name}",
                    value=f"Количество: `{count}`\nПоследнее наказание: `{rule.punishment.get(count, 'warn')}`",
                    inline=False
                )
                
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AutoMod(bot)) 