import discord
from discord.ext import commands
from Niludetsu import Embed, Time, config
from Niludetsu.locale import _

class Starboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.star_emoji = config.STARBOARD_EMOJI
        self.min_stars = config.STARBOARD_MIN_STARS
        self.time_service = Time()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.guild_id != config.SERVERS["MAIN_ID"]:
            return

        if not config.STARBOARD_CHANNEL_ID:
            return

        if str(payload.emoji) != self.star_emoji:
            return

        channel = self.bot.get_channel(payload.channel_id)
        if not channel:
            return

        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.NotFound:
            return

        t = _(guild_id=payload.guild_id, bot=self.bot)

        star_reaction = discord.utils.get(message.reactions, emoji=self.star_emoji)
        if not star_reaction or star_reaction.count < self.min_stars:
            return

        starboard_channel = self.bot.get_channel(config.STARBOARD_CHANNEL_ID)
        if not starboard_channel:
            return

        content = message.content
        image_url = None
        thumbnail_url = None
        additional_attachments = []

        if message.embeds:
            embed_data = message.embeds[0]
            if embed_data.description:
                content = f"{content}\n{embed_data.description}" if content else embed_data.description
            if embed_data.image:
                image_url = embed_data.image.url
            elif embed_data.thumbnail:
                thumbnail_url = embed_data.thumbnail.url

        embed = Embed.default(description=content or t("utilities", "starboard_no_text"))

        created_dt = self.time_service.ensure_datetime(message.created_at)
        created_at = self.time_service.format_datetime(created_dt, fmt="DD.MM.YYYY HH:mm")

        embed.set_author(
            name=f"{message.author.display_name} • {created_at}",
            icon_url=message.author.display_avatar.url if message.author.avatar else None
        )

        if message.attachments:
            for i, attachment in enumerate(message.attachments):
                file_ext = attachment.filename.split('.')[-1].lower()

                if i == 0:
                    if file_ext in ['png', 'jpg', 'jpeg', 'webp']:
                        image_url = attachment.url
                    elif file_ext in ['gif', 'mp4', 'webm', 'mov']:
                        thumbnail_url = attachment.url
                else:
                    additional_attachments.append((t("utilities", "starboard_source_n", n=i+1), attachment.url))

        if image_url:
            embed.set_image(url=image_url)
        if thumbnail_url:
            embed.set_thumbnail(url=thumbnail_url)

        embed.add_field(
            name=t("utilities", "starboard_source"),
            value=f"[{t('utilities', 'starboard_jump')}]({message.jump_url})",
            inline=False
        )

        for name, url in additional_attachments:
            embed.add_field(
                name=name,
                value=f"[{t('utilities', 'starboard_open')}]({url})",
                inline=True
            )

        embed.set_footer(text=f"{star_reaction.count} ⭐")

        async for old_message in starboard_channel.history(limit=100):
            if old_message.embeds:
                for field in old_message.embeds[0].fields:
                    if field.name == t("utilities", "starboard_source") and message.jump_url in field.value:
                        new_embed = old_message.embeds[0].copy()
                        new_embed.set_footer(text=f"{star_reaction.count} ⭐")
                        await old_message.edit(embed=new_embed)
                        return

        await starboard_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if not config.STARBOARD_CHANNEL_ID:
            return

        if str(payload.emoji) != self.star_emoji:
            return

        channel = self.bot.get_channel(payload.channel_id)
        if not channel:
            return

        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.NotFound:
            return

        t = _(guild_id=payload.guild_id, bot=self.bot)

        star_reaction = discord.utils.get(message.reactions, emoji=self.star_emoji)
        star_count = star_reaction.count if star_reaction else 0

        starboard_channel = self.bot.get_channel(config.STARBOARD_CHANNEL_ID)
        if not starboard_channel:
            return

        async for old_message in starboard_channel.history(limit=100):
            if old_message.embeds:
                for field in old_message.embeds[0].fields:
                    if field.name == t("utilities", "starboard_source") and message.jump_url in field.value:
                        if star_count < self.min_stars:
                            await old_message.delete()
                        else:
                            new_embed = old_message.embeds[0].copy()
                            new_embed.set_footer(text=f"{star_count} ⭐")
                            await old_message.edit(embed=new_embed)
                        return

async def setup(bot):
    await bot.add_cog(Starboard(bot))
