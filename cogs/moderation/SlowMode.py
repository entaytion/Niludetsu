import discord
from discord import app_commands
from discord.ext import commands
import typing
from datetime import timedelta
from utils import create_embed, EMOJIS, has_mod_role, command_cooldown

def format_time(seconds: int) -> str:
    """Форматирует время в читаемый вид"""
    if seconds == 0:
        return "отключен"
    
    time = timedelta(seconds=seconds)
    parts = []
    
    days = time.days
    hours, remainder = divmod(time.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if days:
        parts.append(f"{days} {'день' if days == 1 else 'дней' if days >= 5 else 'дня'}")
    if hours:
        parts.append(f"{hours} {'час' if hours == 1 else 'часов' if hours >= 5 else 'часа'}")
    if minutes:
        parts.append(f"{minutes} {'минута' if minutes == 1 else 'минут' if minutes >= 5 else 'минуты'}")
    if seconds:
        parts.append(f"{seconds} {'секунда' if seconds == 1 else 'секунд' if seconds >= 5 else 'секунды'}")
    
    return ", ".join(parts)

class SlowMode(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    slowmode_group = app_commands.Group(name="slowmode", description="Управление медленным режимом")
    
    @slowmode_group.command(name="set", description="Установить медленный режим в канале")
    @app_commands.describe(
        seconds="Задержка в секундах (0-21600)",
        channel="Канал для установки медленного режима (по умолчанию - текущий)",
        all_channels="Применить ко всем текстовым каналам",
        reason="Причина установки медленного режима"
    )
    @app_commands.default_permissions(manage_channels=True)
    async def slowmode_set(
        self, 
        interaction: discord.Interaction, 
        seconds: app_commands.Range[int, 0, 21600],
        channel: typing.Optional[discord.TextChannel] = None,
        all_channels: typing.Optional[bool] = False,
        reason: typing.Optional[str] = None
    ):
        await interaction.response.defer()
        
        if all_channels:
            success_channels = []
            failed_channels = []
            
            for ch in interaction.guild.text_channels:
                try:
                    await ch.edit(
                        slowmode_delay=seconds,
                        reason=f"Медленный режим установлен {interaction.user} | Причина: {reason}" if reason else f"Медленный режим установлен {interaction.user}"
                    )
                    success_channels.append(ch.mention)
                except:
                    failed_channels.append(ch.mention)
            
            embed = create_embed(
                title="⏱️ Медленный режим изменен",
                description=f"Задержка: {format_time(seconds)}"
            )
            
            if success_channels:
                embed.add_field(
                    name=f"{EMOJIS['SUCCESS']} Успешно установлен в каналах:",
                    value=", ".join(success_channels) if len(", ".join(success_channels)) <= 1024 else f"Успешно в {len(success_channels)} каналах",
                    inline=False
                )
            
            if failed_channels:
                embed.add_field(
                    name=f"{EMOJIS['ERROR']} Не удалось установить в каналах:",
                    value=", ".join(failed_channels) if len(", ".join(failed_channels)) <= 1024 else f"Неудачно в {len(failed_channels)} каналах",
                    inline=False
                )
            
            if reason:
                embed.add_field(name="Причина", value=reason)
                
            embed.set_footer(text=f"Установил: {interaction.user}")
            
            await interaction.followup.send(embed=embed)
            return
            
        channel = channel or interaction.channel
        
        if not isinstance(channel, discord.TextChannel):
            await interaction.followup.send("❌ Медленный режим можно установить только в текстовом канале!")
            return
            
        try:
            await channel.edit(
                slowmode_delay=seconds,
                reason=f"Медленный режим установлен {interaction.user} | Причина: {reason}" if reason else f"Медленный режим установлен {interaction.user}"
            )
            
            embed = create_embed(
                title="⏱️ Медленный режим изменен",
                description=f"Канал: {channel.mention}\nЗадержка: {format_time(seconds)}"
            )
            
            if reason:
                embed.add_field(name="Причина", value=reason)
                
            embed.set_footer(text=f"Установил: {interaction.user}")
            
            await interaction.followup.send(embed=embed)
            
        except discord.Forbidden:
            await interaction.followup.send("❌ У меня нет прав для изменения медленного режима в этом канале!")
        except Exception as e:
            await interaction.followup.send(f"❌ Произошла ошибка: {str(e)}")
    
    @slowmode_group.command(name="off", description="Отключить медленный режим в канале")
    @app_commands.describe(
        channel="Канал для отключения медленного режима (по умолчанию - текущий)",
        all_channels="Отключить во всех текстовых каналах",
        reason="Причина отключения медленного режима"
    )
    @has_mod_role()
    @command_cooldown()
    async def slowmode_off(
        self,
        interaction: discord.Interaction,
        channel: typing.Optional[discord.TextChannel] = None,
        all_channels: typing.Optional[bool] = False,
        reason: typing.Optional[str] = None
    ):
        await interaction.response.defer()
        
        if all_channels:
            success_channels = []
            failed_channels = []
            
            for ch in interaction.guild.text_channels:
                try:
                    await ch.edit(
                        slowmode_delay=0,
                        reason=f"Медленный режим отключен {interaction.user} | Причина: {reason}" if reason else f"Медленный режим отключен {interaction.user}"
                    )
                    success_channels.append(ch.mention)
                except:
                    failed_channels.append(ch.mention)
            
            embed = create_embed(
                title="⏱️ Медленный режим отключен",
                description="Медленный режим отключен во всех каналах"
            )
            
            if success_channels:
                embed.add_field(
                    name=f"{EMOJIS['SUCCESS']} Успешно отключен в каналах:",
                    value=", ".join(success_channels) if len(", ".join(success_channels)) <= 1024 else f"Успешно в {len(success_channels)} каналах",
                    inline=False
                )
            
            if failed_channels:
                embed.add_field(
                    name=f"{EMOJIS['ERROR']} Не удалось отключить в каналах:",
                    value=", ".join(failed_channels) if len(", ".join(failed_channels)) <= 1024 else f"Неудачно в {len(failed_channels)} каналах",
                    inline=False
                )
            
            if reason:
                embed.add_field(name="Причина", value=reason)
                
            embed.set_footer(text=f"Отключил: {interaction.user}")
            
            await interaction.followup.send(embed=embed)
            return
            
        channel = channel or interaction.channel
        
        if not isinstance(channel, discord.TextChannel):
            await interaction.followup.send("❌ Медленный режим можно отключить только в текстовом канале!")
            return
            
        try:
            await channel.edit(
                slowmode_delay=0,
                reason=f"Медленный режим отключен {interaction.user} | Причина: {reason}" if reason else f"Медленный режим отключен {interaction.user}"
            )
            
            embed = create_embed(
                title="⏱️ Медленный режим отключен",
                description=f"Канал: {channel.mention}"
            )
            
            if reason:
                embed.add_field(name="Причина", value=reason)
                
            embed.set_footer(text=f"Отключил: {interaction.user}")
            
            await interaction.followup.send(embed=embed)
            
        except discord.Forbidden:
            await interaction.followup.send("❌ У меня нет прав для изменения медленного режима в этом канале!")
        except Exception as e:
            await interaction.followup.send(f"❌ Произошла ошибка: {str(e)}")
    
    @slowmode_group.command(name="info", description="Показать информацию о медленном режиме в канале")
    @app_commands.describe(
        channel="Канал для проверки (по умолчанию - текущий)",
        all_channels="Показать информацию о всех каналах"
    )
    async def slowmode_info(
        self,
        interaction: discord.Interaction,
        channel: typing.Optional[discord.TextChannel] = None,
        all_channels: typing.Optional[bool] = False
    ):
        await interaction.response.defer()
        
        if all_channels:
            embed = create_embed(
                title="⏱️ Информация о медленном режиме",
                description="Информация о всех текстовых каналах:"
            )
            
            # Группируем каналы по задержке
            channels_by_delay = {}
            for ch in interaction.guild.text_channels:
                delay = ch.slowmode_delay
                if delay not in channels_by_delay:
                    channels_by_delay[delay] = []
                channels_by_delay[delay].append(ch.mention)
            
            # Сортируем задержки
            for delay in sorted(channels_by_delay.keys()):
                channels = channels_by_delay[delay]
                field_value = ", ".join(channels)
                
                # Если значение слишком длинное, показываем только количество
                if len(field_value) > 1024:
                    field_value = f"{len(channels)} каналов"
                
                embed.add_field(
                    name=f"Задержка: {format_time(delay)}",
                    value=field_value,
                    inline=False
                )
            
            await interaction.followup.send(embed=embed)
            return
            
        channel = channel or interaction.channel
        
        if not isinstance(channel, discord.TextChannel):
            await interaction.followup.send("❌ Медленный режим есть только в текстовых каналах!")
            return
            
        embed = create_embed(
            title="⏱️ Информация о медленном режиме",
            description=f"Канал: {channel.mention}\nТекущая задержка: {format_time(channel.slowmode_delay)}"
        )
        
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(SlowMode(bot))    