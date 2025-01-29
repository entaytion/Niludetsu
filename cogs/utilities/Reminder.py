import discord
from discord.ext import commands, tasks
import asyncio
from datetime import datetime, timedelta
import re
from Niludetsu.utils.embed import create_embed
from Niludetsu.core.base import EMOJIS

class Reminder(commands.GroupCog, group_name="reminder"):
    def __init__(self, bot):
        self.bot = bot
        self.reminders = {}
        self.check_reminders.start()

    def cog_unload(self):
        self.check_reminders.cancel()

    def parse_time(self, time_str: str) -> tuple[timedelta, str]:
        """Парсинг строки времени в timedelta"""
        time_units = {
            'с': ('seconds', 'секунд'),
            'м': ('minutes', 'минут'),
            'ч': ('hours', 'часов'),
            'д': ('days', 'дней'),
            'н': ('weeks', 'недель')
        }
        
        total_seconds = 0
        pattern = r'(\d+)([смчдн])'
        matches = re.findall(pattern, time_str.lower())
        
        if not matches:
            raise ValueError("Неверный формат времени")
            
        time_parts = []
        for value, unit in matches:
            value = int(value)
            if unit in time_units:
                unit_name = time_units[unit][1]
                if unit == 'н':  # недели
                    total_seconds += value * 7 * 24 * 60 * 60
                    time_parts.append(f"{value} {unit_name}")
                elif unit == 'д':  # дни
                    total_seconds += value * 24 * 60 * 60
                    time_parts.append(f"{value} {unit_name}")
                elif unit == 'ч':  # часы
                    total_seconds += value * 60 * 60
                    time_parts.append(f"{value} {unit_name}")
                elif unit == 'м':  # минуты
                    total_seconds += value * 60
                    time_parts.append(f"{value} {unit_name}")
                elif unit == 'с':  # секунды
                    total_seconds += value
                    time_parts.append(f"{value} {unit_name}")
        
        return timedelta(seconds=total_seconds), ", ".join(time_parts)

    @tasks.loop(seconds=1)
    async def check_reminders(self):
        current_time = datetime.now()
        to_remove = []
        
        for user_id, user_reminders in self.reminders.items():
            for reminder in user_reminders[:]:
                if current_time >= reminder['time']:
                    user = self.bot.get_user(user_id)
                    if user:
                        channel = reminder.get('channel')
                        if channel:
                            embed = create_embed(
                                title="⏰ Напоминание",
                                description=f"{reminder['message']}",
                                color=0x2ecc71
                            )
                            try:
                                await channel.send(f"{user.mention}", embed=embed)
                            except:
                                # Если не удалось отправить в канал, пробуем отправить в ЛС
                                try:
                                    await user.send(embed=embed)
                                except:
                                    pass
                    user_reminders.remove(reminder)
            
            if not user_reminders:
                to_remove.append(user_id)
        
        for user_id in to_remove:
            del self.reminders[user_id]

    @discord.app_commands.command(name="create", description="Создать новое напоминание")
    @discord.app_commands.describe(
        time="Время до напоминания (например: 30с, 15м, 2ч, 1д, 1н)",
        message="Текст напоминания"
    )
    async def create(self, interaction: discord.Interaction, time: str, message: str):
        try:
            time_delta, time_str = self.parse_time(time)
            
            # Проверка минимального времени
            if time_delta.total_seconds() < 5:  # Минимум 5 секунд
                await interaction.response.send_message(
                    embed=create_embed(
                        title="❌ Ошибка",
                        description="Минимальное время напоминания - 5 секунд!",
                        color=0xe74c3c
                    )
                )
                return
            
            # Проверка максимального времени
            if time_delta.total_seconds() > 30 * 24 * 60 * 60:  # 30 дней
                await interaction.response.send_message(
                    embed=create_embed(
                        title="❌ Ошибка",
                        description="Максимальное время напоминания - 30 дней!",
                        color=0xe74c3c
                    )
                )
                return

            reminder_time = datetime.now() + time_delta
            
            # Проверка количества напоминаний
            if interaction.user.id not in self.reminders:
                self.reminders[interaction.user.id] = []
            
            if len(self.reminders[interaction.user.id]) >= 5:
                await interaction.response.send_message(
                    embed=create_embed(
                        title="❌ Ошибка",
                        description="У вас уже установлено максимальное количество напоминаний (5)!",
                        color=0xe74c3c
                    )
                )
                return

            # Добавляем напоминание
            self.reminders[interaction.user.id].append({
                'message': message,
                'time': reminder_time,
                'channel': interaction.channel
            })

            await interaction.response.send_message(
                embed=create_embed(
                    title="⏰ Напоминание создано",
                    description=f"Я напомню вам через {time_str}:\n{message}",
                    color=0x2ecc71
                )
            )
            
        except ValueError as e:
            await interaction.response.send_message(
                embed=create_embed(
                    title="❌ Ошибка",
                    description=str(e) if str(e) != "Неверный формат времени" else 
                              "Неверный формат времени! Используйте: 30с, 15м, 2ч, 1д, 1н",
                    color=0xe74c3c
                )
            )
        except Exception as e:
            await interaction.response.send_message(
                embed=create_embed(
                    title="❌ Ошибка",
                    description=f"Произошла ошибка: {str(e)}",
                    color=0xe74c3c
                )
            )

    @discord.app_commands.command(name="list", description="Показать список ваших напоминаний")
    async def list(self, interaction: discord.Interaction):
        if interaction.user.id not in self.reminders or not self.reminders[interaction.user.id]:
            await interaction.response.send_message(
                embed=create_embed(
                    title="📝 Напоминания",
                    description="У вас нет активных напоминаний!",
                    color=0xf1c40f
                )
            )
            return

        reminders_list = []
        for i, reminder in enumerate(self.reminders[interaction.user.id], 1):
            time_left = reminder['time'] - datetime.now()
            total_seconds = int(time_left.total_seconds())
            
            if total_seconds < 0:
                continue
                
            days = total_seconds // (24 * 3600)
            hours = (total_seconds % (24 * 3600)) // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            
            time_parts = []
            if days > 0:
                time_parts.append(f"{days}д")
            if hours > 0:
                time_parts.append(f"{hours}ч")
            if minutes > 0:
                time_parts.append(f"{minutes}м")
            if seconds > 0 or not time_parts:  # показываем секунды всегда, если нет других единиц
                time_parts.append(f"{seconds}с")
            
            time_str = " ".join(time_parts)
            reminders_list.append(f"**{i}.** Через {time_str}: {reminder['message']}")

        embed = create_embed(
            title="📝 Ваши напоминания",
            description="\n".join(reminders_list),
            color=0x3498db
        )
        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="delete", description="Удалить напоминание")
    @discord.app_commands.describe(number="Номер напоминания (используйте /reminder list чтобы увидеть список)")
    async def delete(self, interaction: discord.Interaction, number: int):
        if (interaction.user.id not in self.reminders or 
            not self.reminders[interaction.user.id] or 
            number < 1 or 
            number > len(self.reminders[interaction.user.id])):
            
            await interaction.response.send_message(
                embed=create_embed(
                    title="❌ Ошибка",
                    description="Напоминание с таким номером не найдено!",
                    color=0xe74c3c
                )
            )
            return

        removed_reminder = self.reminders[interaction.user.id].pop(number - 1)
        if not self.reminders[interaction.user.id]:
            del self.reminders[interaction.user.id]

        await interaction.response.send_message(
            embed=create_embed(
                title="✅ Напоминание удалено",
                description=f"Удалено напоминание:\n{removed_reminder['message']}",
                color=0x2ecc71
            )
        )

async def setup(bot):
    await bot.add_cog(Reminder(bot)) 