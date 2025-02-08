import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import typing
import json

def truncate_text(text: str, max_length: int = 1900) -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."

def nsfw_check():
    async def predicate(interaction: discord.Interaction) -> bool:
        if not interaction.channel.nsfw:
            await interaction.response.send_message("Эта команда может быть использована только в NSFW каналах!", ephemeral=True)
            return False
        return True
    return app_commands.check(predicate)

class NSFW(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_url = "https://api.waifu.im/search"
        self.headers = {
            "Accept": "application/json"
        }
        
    @app_commands.command(name="nsfw", description="Получить NSFW изображение")
    @nsfw_check()
    async def nsfw(self, interaction: discord.Interaction, category: typing.Literal[
        "ass", "hentai", "milf", "oral", "paizuri", "ecchi", "ero"
    ]):
        """
        Получить NSFW изображение из выбранной категории
        
        Parameters
        -----------
        category: Категория изображения
        """
        await interaction.response.defer()
        
        params = {
            "included_tags": category,
            "is_nsfw": "true"
        }
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(self.api_url, params=params) as response:
                try:
                    if response.status == 200:
                        try:
                            data = await response.json()
                            if data.get("images") and len(data["images"]) > 0:
                                image = data["images"][0]
                                embed = discord.Embed(color=discord.Color.random())
                                embed.set_image(url=image["url"])
                                embed.set_footer(text=f"Запрошено: {interaction.user.name}")
                                await interaction.followup.send(embed=embed)
                            else:
                                error_msg = f"Ошибка в ответе API: {json.dumps(data, ensure_ascii=False)}"
                                await interaction.followup.send(
                                    truncate_text(error_msg),
                                    ephemeral=True
                                )
                        except json.JSONDecodeError as e:
                            error_msg = f"Ошибка при обработке JSON ответа: {str(e)}"
                            await interaction.followup.send(
                                truncate_text(error_msg),
                                ephemeral=True
                            )
                    else:
                        error_msg = f"Ошибка API: Статус {response.status}"
                        await interaction.followup.send(
                            truncate_text(error_msg),
                            ephemeral=True
                        )
                except Exception as e:
                    error_msg = f"Непредвиденная ошибка: {str(e)}"
                    await interaction.followup.send(
                        truncate_text(error_msg),
                        ephemeral=True
                    )

async def setup(bot):
    await bot.add_cog(NSFW(bot)) 