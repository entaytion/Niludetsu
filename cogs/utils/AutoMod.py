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
import asyncio
import json
from datetime import datetime

class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.punishment_handler = Punishment(bot)
        self.ready = False
        
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
        
        # Запускаем инициализацию
        asyncio.create_task(self._initialize())
        
    async def _initialize(self):
        """Инициализация модуля автомодерации"""
        await self.bot.wait_until_ready()
        
        await self.db.init()
        await self.load_violations()
        await self.load_exceptions()
        await self.load_rules()
        
        # Добавляем исключение для канала партнёрств
        try:
            if self.bot.guilds:
                await self.add_exception(1125546967217471609, "links")
            else:
                print("❌ Бот не подключен ни к одному серверу")
        except Exception as e:
            print(f"❌ Ошибка при добавлении исключения для канала партнёрств: {e}")
            
        self.ready = True
        print("✅ Автомодерация инициализирована")
        
    async def load_rules(self):
        """Загрузка настроек правил из базы данных"""
        try:
            for guild in self.bot.guilds:
                results = await self.db.fetch_all(
                    """
                    SELECT rule_name, enabled, settings, last_update
                    FROM automod_rules
                    WHERE guild_id = ?
                    """,
                    str(guild.id)
                )
                
                for row in results:
                    rule_name = row['rule_name']
                    if rule_name in self.rules:
                        rule = self.rules[rule_name]
                        rule.enabled = row['enabled']
                        if row['settings']:
                            settings = json.loads(row['settings'])
                            rule.update_from_dict(settings)
                            
        except Exception as e:
            print(f"❌ Ошибка при загрузке настроек правил: {e}")
            
    async def save_rule_settings(self, guild_id: str, rule_name: str):
        """Сохранение настроек правила в базу данных"""
        try:
            if rule_name in self.rules:
                rule = self.rules[rule_name]
                settings = rule.to_dict()
                
                await self.db.execute(
                    """
                    INSERT INTO automod_rules (rule_name, guild_id, enabled, settings, last_update)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(rule_name, guild_id) 
                    DO UPDATE SET enabled = ?, settings = ?, last_update = CURRENT_TIMESTAMP
                    """,
                    rule_name, guild_id, rule.enabled, json.dumps(settings),
                    rule.enabled, json.dumps(settings)
                )
                
        except Exception as e:
            print(f"❌ Ошибка при сохранении настроек правила: {e}")
            
    async def load_violations(self):
        """Загрузка истории нарушений из базы данных"""
        try:
            results = await self.db.fetch_all(
                """
                SELECT user_id, rule_name, COUNT(*) as violations_count 
                FROM moderation 
                WHERE type = 'violation' AND active = TRUE 
                GROUP BY user_id, rule_name
                """
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
                """
                SELECT channel_id, rule_name 
                FROM moderation 
                WHERE type = 'exception' AND active = TRUE
                """
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
            
            # Получаем guild_id безопасно
            guild_id = None
            for guild in self.bot.guilds:
                guild_id = str(guild.id)
                break
                
            if guild_id:
                await self.db.execute(
                    """
                    INSERT INTO moderation (
                        user_id, guild_id, type, rule_name,
                        created_at, active
                    ) VALUES (?, ?, 'violation', ?, CURRENT_TIMESTAMP, TRUE)
                    """,
                    str(user_id), guild_id, rule_name
                )
            else:
                print("❌ Не удалось получить guild_id для сохранения нарушения")
        except Exception as e:
            print(f"❌ Ошибка при сохранении нарушения: {e}")
            
    async def add_exception(self, channel_id: int, rule_name: str):
        """Добавить исключение для канала"""
        try:
            # Получаем guild_id безопасно
            guild_id = None
            for guild in self.bot.guilds:
                guild_id = str(guild.id)
                break
                
            if not guild_id:
                print("❌ Не удалось получить guild_id для добавления исключения")
                return

            # Проверяем, существует ли уже такое исключение
            existing = await self.db.fetch_all(
                """
                SELECT id FROM moderation 
                WHERE channel_id = ? AND rule_name = ? 
                AND type = 'exception' AND active = TRUE
                """,
                str(channel_id), rule_name
            )
            
            if existing:
                print(f"ℹ️ Исключение для канала {channel_id} и правила {rule_name} уже существует")
                return
                
            # Если исключения нет, добавляем его
            await self.db.execute(
                """
                INSERT INTO moderation (
                    channel_id, guild_id, type, rule_name,
                    created_at, active
                ) VALUES (?, ?, 'exception', ?, CURRENT_TIMESTAMP, TRUE)
                """,
                str(channel_id), guild_id, rule_name
            )
            
            if channel_id not in self.exceptions:
                self.exceptions[channel_id] = []
            if rule_name not in self.exceptions[channel_id]:
                self.exceptions[channel_id].append(rule_name)
                print(f"✅ Добавлено исключение для канала {channel_id} и правила {rule_name}")
                
        except Exception as e:
            print(f"❌ Ошибка при добавлении исключения: {e}")
            
    async def remove_exception(self, channel_id: int, rule_name: str):
        """Удалить исключение для канала"""
        try:
            await self.db.execute(
                """
                UPDATE moderation 
                SET active = FALSE 
                WHERE channel_id = ? AND rule_name = ? 
                AND type = 'exception' AND active = TRUE
                """,
                str(channel_id), rule_name
            )
            
            if channel_id in self.exceptions and rule_name in self.exceptions[channel_id]:
                self.exceptions[channel_id].remove(rule_name)
                
        except Exception as e:
            print(f"❌ Ошибка при удалении исключения: {e}")
            
    async def check_message(self, message: discord.Message) -> Optional[str]:
        """Проверка сообщения на нарушения"""
        if message.author.bot:
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
                f"Нарушение правила: {rule.description}",
                rule_name,
                self.bot.user.id
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
        if not message.guild or not self.ready:
            return
            
        try:
            rule_name = await self.check_message(message)
            if rule_name:
                await self.handle_violation(message, rule_name)
        except Exception as e:
            print(f"❌ Ошибка при обработке сообщения: {e}")
            # Логируем ошибку в канал логов
            try:
                log_channel = discord.utils.get(message.guild.channels, name="mod-logs")
                if log_channel:
                    error_embed = Embed(
                        title=f"{Emojis.ERROR} Ошибка автомодерации",
                        description=f"```py\n{str(e)}\n```",
                        color="RED"
                    )
                    error_embed.add_field(
                        name="Канал",
                        value=f"{message.channel.mention} (`{message.channel.id}`)",
                        inline=True
                    )
                    error_embed.add_field(
                        name="Пользователь",
                        value=f"{message.author.mention} (`{message.author.id}`)",
                        inline=True
                    )
                    await log_channel.send(embed=error_embed)
            except:
                pass
            
    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """Обработка редактирования сообщений"""
        if not after.guild or before.content == after.content:
            return
            
        rule_name = await self.check_message(after)
        if rule_name:
            await self.handle_violation(after, rule_name)
            
    @commands.command(name="automod", description="Управление автомодерацией")
    async def automod_command(self, ctx):
        """Команда для управления автомодерацией"""
        # Создаем эмбед с информацией о правилах
        embed = Embed(
            title=f"{Emojis.SETTINGS} Настройки автомодерации",
            description="Используйте `!automod <правило> <on/off>` для управления правилами\nНапример: `!automod spam off`",
            color="BLUE"
        )
        
        for rule_name, rule in self.rules.items():
            embed.add_field(
                name=f"{Emojis.DOT} {rule.name}",
                value=(
                    f"**Статус:** {'🟢 Включено' if rule.enabled else '🔴 Выключено'}\n"
                    f"**Описание:** {rule.description}\n"
                    f"**Обновлено:** <t:{int(rule.last_update.timestamp())}:R>"
                ),
                inline=False
            )
            
        await ctx.send(embed=embed)
        
    @commands.command(name="automod_toggle", aliases=["am"])
    async def automod_toggle(self, ctx, rule_name: str = None, state: str = None):
        """Включение/выключение правил автомодерации
        
        Параметры:
        ---------------
        rule_name: Название правила (spam/caps/links/bad_words/mention_spam/emote_spam/newline_spam)
        state: on/off - включить/выключить
        """
        if not rule_name:
            await ctx.send("❌ Укажите название правила!")
            return
            
        if not state or state.lower() not in ['on', 'off']:
            await ctx.send("❌ Укажите состояние (on/off)!")
            return
            
        rule_name = rule_name.lower()
        if rule_name not in self.rules:
            await ctx.send("❌ Неверное название правила!")
            return
            
        rule = self.rules[rule_name]
        new_state = state.lower() == 'on'
        
        if rule.enabled == new_state:
            await ctx.send(f"ℹ️ Правило {rule.name} уже {'включено' if new_state else 'выключено'}!")
            return
            
        # Переключаем состояние правила
        rule.enabled = new_state
        rule.last_update = datetime.now()
        
        # Сохраняем изменения
        await self.save_rule_settings(str(ctx.guild.id), rule_name)
        
        await ctx.send(
            f"{'✅ Включено' if new_state else '❌ Отключено'} правило {rule.name}"
        )

async def setup(bot):
    await bot.add_cog(AutoMod(bot)) 