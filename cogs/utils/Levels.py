import asyncio
import random
import re
from discord.ext import commands, tasks
from Niludetsu.utils.database import get_user, save_user, calculate_next_level_xp
from Niludetsu.utils.embed import create_embed
from Niludetsu.core.base import EMOJIS

class LevelSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.check_voice_channels_loop())

    CATEGORY_ID = 1128436199204343828

    async def check_voice_channels_loop(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            await self.check_voice_channels()
            await asyncio.sleep(120) 

    async def check_voice_channels(self):
        for guild in self.bot.guilds:
            text_channel_id = 1125546970522583070 
            text_channel = guild.get_channel(text_channel_id)
            if not text_channel:
                continue

            for voice_channel in guild.voice_channels:
                if voice_channel.category and voice_channel.category.id == self.CATEGORY_ID:
                    for member in voice_channel.members:
                        if member.bot:
                            continue
                        user_id = str(member.id)
                        user = get_user(self.bot, user_id)
                        if not user:  # Проверка на None
                            continue
                        xp = user['xp']
                        level = user['level']
                        xp += 3

                        next_level_xp = calculate_next_level_xp(level)
                        if xp >= next_level_xp:
                            xp -= next_level_xp
                            level += 1
                            await self.level_up_notification(member, level, guild)

                        user['xp'] = xp
                        user['level'] = level
                        save_user(user_id, user)

    async def level_up_notification(self, member, level, guild):
        notification_channel_id = 1125546970522583070 
        notification_channel = guild.get_channel(notification_channel_id)
        if not notification_channel:
            return

        embed = create_embed(
            title="Новый уровень!",
            description=f"Поздравляю, {member.mention}!\nТеперь у вас {level} уровень!",
        )
        await notification_channel.send(embed=embed)

    async def give_role_by_level(self, member, level):
        roles = {
            5: {"remove": "1125344221986041902", "add": "1125344221986041903"},
            10: {"remove": ["1125344221986041902", "1125344221986041903"], "add": "1125344221986041904"},
            20: {"remove": ["1125344221986041902", "1125344221986041903", "1125344221986041904"], "add": "1125344221986041905"},
            30: {"remove": ["1125344221986041902", "1125344221986041903", "1125344221986041904", "1125344221986041905"], "add": "1125344222007005184"},
            50: {"remove": ["1125344221986041902", "1125344221986041903", "1125344221986041904", "1125344221986041905", "1125344222007005184"], "add": "1125344222007005186"},
        }
        if level in roles:
            role_remove = roles[level]["remove"]
            role_add = roles[level]["add"]
            if isinstance(role_remove, list):
                for role in role_remove:
                    role = member.guild.get_role(int(role))
                    if role:
                        await member.remove_roles(role)
            else:
                role = member.guild.get_role(int(role_remove))
                if role:
                    await member.remove_roles(role)
            role = member.guild.get_role(int(role_add))
            if role:
                await member.add_roles(role)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if message.stickers:
            return  
        
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # емодзі емоцій
            u"\U0001F300-\U0001F5FF"  # символи та піктограми
            u"\U0001F680-\U0001F6FF"  # транспорт та символи
            u"\U0001F1E0-\U0001F1FF"  # прапори країн
            u"\U00002702-\U000027B0"  # додаткові символи
            u"\U000024C2-\U0001F251" 
            "]+", flags=re.UNICODE)
        
        message_without_emoji = emoji_pattern.sub(r'', message.content)
        if message.content and not message_without_emoji.strip():
            return 

        user_id = str(message.author.id)
        user = get_user(self.bot, user_id)
        if not user: 
            return
        xp = user['xp']
        level = user['level']

        if len(message.content) >= 7:
            xp += 1
            next_level_xp = calculate_next_level_xp(level)
            if xp >= next_level_xp:
                xp -= next_level_xp
                level += 1
                await self.level_up_notification(message.author, level, message.guild)

            user['xp'] = xp
            user['level'] = level
            save_user(user_id, user)

async def setup(bot):
    await bot.add_cog(LevelSystem(bot))
