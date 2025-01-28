import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu.utils.embed import create_embed
from Niludetsu.core.base import EMOJIS

class Avatar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="avatar", description="Показать аватар пользователя")
    @app_commands.describe(
        user="Пользователь, чей аватар вы хотите посмотреть"
    )
    async def avatar(
        self, 
        interaction: discord.Interaction, 
        user: discord.Member = None
    ):
        # Если пользователь не указан, показываем аватар автора команды
        target = user or interaction.user
        
        # Получаем URL аватарки в разных форматах
        avatar_formats = {
            'png': target.avatar.with_format('png').url if target.avatar else target.default_avatar.url,
            'jpg': target.avatar.with_format('jpg').url if target.avatar else None,
            'webp': target.avatar.with_format('webp').url if target.avatar else None,
            'gif': target.avatar.with_format('gif').url if target.avatar and target.avatar.is_animated() else None
        }
        
        # Создаем эмбед
        embed = create_embed(
            title=f"{EMOJIS['AVATAR']} Аватар {'вашего профиля' if target == interaction.user else f'профиля {target.name}'}",
            description="",
            color="BLUE",
            image_url=avatar_formats['png']  # По умолчанию показываем PNG
        )
        
        # Добавляем поле с ссылками на разные форматы
        links = []
        for format, url in avatar_formats.items():
            if url:
                links.append(f"[{format.upper()}]({url})")
        
        if links:
            embed.description = f"{EMOJIS['DOWNLOAD']} Скачать: " + " • ".join(links)
        
        # Создаем кнопки для просмотра в разных форматах
        class AvatarView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
                
            @discord.ui.button(label="PNG", style=discord.ButtonStyle.gray)
            async def png_button(self, i: discord.Interaction, button: discord.ui.Button):
                embed.set_image(url=avatar_formats['png'])
                await i.response.edit_message(embed=embed)
            
            @discord.ui.button(label="JPG", style=discord.ButtonStyle.gray)
            async def jpg_button(self, i: discord.Interaction, button: discord.ui.Button):
                if avatar_formats['jpg']:
                    embed.set_image(url=avatar_formats['jpg'])
                    await i.response.edit_message(embed=embed)
                else:
                    await i.response.send_message("JPG формат недоступен")
            
            @discord.ui.button(label="WEBP", style=discord.ButtonStyle.gray)
            async def webp_button(self, i: discord.Interaction, button: discord.ui.Button):
                if avatar_formats['webp']:
                    embed.set_image(url=avatar_formats['webp'])
                    await i.response.edit_message(embed=embed)
                else:
                    await i.response.send_message("WEBP формат недоступен")
            
            @discord.ui.button(label="GIF", style=discord.ButtonStyle.gray)
            async def gif_button(self, i: discord.Interaction, button: discord.ui.Button):
                if avatar_formats['gif']:
                    embed.set_image(url=avatar_formats['gif'])
                    await i.response.edit_message(embed=embed)
                else:
                    await i.response.send_message("GIF формат недоступен")
        
        # Отправляем сообщение
        await interaction.response.send_message(
            embed=embed,
            view=AvatarView()
        )

async def setup(bot):
    await bot.add_cog(Avatar(bot)) 