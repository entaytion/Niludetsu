import discord
import matplotlib.pyplot as plt
import io
from collections import Counter
from .base import BaseAnalytics, COLORS
from Niludetsu.utils.constants import Emojis
from Niludetsu.utils.embed import Embed

class ServerAnalytics(BaseAnalytics):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        
    async def generate_analytics(self, guild):
        """Генерирует аналитику сервера"""
        # Основная статистика
        total_members = guild.member_count
        total_humans = len([m for m in guild.members if not m.bot])
        total_bots = len([m for m in guild.members if m.bot])
        
        # Статистика по статусам
        statuses = Counter([member.status for member in guild.members])
        
        # Статистика каналов
        total_channels = len(guild.channels)
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        forum_channels = len([c for c in guild.channels if isinstance(c, discord.ForumChannel)])
        stage_channels = len([c for c in guild.channels if isinstance(c, discord.StageChannel)])
        
        # Статистика ролей
        roles = len(guild.roles) - 1  # Исключаем @everyone
        
        # Статистика эмодзи и стикеров
        emojis = len(guild.emojis)
        animated_emojis = len([e for e in guild.emojis if e.animated])
        static_emojis = emojis - animated_emojis
        stickers = len(guild.stickers)
        
        # Уровень буста
        boost_level = guild.premium_tier
        boost_count = guild.premium_subscription_count
        boosters = len(guild.premium_subscribers)
        
        # Создаем график активности по дням недели
        plt.figure(figsize=(10, 5))
        ax = plt.gca()
        
        days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        member_joins = [0] * 7
        
        for member in guild.members:
            if member.joined_at:
                day = member.joined_at.weekday()
                member_joins[day] += 1
        
        bars = ax.bar(days, member_joins, color=COLORS['primary'])
        
        # Добавляем значения над столбцами
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}',
                   ha='center', va='bottom',
                   color=COLORS['text'],
                   fontproperties=self.custom_font)
        
        ax.set_title('Статистика присоединений по дням недели')
        ax.set_xlabel('День недели')
        ax.set_ylabel('Количество участников')
        
        self.style_plot(plt.gcf(), ax)
        
        # Устанавливаем отступы вручную
        plt.subplots_adjust(left=0.12, right=0.95, top=0.9, bottom=0.1)
        
        # Сохраняем график
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=300)
        buffer.seek(0)
        plt.close()
        
        # Создаем эмбед
        embed = Embed(
            title=f"{Emojis.STATS} Аналитика сервера {guild.name}",
            description=f"{Emojis.INFO} Подробная статистика сервера",
            fields=[
                {
                    "name": f"{Emojis.MEMBERS} Участники",
                    "value": f"{Emojis.DOT} **Всего:** `{total_members}`\n"
                            f"{Emojis.DOT} **Людей:** `{total_humans}`\n"
                            f"{Emojis.DOT} **Ботов:** `{total_bots}`\n"
                            f"{Emojis.DOT} **Онлайн:** `{statuses[discord.Status.online]}`\n"
                            f"{Emojis.DOT} **Не активен:** `{statuses[discord.Status.idle]}`\n"
                            f"{Emojis.DOT} **Не беспокоить:** `{statuses[discord.Status.dnd]}`\n"
                            f"{Emojis.DOT} **Оффлайн:** `{statuses[discord.Status.offline]}`",
                    "inline": True
                },
                {
                    "name": f"{Emojis.CHANNELS} Каналы",
                    "value": f"{Emojis.DOT} **Всего:** `{total_channels}`\n"
                            f"{Emojis.DOT} **Текстовых:** `{text_channels}`\n"
                            f"{Emojis.DOT} **Голосовых:** `{voice_channels}`\n"
                            f"{Emojis.DOT} **Категорий:** `{categories}`\n"
                            f"{Emojis.DOT} **Форумов:** `{forum_channels}`\n"
                            f"{Emojis.DOT} **Трибун:** `{stage_channels}`",
                    "inline": True
                },
                {
                    "name": f"{Emojis.FEATURES} Контент",
                    "value": f"{Emojis.DOT} **Ролей:** `{roles}`\n"
                            f"{Emojis.DOT} **Эмодзи:** `{emojis}`\n"
                            f"{Emojis.DOT} **Анимированных:** `{animated_emojis}`\n"
                            f"{Emojis.DOT} **Статичных:** `{static_emojis}`\n"
                            f"{Emojis.DOT} **Стикеров:** `{stickers}`",
                    "inline": True
                },
                {
                    "name": f"{Emojis.BOOST} Буст статус",
                    "value": f"{Emojis.DOT} **Уровень:** `{boost_level}`\n"
                            f"{Emojis.DOT} **Бустов:** `{boost_count}`\n"
                            f"{Emojis.DOT} **Бустеров:** `{boosters}`\n"
                            f"{Emojis.DOT} **До следующего уровня:** `{2 if boost_level == 0 else (7 if boost_level == 1 else (14 if boost_level == 2 else 0)) - boost_count if boost_level < 3 else 0} бустов`",
                    "inline": True
                },
                {
                    "name": f"{Emojis.SHIELD} Безопасность",
                    "value": f"{Emojis.DOT} **Уровень проверки:** `{guild.verification_level}`\n"
                            f"{Emojis.DOT} **Фильтр контента:** `{guild.explicit_content_filter}`\n"
                            f"{Emojis.DOT} **2FA для модерации:** `{'Включено' if guild.mfa_level else 'Выключено'}`\n"
                            f"{Emojis.DOT} **Уровень NSFW:** `{guild.nsfw_level}`",
                    "inline": True
                },
                {
                    "name": f"{Emojis.SETTINGS} Дополнительно",
                    "value": f"{Emojis.DOT} **Владелец:** {guild.owner.mention}\n"
                            f"{Emojis.DOT} **Регион:** `{str(guild.preferred_locale)}`\n"
                            f"{Emojis.DOT} **Максимум участников:** `{guild.max_members}`\n"
                            f"{Emojis.DOT} **Лимит файлов:** `{guild.filesize_limit // 1048576}MB`",
                    "inline": True
                }
            ],
            color="DEFAULT"
        )
        
        embed.set_image(url="attachment://analytics.png")
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
            
        embed.set_footer(text=f"ID: {guild.id} • Сервер создан")
        embed.timestamp = guild.created_at
        
        return embed, discord.File(buffer, filename='analytics.png') 