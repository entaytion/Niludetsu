import discord, matplotlib.pyplot as plt, io
from .base import BaseAnalytics, COLORS
from Niludetsu import Emojis, Embed

class ChannelsAnalytics(BaseAnalytics):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        
    async def generate_analytics(self, guild):
        """Генерирует аналитику каналов"""
        # Собираем статистику по типам каналов
        text_channels = guild.text_channels
        voice_channels = guild.voice_channels
        categories = guild.categories
        forum_channels = [c for c in guild.channels if isinstance(c, discord.ForumChannel)]
        stage_channels = [c for c in guild.channels if isinstance(c, discord.StageChannel)]
        
        # Статистика по правам доступа
        private_text = len([c for c in text_channels if not c.permissions_for(guild.default_role).view_channel])
        private_voice = len([c for c in voice_channels if not c.permissions_for(guild.default_role).view_channel])
        
        # Создаем круговую диаграмму типов каналов
        fig, ax = plt.subplots(figsize=(10, 5))
        
        # Собираем только непустые категории
        channel_data = [
            ('Текстовые', len(text_channels)),
            ('Голосовые', len(voice_channels)),
            ('Форумы', len(forum_channels)),
            ('Трибуны', len(stage_channels)),
            ('Категории', len(categories))
        ]
        
        # Фильтруем только непустые категории
        channel_data = [(name, count) for name, count in channel_data if count > 0]
        
        # Разделяем данные
        channel_types, sizes = zip(*channel_data) if channel_data else ([], [])
        
        # Создаем градиент красных оттенков
        colors = ['#ED4245', '#FF6B6B', '#FF8585', '#FFA3A3', '#FFC1C1'][:len(channel_types)]
        
        # Создаем круговую диаграмму
        wedges, texts, autotexts = ax.pie(
            sizes, 
            labels=channel_types, 
            colors=colors, 
            autopct='%1.1f%%',
            pctdistance=0.85,
            labeldistance=1.1
        )
        
        # Настраиваем шрифты для меток и процентов
        plt.setp(autotexts, size=9, weight="bold")
        plt.setp(texts, size=10, weight="bold")
        
        for text in texts + autotexts:
            text.set_fontproperties(self.custom_font)
            text.set_color(COLORS['text'])
        
        ax.set_title('Распределение типов каналов')
        
        self.style_plot(fig, ax)
        
        # Сохраняем график
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', transparent=True, dpi=300, bbox_inches='tight')
        buffer.seek(0)
        plt.close()
        
        # Создаем эмбед
        embed = Embed(
            title=f"{Emojis.CHANNELS} Аналитика каналов {guild.name}",
            description=f"{Emojis.INFO} Подробная статистика каналов сервера"
        )
        
        # Общая статистика
        embed.add_field(
            name=f"{Emojis.STATS} Общая статистика",
            value=f"{Emojis.DOT} **Всего каналов:** `{len(guild.channels)}`\n"
                  f"{Emojis.DOT} **Текстовых:** `{len(text_channels)}`\n"
                  f"{Emojis.DOT} **Голосовых:** `{len(voice_channels)}`\n"
                  f"{Emojis.DOT} **Форумов:** `{len(forum_channels)}`\n"
                  f"{Emojis.DOT} **Трибун:** `{len(stage_channels)}`\n"
                  f"{Emojis.DOT} **Категорий:** `{len(categories)}`",
            inline=True
        )
        
        # Статистика по доступу
        embed.add_field(
            name=f"{Emojis.SHIELD} Приватность",
            value=f"{Emojis.DOT} **Приватных текстовых:** `{private_text}`\n"
                  f"{Emojis.DOT} **Приватных голосовых:** `{private_voice}`\n"
                  f"{Emojis.DOT} **Публичных текстовых:** `{len(text_channels) - private_text}`\n"
                  f"{Emojis.DOT} **Публичных голосовых:** `{len(voice_channels) - private_voice}`",
            inline=True
        )
        
        # Дополнительная статистика
        news_channels = len([c for c in text_channels if c.is_news()])
        nsfw_channels = len([c for c in text_channels if c.is_nsfw()])
        slowmode_channels = len([c for c in text_channels if c.slowmode_delay > 0])
        
        embed.add_field(
            name=f"{Emojis.FEATURES} Дополнительно",
            value=f"{Emojis.DOT} **Новостных каналов:** `{news_channels}`\n"
                  f"{Emojis.DOT} **NSFW каналов:** `{nsfw_channels}`\n"
                  f"{Emojis.DOT} **Слоумод каналов:** `{slowmode_channels}`\n"
                  f"{Emojis.DOT} **Тредов:** `{sum(len(c.threads) for c in text_channels)}`",
            inline=True
        )
        
        embed.set_image(url="attachment://channels.png")
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
            
        return embed, discord.File(buffer, filename='channels.png') 