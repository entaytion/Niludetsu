import discord
import json
import io
from datetime import datetime, timezone
from discord.ext import commands
from Niludetsu import Emojis

class JSONEmbed(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(name="embedjson", aliases=["jsonembed", "loadjson"])
    @commands.has_permissions(administrator=True)
    async def embed_json(self, ctx: commands.Context) -> None:
        """
        Отправляет сообщение, созданное из JSON файла (формат Discohook).
        Использование: !embedjson (прикрепите .json файл)
        """
        if not ctx.message.attachments:
            await ctx.reply(f"{Emojis.ERROR} Пожалуйста, прикрепите JSON файл с данными сообщения.")
            return

        attachment = ctx.message.attachments[0]
        if not attachment.filename.endswith('.json'):
            await ctx.reply(f"{Emojis.ERROR} Файл должен иметь расширение .json.")
            return

        try:
            file_content = await attachment.read()
            data = json.loads(file_content)
        except json.JSONDecodeError:
            await ctx.reply(f"{Emojis.ERROR} Неверный формат JSON файла.")
            return
        except Exception as e:
            await ctx.reply(f"{Emojis.ERROR} Ошибка при чтении файла: {e}")
            return

        # Нормализация структуры данных
        content = None
        embeds_data = []
        components_data = []

        if isinstance(data, list):
            # Если это список, то это список эмбедов
            embeds_data = data
        elif isinstance(data, dict):
            # Проверяем, является ли это структурой сообщения (Discohook/Webhook)
            if any(key in data for key in ("content", "embeds", "components")):
                content = data.get("content")
                embeds_data = data.get("embeds", [])
                components_data = data.get("components", [])
            else:
                # Иначе считаем, что это один объект эмбеда
                embeds_data = [data]

        # Парсинг Embeds
        embeds = []
        for embed_dict in embeds_data:
            try:
                # Исправление Timestamp (если число)
                if "timestamp" in embed_dict and isinstance(embed_dict["timestamp"], (int, float)):
                    try:
                        # Обычно JS timestamp в миллисекундах
                        ts = embed_dict["timestamp"]
                        if ts > 1000000000000: # Грубая проверка на мс
                             ts = ts / 1000.0
                        dt = datetime.fromtimestamp(ts, timezone.utc)
                        embed_dict["timestamp"] = dt.isoformat()
                    except:
                        pass

                # discord.Embed.from_dict ожидает корректную структуру API Discord
                if "color" in embed_dict:
                     val = embed_dict["color"]
                     if isinstance(val, str):
                         # Конвертация HEX string (#ffffff) -> int
                         try:
                            embed_dict["color"] = int(val.replace("#", ""), 16)
                         except:
                            pass
                
                embed = discord.Embed.from_dict(embed_dict)
                embeds.append(embed)
            except Exception as e:
                await ctx.reply(f"{Emojis.ERROR} Ошибка при создании Embed: {e}")
                return

        # Парсинг Components (Кнопки)
        view = discord.ui.View() if components_data else None
        
        if components_data:
            has_valid_components = False
            for row in components_data:
                # Discohook структура: components -> list of rows -> row['components'] -> list of items
                # Иногда структура может быть плоской, но стандартно это список ActionRow
                
                # Проверка: если это ActionRow (Type 1), идем внутрь
                items = row.get("components", []) if row.get("type") == 1 else [row] # fallback на случай странной структуры
                
                for component in items:
                    if component.get("type") == 2: # Button
                        style_value = component.get("style", 1)
                        label = component.get("label")
                        emoji = component.get("emoji")
                        url = component.get("url")
                        custom_id = component.get("custom_id")
                        disabled = component.get("disabled", False)

                        # Преобразуем emoji dict в объект или строку, если есть
                        discord_emoji = None
                        if isinstance(emoji, dict):
                            # Попытка воссоздать эмодзи
                            e_id = emoji.get("id")
                            e_name = emoji.get("name")
                            if e_id:
                                discord_emoji = f"<:{e_name}:{e_id}>" if not emoji.get("animated") else f"<a:{e_name}:{e_id}>"
                            elif e_name:
                                discord_emoji = e_name
                        elif isinstance(emoji, str):
                            discord_emoji = emoji

                        try:
                            style = discord.ButtonStyle(style_value)
                        except ValueError:
                            style = discord.ButtonStyle.secondary

                        # Создаем кнопку
                        button = discord.ui.Button(
                            style=style,
                            label=label,
                            emoji=discord_emoji,
                            url=url,
                            disabled=disabled,
                            row=None # авто-распределение
                        )
                        
                        # Если кнопка не Link, она не будет работать без callback.
                        # Добавим ей заглушку или просто custom_id
                        if style != discord.ButtonStyle.link:
                             button.custom_id = custom_id or f"no_callback_{json.dumps(label)}"
                        
                        view.add_item(button)
                        has_valid_components = True

            if not has_valid_components:
                view = None

        try:
            await ctx.send(content=content, embeds=embeds, view=view)
            await ctx.message.add_reaction("✅")
        except discord.HTTPException as e:
            await ctx.reply(f"{Emojis.ERROR} Ошибка Discord API при отправке: {e}")

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(JSONEmbed(bot))
