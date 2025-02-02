import discord
from discord.ext import commands, tasks
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import io
import os

class Birthday(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_birthdays.start()
        self.font_path = "assets/fonts/Montserrat-Bold.ttf"  # Путь к шрифту
        self.template_path = "assets/images/birthday.png"  # Путь к шаблону картинки
        
    def cog_unload(self):
        self.check_birthdays.cancel()
        
    async def create_birthday_image(self, name):
        """Создает изображение с поздравлением"""
        try:
            # Открываем шаблон
            img = Image.open(self.template_path)
            draw = ImageDraw.Draw(img)
            
            # Загружаем шрифт
            font = ImageFont.truetype(self.font_path, 60)
            
            # Вычисляем позицию для текста (центрирование)
            text = f"С днем рождения, {name}!"
            text_width = draw.textlength(text, font=font)
            x = (img.width - text_width) / 2
            y = img.height / 2  # Можно настроить позицию по вертикали
            
            # Добавляем текст
            draw.text((x, y), text, font=font, fill=(255, 255, 255))  # Белый цвет текста
            
            # Конвертируем в bytes
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            
            return buffer
            
        except Exception as e:
            print(f"Ошибка при создании изображения: {e}")
            return None
        
    @tasks.loop(hours=24)
    async def check_birthdays(self):
        """Проверяет дни рождения пользователей"""
        try:
            # Получаем текущую дату
            current_date = datetime.now().strftime("%d.%M")
            
            # Получаем всех пользователей, у которых сегодня день рождения
            async with self.bot.pool.acquire() as conn:
                users = await conn.fetch(
                    "SELECT user_id, name FROM users WHERE birthday = $1",
                    current_date
                )
                
            if not users:
                return
                
            # Получаем канал для поздравлений
            channel_id = self.bot.config.get("birthdays", {}).get("channel")
            if not channel_id:
                return
                
            channel = self.bot.get_channel(int(channel_id))
            if not channel:
                return
                
            # Поздравляем каждого пользователя
            for user in users:
                member = channel.guild.get_member(int(user['user_id']))
                if not member:
                    continue
                    
                name = user['name'] or member.display_name
                
                # Создаем изображение с поздравлением
                image_buffer = await self.create_birthday_image(name)
                if not image_buffer:
                    continue
                
                # Отправляем сообщение с изображением
                file = discord.File(image_buffer, filename="birthday.png")
                await channel.send(
                    content=f"🎉 {member.mention}, поздравляем с днем рождения! Желаем всего наилучшего! 🎂",
                    file=file
                )
                
                # Выдаем подарок
                async with self.bot.pool.acquire() as conn:
                    await conn.execute(
                        "UPDATE users SET balance = balance + $1 WHERE user_id = $2",
                        1000,
                        str(member.id)
                    )
                    
        except Exception as e:
            print(f"Ошибка при проверке дней рождения: {e}")
            
    @check_birthdays.before_loop
    async def before_check_birthdays(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Birthday(bot)) 