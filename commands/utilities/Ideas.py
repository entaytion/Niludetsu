import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Modal, TextInput, View
from Niludetsu import Embed, Time, Emojis
from Niludetsu.config import IDEAS_CHANNEL_ID, ADMINISTRATOR_ID, SERVER_TEAM_ID
from typing import Optional

class ReasonModal(Modal):
    def __init__(self, title: str, callback):
        super().__init__(title=title)
        self.callback = callback

        self.reason_input = TextInput(
            label="Причина",
            placeholder="Укажите причину...",
            style=discord.TextStyle.paragraph,
            required=False,
            max_length=1000,
        )
        self.add_item(self.reason_input)

    async def on_submit(self, interaction: discord.Interaction):
        await self.callback(interaction, self.reason_input.value if self.reason_input.value else None)

class IdeaView(View):
    def __init__(self, user_id: int, thread_id: int = None):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.thread_id = thread_id

        self.add_item(self._create_rating_select())
        self.add_item(self._create_admin_select())

    def _create_rating_select(self):
        select = discord.ui.Select(
            placeholder="Оценить идею",
            custom_id="idea_rating_select",
            options=[
                discord.SelectOption(label="1", emoji="1️⃣", value="1", description="Ужасная идея"),
                discord.SelectOption(label="2", emoji="2️⃣", value="2", description="Плохая идея"),
                discord.SelectOption(label="3", emoji="3️⃣", value="3", description="Средняя идея"),
                discord.SelectOption(label="4", emoji="4️⃣", value="4", description="Хорошая идея"),
                discord.SelectOption(label="5", emoji="5️⃣", value="5", description="Отличная идея"),
            ]
        )
        select.callback = self._rating_callback
        return select

    def _create_admin_select(self):
        select = discord.ui.Select(
            placeholder="Для администрации",
            custom_id="idea_admin_select",
            options=[
                discord.SelectOption(label="Принять", emoji=Emojis.SUCCESS, value="accept", description="Принять идею"),
                discord.SelectOption(label="Отклонить", emoji=Emojis.ERROR, value="reject", description="Отклонить идею"),
            ]
        )
        select.callback = self._admin_callback
        return select

    async def _rating_callback(self, interaction: discord.Interaction):
        rating = int(interaction.data["values"][0])
        await self._handle_rating(interaction, rating)

    async def _admin_callback(self, interaction: discord.Interaction):
        if not await self._check_admin_permission(interaction):
            await interaction.response.send_message(
                "У вас недостаточно прав для принятия решений по идеям! Требуется роль администратора.",
                ephemeral=True
            )
            return

        action = interaction.data["values"][0]
        if action == "accept":
            modal = ReasonModal("Причина принятия", lambda i, r: self._handle_accept(i, r))
        else:
            modal = ReasonModal("Причина отклонения", lambda i, r: self._handle_reject(i, r))

        await interaction.response.send_modal(modal)

    async def _check_admin_permission(self, interaction: discord.Interaction) -> bool:
        return (interaction.user.guild_permissions.administrator or
                any(role.id == ADMINISTRATOR_ID for role in interaction.user.roles))

    async def _handle_rating(self, interaction: discord.Interaction, rating: int):
        message = interaction.message
        if not message.embeds:
            await interaction.response.send_message("Ошибка: сообщение с идеей не содержит эмбед!", ephemeral=True)
            return

        idea_embed = message.embeds[0]
        team_role_id = SERVER_TEAM_ID

        # Считываем уже выставленные оценки
        ratings = {}
        for field in idea_embed.fields:
            if field.name == "Оценки:":
                if field.value and field.value != "Нет оценок":
                    for entry in field.value.split('\n'):
                        if ':' in entry:
                            m = re.search(r'<@(\d+)>:\s*(\d+)', entry)
                            if m:
                                uid = int(m.group(1))
                                r = int(m.group(2))
                                ratings[uid] = r
                break

        ratings[interaction.user.id] = rating

        # Формируем список оценок с отметкой для команды
        ratings_text = []
        for uid, r in ratings.items():
            user = interaction.guild.get_member(uid)
            if user:
                prefix = "🛠️ " if any(role.id == team_role_id for role in user.roles) else ""
                ratings_text.append(f"{prefix}<@{uid}>: {r}")
        ratings_value = "\n".join(ratings_text) if ratings_text else "Нет оценок"

        # Средний рейтинг
        avg_rating = sum(ratings.values()) / len(ratings) if ratings else 0.0

        # Цвет от красного (1) к зеленому (5)
        r = max(0, min(255, int(255 * (5 - avg_rating) / 4)))
        g = max(0, min(255, int(255 * (avg_rating - 1) / 4)))
        color = (r << 16) + (g << 8)
        idea_embed.color = color

        # Обновляем поля
        found_ratings = False
        for i, field in enumerate(idea_embed.fields):
            if field.name == "Оценки:":
                idea_embed.set_field_at(i, name="Оценки:", value=ratings_value, inline=False)
                found_ratings = True
                break
        if not found_ratings:
            idea_embed.add_field(name="Оценки:", value=ratings_value, inline=False)

        found_avg = False
        for i, field in enumerate(idea_embed.fields):
            if field.name == "Средний рейтинг:":
                idea_embed.set_field_at(i, name="Средний рейтинг:", value=f"{avg_rating:.1f}/5.0", inline=True)
                found_avg = True
                break
        if not found_avg:
            idea_embed.add_field(name="Средний рейтинг:", value=f"{avg_rating:.1f}/5.0", inline=True)

        await message.edit(embed=idea_embed)
        await interaction.response.send_message(f"Вы оценили идею на {rating}/5!", ephemeral=True)

    async def _update_idea_status(self, interaction: discord.Interaction, status: str, color: int, reason: str = None):
        user = interaction.client.get_user(self.user_id)
        status_emoji = Emojis.SUCCESS if status == "принята" else Emojis.ERROR

        idea_text = interaction.message.embeds[0].description if interaction.message.embeds else ""
        if user:
            dm_embed = Embed(
                title=f"{status_emoji} Ваша идея была рассмотрена",
                color=color
            )
            dm_embed.set_author(
                name=f"Решение принял: {interaction.user.display_name}",
                icon_url=interaction.user.avatar.url if interaction.user.avatar else None
            )
            dm_embed.add_field(name="Ваша идея", value=f'>>> {idea_text}', inline=False)
            dm_embed.add_field(
                name="Ответ",
                value=f'Идея была **{status}**.' + (f'\n**Причина:** {reason}' if reason else ''),
                inline=False
            )
            try:
                await user.send(embed=dm_embed)
            except discord.Forbidden:
                pass

        embed = interaction.message.embeds[0] if interaction.message.embeds else Embed()
        embed.color = color

        author = embed.author if hasattr(embed, "author") else None

        new_embed = Embed(
            title=f"{status_emoji} Идея {status}",
            description=embed.description,
            color=color
        )
        if author:
            new_embed.set_author(name=getattr(author, "name", None), icon_url=getattr(author, "icon_url", None))

        for field in embed.fields:
            if field.name not in ["Причина"]:
                new_embed.add_field(name=field.name, value=field.value, inline=field.inline)

        if reason:
            new_embed.add_field(name=f"Причина от {interaction.user.display_name}", value=reason, inline=False)

        if embed.image:
            new_embed.set_image(url=embed.image.url)

        for item in self.children:
            item.disabled = True

        await interaction.message.edit(embed=new_embed, view=self)

        response_message = f"{status_emoji} Идея была {status}"
        if reason:
            response_message += f"\n**Причина:** {reason}"
        await interaction.response.send_message(response_message, ephemeral=True)

    async def _close_thread(self, interaction: discord.Interaction, status_emoji: str, status: str, color: int, reason: Optional[str]):
        if not self.thread_id:
            return
        try:
            thread = interaction.client.get_channel(self.thread_id) or await interaction.client.fetch_channel(self.thread_id)
            if thread:
                close_embed = Embed(
                    title=f"{status_emoji} Обсуждение закрыто",
                    description=f"Идея была **{status}**!" + (f"\n**Причина:** {reason}" if reason else ""),
                    color=color
                )
                close_embed.set_author(
                    name=f"Решение принял: {interaction.user.display_name}",
                    icon_url=interaction.user.avatar.url if interaction.user.avatar else None
                )
                await thread.send(embed=close_embed)
                await asyncio.sleep(1)
                await thread.delete()
        except (discord.NotFound, discord.Forbidden):
            pass

    async def _handle_accept(self, interaction: discord.Interaction, reason: str = None):
        await self._update_idea_status(interaction, "принята", 0x2ecc71, reason)
        await self._close_thread(interaction, "✅", "принята", 0x2ecc71, reason)

    async def _handle_reject(self, interaction: discord.Interaction, reason: str = None):
        await self._update_idea_status(interaction, "отклонена", 0xe74c3c, reason)
        await self._close_thread(interaction, "❌", "отклонена", 0xe74c3c, reason)

