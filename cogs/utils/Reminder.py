import discord
from discord.ext import commands, tasks
import asyncio
from datetime import datetime, timedelta
import re
from utils import create_embed

class Reminder(commands.GroupCog, group_name="reminder"):
    def __init__(self, bot):
        self.bot = bot
        self.reminders = {}
        self.check_reminders.start()

    def cog_unload(self):
        self.check_reminders.cancel()

    def parse_time(self, time_str: str) -> timedelta:
        """Парсинг строки времени в timedelta"""
        time_units = {
            'с': 'seconds',
            'м': 'minutes',
            'ч': 'hours',
            'д': 'days',
            'н': 'weeks'
        }
        
        total_seconds = 0
        pattern = r'(\d+)([смчдн])'
        matches = re.findall(pattern, time_str.lower())
        
        for value, unit in matches:
            if unit in time_units:
                if unit == 'н':  # недели
                    total_seconds += int(value) * 7 * 24 * 60 * 60
                elif unit == 'д':  # дни
                    total_seconds += int(value) * 24 * 60 * 60
                elif unit == 'ч':  # часы
                    total_seconds += int(value) * 60 * 60
                elif unit == 'м':  # минуты
                    total_seconds += int(value) * 60
                elif unit == 'с':  # секунды
                    total_seconds += int(value)
        
        return timedelta(seconds=total_seconds)

    @tasks.loop(seconds=30)
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
        time="Время до напоминания (например: 30м, 1ч, 2д)",
        message="Текст напоминания"
    )
    async def create(self, interaction: discord.Interaction, time: str, message: str):
        try:
            time_delta = self.parse_time(time)
            if time_delta.total_seconds() < 30:
                await interaction.response.send_message(
                    embed=create_embed(
                        description="Минимальное время напоминания - 30 секунд!"
                    )
                )
                return
            
            if time_delta.total_seconds() > 30 * 24 * 60 * 60:  # 30 дней
                await interaction.response.send_message(
                    embed=create_embed(
                        description="Максимальное время напоминания - 30 дней!"
                    )
                )
                return

            reminder_time = datetime.now() + time_delta
            
            if interaction.user.id not in self.reminders:
                self.reminders[interaction.user.id] = []
            
            if len(self.reminders[interaction.user.id]) >= 5:
                await interaction.response.send_message(
                    embed=create_embed(
                        description="У вас уже установлено максимальное количество напоминаний (5)!"
                    )
                )
                return

            self.reminders[interaction.user.id].append({
                'message': message,
                'time': reminder_time,
                'channel': interaction.channel  # Сохраняем канал, где было создано напоминание
            })

            # Форматирование времени для отображения
            time_str = []
            if time_delta.days > 0:
                time_str.append(f"{time_delta.days} дней")
            hours = time_delta.seconds // 3600
            if hours > 0:
                time_str.append(f"{hours} часов")
            minutes = (time_delta.seconds % 3600) // 60
            if minutes > 0:
                time_str.append(f"{minutes} минут")
            seconds = time_delta.seconds % 60
            if seconds > 0:
                time_str.append(f"{seconds} секунд")

            await interaction.response.send_message(
                embed=create_embed(
                    title="⏰ Напоминание создано",
                    description=f"Я напомню вам через {', '.join(time_str)}:\n{message}"
                )
            )
        except Exception as e:
            await interaction.response.send_message(
                embed=create_embed(
                    description="Неверный формат времени! Используйте: 30с, 15м, 2ч, 1д, 1н"
                )
            )

    @discord.app_commands.command(name="list", description="Показать список ваших напоминаний")
    async def list(self, interaction: discord.Interaction):
        if interaction.user.id not in self.reminders or not self.reminders[interaction.user.id]:
            await interaction.response.send_message(
                embed=create_embed(
                    description="У вас нет активных напоминаний!"
                )
            )
            return

        reminders_list = []
        for i, reminder in enumerate(self.reminders[interaction.user.id], 1):
            time_left = reminder['time'] - datetime.now()
            total_seconds = int(time_left.total_seconds())
            
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
            if seconds > 0 and not (days > 0 or hours > 0):  # показываем секунды только если нет дней и часов
                time_parts.append(f"{seconds}с")
            
            time_str = " ".join(time_parts) if time_parts else "меньше минуты"
            reminders_list.append(f"**{i}.** Через {time_str}: {reminder['message']}")

        embed = create_embed(
            title="⏰ Ваши напоминания",
            description="\n".join(reminders_list)
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
                    description="Напоминание с таким номером не найдено!"
                )
            )
            return

        removed_reminder = self.reminders[interaction.user.id].pop(number - 1)
        if not self.reminders[interaction.user.id]:
            del self.reminders[interaction.user.id]

        await interaction.response.send_message(
            embed=create_embed(
                title="⏰ Напоминание удалено",
                description=f"Удалено напоминание:\n{removed_reminder['message']}"
            )
        )

async def setup(bot):
    await bot.add_cog(Reminder(bot)) 