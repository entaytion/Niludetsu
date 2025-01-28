import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu.utils.embed import create_embed
from Niludetsu.core.base import EMOJIS
import qrcode
import io

class QR(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="qr", description="Создать QR-код из текста или ссылки")
    @app_commands.describe(
        content="Текст или ссылка для QR-кода",
        size="Размер QR-кода (от 1 до 10, по умолчанию 5)"
    )
    async def qr(
        self,
        interaction: discord.Interaction,
        content: str,
        size: int = 5
    ):
        await interaction.response.defer()

        try:
            # Перевіряємо розмір
            if not 1 <= size <= 10:
                await interaction.followup.send(
                    embed=create_embed(
                        description="Размер должен быть от 1 до 10!"
                    )
                )
                return

            # Створюємо QR-код
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=size * 10,
                border=2,
            )
            qr.add_data(content)
            qr.make(fit=True)

            # Створюємо зображення
            qr_image = qr.make_image(fill_color="black", back_color="white")

            # Зберігаємо зображення в байти
            with io.BytesIO() as image_binary:
                qr_image.save(image_binary, 'PNG')
                image_binary.seek(0)
                
                # Відправляємо QR-код
                await interaction.followup.send(
                    embed=create_embed(
                        title="🔲 QR-код создан",
                        description=f"Содержимое: `{content}`"
                    ),
                    file=discord.File(fp=image_binary, filename='qr.png')
                )

        except Exception as e:
            await interaction.followup.send(
                embed=create_embed(
                    description=f"Произошла ошибка при создании QR-кода: {str(e)}"
                )
            )

async def setup(bot):
    await bot.add_cog(QR(bot)) 