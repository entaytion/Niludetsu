import discord, matplotlib.pyplot as plt, io
from .base import BaseAnalytics, COLORS
from Niludetsu import Emojis, Embed

class RolesAnalytics(BaseAnalytics):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        
    async def generate_analytics(self, guild):
        """Генерирует аналитику ролей"""
        # Собираем статистику по ролям
        role_stats = []
        for role in guild.roles[1:]:  # Пропускаем @everyone
            members_count = len(role.members)
            role_stats.append({
                'name': role.name,
                'members': members_count,
                'color': role.color,
                'hoisted': role.hoist,
                'mentionable': role.mentionable,
                'position': role.position,
                'managed': role.managed,
                'permissions': role.permissions
            })
        
        # Сортируем по количеству участников
        role_stats.sort(key=lambda x: x['members'], reverse=True)
        
        # Создаем график топ-10 ролей
        fig, ax = plt.subplots(figsize=(10, 5))
        
        top_roles = role_stats[:10]
        names = [r['name'] for r in top_roles]
        members = [r['members'] for r in top_roles]
        
        # Создаем градиент цветов от primary до secondary
        colors = [COLORS['primary']] * len(names)
        
        bars = ax.bar(names, members, color=colors)
        
        # Добавляем значения над столбцами
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}',
                   ha='center', va='bottom',
                   color=COLORS['text'],
                   fontproperties=self.custom_font)
        
        plt.xticks(rotation=45, ha='right')
        ax.set_title('Топ-10 ролей по количеству участников')
        ax.set_xlabel('Роли')
        ax.set_ylabel('Количество участников')
        
        self.style_plot(fig, ax)
        
        # Сохраняем график
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', transparent=True, dpi=300, bbox_inches='tight')
        buffer.seek(0)
        plt.close()
        
        # Создаем эмбед
        embed = Embed(
            title=f"{Emojis.ROLES} Аналитика ролей {guild.name}",
            description=f"{Emojis.INFO} Подробная статистика ролей сервера"
        )
        
        # Общая статистика
        embed.add_field(
            name=f"{Emojis.STATS} Общая статистика",
            value=f"{Emojis.DOT} **Всего ролей:** `{len(guild.roles) - 1}`\n"
                  f"{Emojis.DOT} **Отображаемых отдельно:** `{len([r for r in guild.roles if r.hoist])}`\n"
                  f"{Emojis.DOT} **Упоминаемых:** `{len([r for r in guild.roles if r.mentionable])}`\n"
                  f"{Emojis.DOT} **Управляемых:** `{len([r for r in guild.roles if r.managed])}`\n"
                  f"{Emojis.DOT} **С цветом:** `{len([r for r in guild.roles if r.color != discord.Color.default()])}`",
            inline=False
        )
        
        # Топ-5 ролей
        top_5_text = "\n".join(f"{Emojis.DOT} {i+1}. {role['name']}: `{role['members']} участников`" 
                              for i, role in enumerate(role_stats[:5]))
        embed.add_field(name=f"{Emojis.CROWN} Топ-5 ролей", value=top_5_text, inline=False)
        
        # Роли с особыми правами
        admin_roles = len([r for r in guild.roles if r.permissions.administrator])
        mod_roles = len([r for r in guild.roles if any([
            r.permissions.kick_members,
            r.permissions.ban_members,
            r.permissions.manage_messages,
            r.permissions.manage_roles
        ])])
        
        embed.add_field(
            name=f"{Emojis.SHIELD} Права доступа",
            value=f"{Emojis.DOT} **Администраторы:** `{admin_roles}`\n"
                  f"{Emojis.DOT} **Модераторы:** `{mod_roles}`",
            inline=False
        )
        
        embed.set_image(url="attachment://roles.png")
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
            
        return embed, discord.File(buffer, filename='roles.png') 