class Ideas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.time_service = Time()
        self.team_role_id = SERVER_TEAM_ID

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(IdeaView(0))

    async def process_idea(self, ctx_or_interaction, text: str, attachment: Optional[discord.Attachment] = None):
        is_interaction = isinstance(ctx_or_interaction, discord.Interaction)

        if is_interaction:
            user = ctx_or_interaction.user
            guild = ctx_or_interaction.guild
        else:
            user = ctx_or_interaction.author
            guild = ctx_or_interaction.guild

        # Канал идей из конфига
        channel = guild.get_channel(IDEAS_CHANNEL_ID) if guild else None
        if not channel:
            channel = ctx_or_interaction.channel

        # Проверка кулдауна (не для администраторов)
        is_admin = (user.guild_permissions.administrator or 
                    any(role.id == ADMINISTRATOR_ID for role in user.roles))

        if not is_admin:
            cooldown_key = f"idea:{user.id}"
            can_use, remaining = self.time_service.check_cooldown(cooldown_key, 300)  # 5 минут

            if not can_use:
                time_str = self.time_service.format_duration(remaining)
                error_msg = f"⏰ Подождите {time_str} перед следующим предложением идеи!"

                if is_interaction:
                    await ctx_or_interaction.response.send_message(error_msg, ephemeral=True)
                else:
                    msg = await ctx_or_interaction.send(error_msg)
                    try:
                        await asyncio.sleep(5)
                        await msg.delete()
                        await ctx_or_interaction.message.delete()
                    except (discord.NotFound, discord.Forbidden):
                        pass
                return

        # Проверка прав бота
        try:
            permissions = channel.permissions_for(guild.me)
            if not permissions.send_messages or not permissions.embed_links:
                error_message = "У бота нет прав на отправку сообщений или вставку эмбедов в канал идей!"
                if is_interaction:
                    await ctx_or_interaction.response.send_message(error_message, ephemeral=True)
                else:
                    await ctx_or_interaction.send(error_message)
                return
        except AttributeError:
            error_message = "Не удалось найти настроенный канал для идей!"
            if is_interaction:
                await ctx_or_interaction.response.send_message(error_message, ephemeral=True)
            else:
                await ctx_or_interaction.send(error_message)
            return

        # Формируем эмбед
        embed = Embed.default(title="💡 Новая идея", description=text)
        embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
        embed.add_field(name="Дата", value=f"<t:{int(discord.utils.utcnow().timestamp())}:F>", inline=True)
        embed.add_field(name="Оценки:", value="Нет оценок", inline=False)
        embed.add_field(name="Средний рейтинг:", value="0.0/5.0", inline=True)

        if attachment:
            if attachment.content_type and attachment.content_type.startswith('image/'):
                embed.set_image(url=attachment.url)
            else:
                embed.add_field(name="Вложение", value=f"[Скачать]({attachment.url})", inline=False)

        embed.set_footer(text="Используйте !идея, !idea, !suggest или /suggest для предложения новой идеи")

        # Отправляем в канал
        idea_message = await channel.send(
            content=f"<@&{ADMINISTRATOR_ID}>",
            embed=embed,
            view=IdeaView(user.id)
        )

        # Создаём ветку
        thread = await idea_message.create_thread(
            name=f"Обсуждение идеи от {user.display_name}",
            auto_archive_duration=10080,
            reason=f"Обсуждение идеи от {user.display_name}"
        )
        await thread.send(embed=Embed.default(
            title="Обсуждение идеи",
            description=f"Здесь вы можете обсудить идею от {user.mention}.\nПожалуйста, соблюдайте правила сервера при обсуждении.",
        ))

        # Обновляем view с ID ветки
        await idea_message.edit(view=IdeaView(user.id, thread.id))

        success_message = "Ваша идея успешно отправлена!"
        if is_interaction:
            await ctx_or_interaction.response.send_message(success_message, ephemeral=True)
        else:
            try:
                confirm_msg = await ctx_or_interaction.send(success_message)
                await asyncio.sleep(5)
                await confirm_msg.delete()
                await ctx_or_interaction.message.delete()
            except (discord.NotFound, discord.Forbidden):
                pass

    @commands.hybrid_command(name="idea", aliases=["идея", "suggest"])
    @app_commands.describe(text="Текст вашей идеи", photo="Изображение для иллюстрации идеи (необязательно)")
    async def idea_command(self, ctx, *, text: str = None, photo: Optional[discord.Attachment] = None):
        """ if not text and not ctx.message.attachments:
            await ctx.send("Пожалуйста, укажите текст идеи!")
            return

        if not text and ctx.message.attachments:
            photo = ctx.message.attachments[0]
            text = ctx.message.content
            for prefix in await self.bot.get_prefix(ctx.message):
                for cmd in ["idea", "идея", "suggest"]:
                    cmd_text = f"{prefix}{cmd}"
                    if text.startswith(cmd_text):
                        text = text[len(cmd_text):].strip()
                        break
            if not text:
                text = "Идея без описания"

        await self.process_idea(ctx, text, photo) """

async def setup(bot):
    await bot.add_cog(Ideas(bot))

