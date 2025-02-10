import discord
import matplotlib.pyplot as plt
import numpy as np
import io
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from .base import BaseAnalytics, COLORS
from Niludetsu.utils.constants import Emojis
from Niludetsu.utils.embed import Embed

class MessageAnalytics(BaseAnalytics):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        
    async def generate_analytics(self, guild, days=7):
        """Генерирует расширенную аналитику сообщений"""
        # Создаем фигуру с 4 графиками
        fig = plt.figure(figsize=(15, 12))
        
        # Собираем данные
        start_time = datetime.now() - timedelta(days=days)
        activity_matrix = np.zeros((7, 24))  # дни x часы
        user_messages = defaultdict(int)
        message_lengths = []
        hourly_activity = defaultdict(int)
        
        total_messages = 0
        
        for channel in guild.text_channels:
            try:
                async for message in channel.history(limit=None, after=start_time):
                    if not message.author.bot:
                        # Обновляем тепловую карту
                        day = message.created_at.weekday()
                        hour = message.created_at.hour
                        activity_matrix[day][hour] += 1
                        
                        # Считаем сообщения пользователей
                        user_messages[message.author.name] += 1
                        
                        # Собираем длины сообщений
                        message_lengths.append(len(message.content))
                        
                        # Почасовая активность
                        hour_key = message.created_at.replace(minute=0, second=0, microsecond=0)
                        hourly_activity[hour_key] += 1
                        
                        total_messages += 1
            except discord.Forbidden:
                continue
        
        if total_messages == 0:
            embed = Embed(
                title=f"{Emojis.ERROR} Нет данных",
                description="Не удалось собрать статистику сообщений",
                color=0xe74c3c
            )
            return embed, None
        
        # График 1: Тепловая карта активности
        ax1 = plt.subplot(2, 2, 1)
        im = ax1.imshow(activity_matrix, cmap='YlOrRd')
        ax1.set_title('Тепловая карта активности')
        ax1.set_xlabel('Час')
        ax1.set_ylabel('День недели')
        
        # Настройка осей
        weekdays = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        hours = list(range(24))
        ax1.set_yticks(range(len(weekdays)))
        ax1.set_yticklabels(weekdays)
        ax1.set_xticks(range(0, 24, 3))
        ax1.set_xticklabels([f'{h:02d}:00' for h in range(0, 24, 3)])
        
        # Добавляем colorbar
        plt.colorbar(im, ax=ax1)
        
        # График 2: Топ-10 пользователей
        ax2 = plt.subplot(2, 2, 2)
        top_users = dict(sorted(user_messages.items(), key=lambda x: x[1], reverse=True)[:10])
        bars = ax2.barh(list(top_users.keys()), list(top_users.values()), color=COLORS['secondary'])
        ax2.set_title('Топ-10 активных участников')
        ax2.set_xlabel('Количество сообщений')
        
        # Добавляем значения на бары
        for bar in bars:
            width = bar.get_width()
            ax2.text(width, bar.get_y() + bar.get_height()/2,
                    f'{int(width)}',
                    ha='left', va='center',
                    color=COLORS['text'],
                    fontproperties=self.custom_font)
        
        # График 3: Статистика по периодам
        ax3 = plt.subplot(2, 2, 3)
        
        # Собираем данные за разные периоды
        now = datetime.now(datetime.now().astimezone().tzinfo)  # Получаем текущее время с часовым поясом
        
        # Подсчитываем сообщения за каждый период
        period_messages = {
            '1d': 0,
            '7d': 0,
            '30d': 0
        }
        
        # Проходим по всем сообщениям и считаем их для каждого периода
        for date, count in hourly_activity.items():
            date_with_tz = date.replace(tzinfo=now.tzinfo)
            time_diff = now - date_with_tz
            
            if time_diff <= timedelta(days=1):
                period_messages['1d'] += count
            if time_diff <= timedelta(days=7):
                period_messages['7d'] += count
            if time_diff <= timedelta(days=30):
                period_messages['30d'] += count
        
        # Создаем столбцы
        periods_labels = ['За день', 'За неделю', 'За месяц']
        period_values = [period_messages['1d'], period_messages['7d'], period_messages['30d']]
        
        bars = ax3.bar(periods_labels, period_values, color=COLORS['primary'])
        ax3.set_title('Количество сообщений по периодам')
        ax3.set_ylabel('Количество сообщений')
        
        # Добавляем значения над столбцами
        for bar in bars:
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}',
                    ha='center', va='bottom',
                    color=COLORS['text'],
                    fontproperties=self.custom_font)
                    
        # Поворачиваем подписи для лучшей читаемости
        plt.setp(ax3.get_xticklabels(), rotation=0)
        
        # График 4: Тренд активности
        ax4 = plt.subplot(2, 2, 4)
        dates = sorted(hourly_activity.keys())
        values = [hourly_activity[date] for date in dates]
        
        ax4.plot(dates, values, color=COLORS['accent'], linewidth=2)
        ax4.set_title('Тренд активности')
        ax4.set_xlabel('Время')
        ax4.set_ylabel('Сообщений в час')
        
        # Поворачиваем метки времени
        plt.setp(ax4.get_xticklabels(), rotation=45, ha='right')
        
        # Применяем стиль ко всем графикам
        for ax in [ax1, ax2, ax3, ax4]:
            self.style_plot(fig, ax)
        
        # Настраиваем отступы
        plt.subplots_adjust(left=0.1, right=0.95, top=0.95, bottom=0.1, hspace=0.3, wspace=0.3)
        
        # Сохраняем график
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=300)
        buffer.seek(0)
        plt.close()
        
        # Создаем эмбед
        embed = Embed(
            title=f"{Emojis.STATS} Расширенная аналитика сообщений {guild.name}",
            description=f"{Emojis.INFO} Анализ активности за последние {days} дней",
            color="DEFAULT"
        )
        
        # Добавляем статистику
        avg_messages = total_messages / days
        avg_length = sum(message_lengths) / len(message_lengths) if message_lengths else 0
        peak_hour = max(range(24), key=lambda h: sum(activity_matrix[:, h]))
        peak_day = weekdays[max(range(7), key=lambda d: sum(activity_matrix[d, :]))]
        
        stats = [
            f"{Emojis.DOT} **Всего сообщений:** `{total_messages}`",
            f"{Emojis.DOT} **Среднее в день:** `{int(avg_messages)}`",
            f"{Emojis.DOT} **Средняя длина:** `{int(avg_length)} символов`",
            f"{Emojis.DOT} **Пик активности:** `{peak_hour:02d}:00`",
            f"{Emojis.DOT} **Самый активный день:** `{peak_day}`",
            f"{Emojis.DOT} **Уникальных авторов:** `{len(user_messages)}`"
        ]
        
        embed.add_field(
            name=f"{Emojis.STATS} Общая статистика",
            value="\n".join(stats),
            inline=False
        )

        embed.set_image(url="attachment://analytics.png")
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
            
        embed.set_footer(text=f"ID: {guild.id} • Данные собраны")
        embed.timestamp = datetime.now()
        
        return embed, discord.File(buffer, filename='analytics.png') 