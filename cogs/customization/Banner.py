import aiohttp, discord, io, os, time
from collections import defaultdict
from discord.ext import commands, tasks
from Niludetsu.config import SERVERS
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, List, Set

class Banner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.message_cache: Dict[int, List[tuple]] = defaultdict(list)
        self.active_users_cache: Set[int] = set()
        self.banner_path = os.path.join("data", "images", "banner.jpg")
        self.font_path = os.path.join("data", "fonts", "Bounded-Variable.ttf")
        self.session = None
        self.excluded_category_id = 1363075274018914354
        self.waiting_for_update: Set[int] = set()
        self.banner_available = False  # Флаг доступности баннера

    async def cog_load(self):
        """Инициализация при загрузке кога"""
        self.session = aiohttp.ClientSession()

        # Проверяем доступность баннера для основного сервера
        guild = self.bot.get_guild(SERVERS["MAIN_ID"])
        if guild:
            # Проверяем наличие функции баннера (требуется уровень буста 2+)
            if "BANNER" in guild.features:
                self.banner_available = True
                print("✓ Баннер доступен. Модуль Banner запущен.")
            else:
                print("⚠ Баннер недоступен. Недостаточно бустов (требуется уровень 2+).")
                print("  Модуль Banner не будет активен.")
        else:
            print("⚠ Основной сервер не найден. Модуль Banner не будет активен.")

    def cog_unload(self):
        """Закрываем сессию при выгрузке кога"""
        self.update_banner.cancel()
        if self.session and not self.session.closed:
            self.bot.loop.create_task(self.session.close())

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Если баннер недоступен — не обрабатываем сообщения
        if not self.banner_available:
            return

        if message.guild is None or message.author.bot:
            return

        # Работаем только на основном сервере
        if message.guild.id != SERVERS["MAIN_ID"]:
            return

        # Проверяем, не находится ли канал в исключенной категории
        if message.channel.category_id == self.excluded_category_id:
            return

        # Сохраняем длину сообщения и время
        self.message_cache[message.author.id].append((len(message.content), time.time()))

        # Удаляем старые записи (старше 5 минут)
        current_time = time.time()
        self.message_cache[message.author.id] = [
            (length, timestamp) for length, timestamp in self.message_cache[message.author.id]
            if current_time - timestamp <= 300
        ]

        # Добавляем пользователя в кеш активных
        if self.message_cache[message.author.id]:
            self.active_users_cache.add(message.author.id)

        # Если ждем первого сообщения — обновляем баннер сразу
        guild_id = message.guild.id
        if guild_id in self.waiting_for_update and message.guild.me.guild_permissions.manage_guild:
            voice_count = self.get_voice_users_count(message.guild)
            banner_buffer = await self.create_banner(message.author, voice_count)
            try:
                await message.guild.edit(banner=banner_buffer.getvalue())
            except discord.HTTPException:
                pass
            self.waiting_for_update.discard(guild_id)

    def get_most_active_user(self, guild: discord.Guild) -> discord.Member:
        """Выбирает самого активного пользователя по количеству сообщений за 5 минут"""
        current_time = time.time()
        max_count = 0
        selected_member = None

        for user_id, messages in self.message_cache.items():
            recent_msgs = [msg for msg in messages if current_time - msg[1] <= 300]
            if len(recent_msgs) > max_count:
                member = guild.get_member(user_id)
                if member:
                    max_count = len(recent_msgs)
                    selected_member = member

        return selected_member

    def get_voice_users_count(self, guild: discord.Guild) -> int:
        """Получает количество пользователей в голосовых каналах"""
        count = 0
        for channel in guild.voice_channels:
            if channel.category_id == self.excluded_category_id:
                continue
            count += len(channel.members)
        return min(count, 9)

    def create_circular_mask(self, size):
        """Создает круглую маску для аватарки"""
        mask = Image.new('L', size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0) + size, fill=255)
        return mask

    async def create_banner(self, member: discord.Member, voice_count: int) -> io.BytesIO:
        """Создает баннер с информацией о пользователе"""
        with Image.open(self.banner_path) as img:
            draw = ImageDraw.Draw(img)
            font = ImageFont.truetype(self.font_path, 32)

            # Никнейм (обрезаем если длинный)
            username = member.name
            if len(username) > 12:
                username = username[:9] + "..."

            draw.text((250, 293), username, font=font, fill="white")

            # Аватар (круглый)
            avatar_url = str(member.display_avatar.with_format("png").url)
            async with self.session.get(avatar_url) as response:
                avatar_data = await response.read()
                with Image.open(io.BytesIO(avatar_data)) as avatar:
                    avatar = avatar.convert('RGBA').resize((180, 180))
                    output = Image.new('RGBA', (180, 180), (0, 0, 0, 0))
                    mask = self.create_circular_mask((180, 180))

                    for x in range(180):
                        for y in range(180):
                            if mask.getpixel((x, y)) > 0:
                                output.putpixel((x, y), avatar.getpixel((x, y)))

                    img.paste(output, (52, 223), output)

            # Онлайн в голосовых
            draw.text((750, 293), str(voice_count), font=font, fill="white")

            # Всего участников
            total_members = member.guild.member_count if hasattr(member.guild, 'member_count') else 0
            draw.text((739, 373), str(total_members), font=font, fill="white")

            buffer = io.BytesIO()
            img.save(buffer, format='JPEG')
            buffer.seek(0)
            return buffer

    @tasks.loop(minutes=5)
    async def update_banner(self):
        """Обновляет баннер каждые 5 минут"""
        # Если баннер недоступен — не обновляем
        if not self.banner_available:
            return

        guild = self.bot.get_guild(SERVERS["MAIN_ID"])
        if not guild or not guild.me.guild_permissions.manage_guild:
            return

        current_time = time.time()

        # Очищаем устаревшие сообщения
        active_members = []
        for user_id, messages in list(self.message_cache.items()):
            recent_msgs = [(length, ts) for length, ts in messages if current_time - ts <= 300]
            self.message_cache[user_id] = recent_msgs

            if recent_msgs:
                member = guild.get_member(user_id)
                if member:
                    active_members.append(member)

        # Если нет активных — ждем первого сообщения
        if not active_members:
            self.waiting_for_update.add(guild.id)
            return

        # Выбираем самого активного
        selected_member = self.get_most_active_user(guild)
        if not selected_member:
            self.waiting_for_update.add(guild.id)
            return

        self.waiting_for_update.discard(guild.id)

        voice_count = self.get_voice_users_count(guild)
        banner_buffer = await self.create_banner(selected_member, voice_count)

        try:
            await guild.edit(banner=banner_buffer.getvalue())
        except discord.HTTPException:
            pass

    @commands.Cog.listener()
    async def on_ready(self):
        """Запускает ротацию баннера при старте бота"""
        if self.banner_available:
            self.update_banner.start()

async def setup(bot):
    await bot.add_cog(Banner(bot))

