import discord
from discord.ext import commands
from Niludetsu.utils.embed import Embed
from mcstatus import JavaServer
import datetime
import asyncio

class MCServer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def format_motd(self, motd):
        if hasattr(motd, 'to_plain'):
            return motd.to_plain()
        return str(motd)

    def format_time(self, seconds):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}ч {minutes}м"

    @discord.app_commands.command(name="mcserver", description="Получить подробную информацию о сервере Minecraft")
    @discord.app_commands.describe(ip="IP-адрес сервера")
    async def mcserver(self, interaction: discord.Interaction, ip: str):
        await interaction.response.defer()
        
        server = JavaServer.lookup(ip)
        status = await server.async_status()
        
        # Получаем базовую информацию о сервере
        online = status.players.online
        max_players = status.players.max
        version = status.version.name
        latency = round(status.latency, 2)
        protocol = status.version.protocol
        
        # Получаем MOTD
        motd = self.format_motd(status.description)
        
        # Вычисляем процент заполненности
        player_percentage = (online / max_players) * 100 if max_players > 0 else 0
        progress_bar = "█" * int(player_percentage / 10) + "░" * (10 - int(player_percentage / 10))
        
        # Определяем статус сервера
        if online == 0:
            server_status = "🔴 Пусто"
        elif online >= max_players:
            server_status = "🟡 Заполнен"
        else:
            server_status = "🟢 Активен"

        # Пробуем получить дополнительную информацию через query
        try:
            query = await asyncio.wait_for(server.async_query(), timeout=2.0)
            has_query = True
            software = query.software
            plugins = query.plugins
            game_type = query.game_type
            map_name = query.map
        except:
            has_query = False
        
        # Проверяем наличие модов
        has_forge = False
        mod_info = ""
        if hasattr(status, 'forge_data'):
            has_forge = True
            if hasattr(status.forge_data, 'mods'):
                mods = status.forge_data.mods
                mod_info = f"Количество модов: {len(mods)}\n"
                # Показываем первые 5 модов
                if mods:
                    mod_list = [f"• {mod.name} ({mod.version})" for mod in mods[:5]]
                    mod_info += "Основные моды:\n" + "\n".join(mod_list)
                    if len(mods) > 5:
                        mod_info += f"\n...и еще {len(mods) - 5} модов"
        
        # Формируем поля для эмбеда
        fields = [
            ("📊 Статус", server_status, True),
            ("👥 Игроки", f"{online}/{max_players} ({player_percentage:.1f}%)", True),
            ("🏓 Пинг", f"{latency}мс", True),
            ("🔧 Версия", f"{version} (Protocol: {protocol})", True),
            ("⚡ Загруженность", f"`{progress_bar}`", False),
        ]
        
        if has_query:
            fields.extend([
                ("🖥️ Программное обеспечение", software, True),
                ("🗺️ Карта", map_name, True),
                ("🎮 Тип игры", game_type, True)
            ])
            
            if plugins:
                plugins_str = "\n".join([f"• {plugin}" for plugin in plugins[:5]])
                if len(plugins) > 5:
                    plugins_str += f"\n...и еще {len(plugins) - 5} плагинов"
                fields.append(("🔌 Плагины", f"```{plugins_str}```", False))
        
        if has_forge and mod_info:
            fields.append(("🛠️ Моды", f"```{mod_info}```", False))
        
        if motd:
            fields.append(("📝 MOTD", f"```{motd}```", False))
        
        # Создаем основной эмбед
        embed=Embed(
            title=f"🎮 Информация о сервере Minecraft",
            description=f"**IP:** `{ip}`\n\n",
            color="GREEN" if online > 0 else "RED"
        )
        
        # Добавляем все поля
        for name, value, inline in fields:
            if value:  # Добавляем только непустые поля
                embed.add_field(name=name, value=value, inline=inline)
        
        # Если есть игроки онлайн, добавляем их список
        if status.players.sample:
            players_list = "\n".join([f"• {player.name}" for player in status.players.sample])
            embed.add_field(
                name="👤 Игроки онлайн",
                value=f"```{players_list}```",
                inline=False
            )
        
        # Добавляем время запроса и дополнительную информацию
        footer_text = f"Обновлено • {datetime.datetime.now().strftime('%H:%M:%S')}"
        if has_query:
            footer_text += " | Query доступен"
        if has_forge:
            footer_text += " | Forge сервер"
        embed.set_footer(text=footer_text)
        
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(MCServer(bot)) 