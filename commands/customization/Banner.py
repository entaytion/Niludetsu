import discord, io, os, time
from collections import defaultdict
from discord.ext import commands, tasks
from Niludetsu import config
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, List, Set

class Banner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.message_cache: Dict[int, List[tuple]] = defaultdict(list)
        self.active_users_cache: Set[int] = set()
        self.banner_path = os.path.join("data", "images", "banner.jpg")
        self.font_path = os.path.join("data", "fonts", "Bounded-Variable.ttf")
        self.excluded_category_id = 1363075274018914354
        self.waiting_for_update: Set[int] = set()
        self.update_banner.start()

    def cog_unload(self) -> None:
        self.update_banner.cancel()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if not message.guild or message.author.bot or message.guild.id != config.SERVERS["MAIN_ID"]:
            return
        if message.channel.category_id == self.excluded_category_id:
            return

        now = time.time()
        self.message_cache[message.author.id].append((len(message.content), now))
        self.message_cache[message.author.id] = [
            (length, ts) for length, ts in self.message_cache[message.author.id]
            if now - ts <= 300
        ]
        if self.message_cache[message.author.id]:
            self.active_users_cache.add(message.author.id)

        guild_id = message.guild.id
        if guild_id in self.waiting_for_update and message.guild.me.guild_permissions.manage_guild:
            voice_count = self.get_voice_users_count(message.guild)
            banner_buffer = await self.create_banner(message.author, voice_count)
            try:
                await message.guild.edit(banner=banner_buffer.getvalue())
            except discord.HTTPException:
                pass
            self.waiting_for_update.discard(guild_id)

    def get_most_active_user(self, guild: discord.Guild) -> discord.Member | None:
        now = time.time()
        max_count = 0
        selected = None
        for user_id, messages in self.message_cache.items():
            recent = [msg for msg in messages if now - msg[1] <= 300]
            if len(recent) > max_count:
                member = guild.get_member(user_id)
                if member:
                    max_count = len(recent)
                    selected = member
        return selected

    def get_voice_users_count(self, guild: discord.Guild) -> int:
        count = sum(
            len(c.members) for c in guild.voice_channels
            if c.category_id != self.excluded_category_id
        )
        return min(count, 9)

    def create_circular_mask(self, size: tuple[int, int]) -> Image.Image:
        mask = Image.new("L", size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0) + size, fill=255)
        return mask

    def _build_banner_image(self, avatar_data: bytes, username: str, voice_count: int, total_members: int) -> io.BytesIO:
        with Image.open(self.banner_path) as img:
            draw = ImageDraw.Draw(img)
            font = ImageFont.truetype(self.font_path, 32)
            draw.text((250, 293), username, font=font, fill="white")
            with Image.open(io.BytesIO(avatar_data)) as avatar:
                avatar = avatar.convert("RGBA").resize((180, 180))
                mask = self.create_circular_mask((180, 180))
                output = Image.new("RGBA", (180, 180), (0, 0, 0, 0))
                output.paste(avatar, (0, 0), mask)
                img.paste(output, (52, 223), output)
            draw.text((750, 293), str(voice_count), font=font, fill="white")
            draw.text((739, 373), str(total_members), font=font, fill="white")
            buf = io.BytesIO()
            img.save(buf, format="JPEG")
            buf.seek(0)
            return buf

    async def create_banner(self, member: discord.Member, voice_count: int) -> io.BytesIO:
        username = member.name
        if len(username) > 12:
            username = username[:9] + "..."
        avatar_data = await member.display_avatar.with_format("png").read()
        total_members = member.guild.member_count or 0
        import asyncio
        return await asyncio.to_thread(
            self._build_banner_image, avatar_data, username, voice_count, total_members
        )

    @tasks.loop(minutes=5)
    async def update_banner(self) -> None:
        guild = self.bot.get_guild(config.SERVERS["MAIN_ID"])
        if not guild or not guild.me.guild_permissions.manage_guild or "BANNER" not in guild.features:
            return

        now = time.time()
        active_members = []
        for user_id, messages in list(self.message_cache.items()):
            recent = [(l, ts) for l, ts in messages if now - ts <= 300]
            self.message_cache[user_id] = recent
            if recent:
                member = guild.get_member(user_id)
                if member:
                    active_members.append(member)

        if not active_members:
            self.waiting_for_update.add(guild.id)
            return

        selected = self.get_most_active_user(guild)
        if not selected:
            self.waiting_for_update.add(guild.id)
            return

        self.waiting_for_update.discard(guild.id)
        voice_count = self.get_voice_users_count(guild)
        banner_buffer = await self.create_banner(selected, voice_count)
        try:
            await guild.edit(banner=banner_buffer.getvalue())
        except discord.HTTPException:
            pass

    @update_banner.before_loop
    async def before_update_banner(self) -> None:
        await self.bot.wait_until_ready()

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Banner(bot))

