import aiohttp, asyncio, discord, re
from discord.ext import commands
from Niludetsu import TimeService, Embed, SupabaseDatabase, Emojis

class EventCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.time = TimeService()
        self.db = SupabaseDatabase()

        # Данные игр с описаниями и изображениями
        self.games = {
            1: {
                "name": "Смехлыст",
                "emoji": "🎲", 
                "description": "Смехлыст — эпичное развлечение для большой тусовки! Придумай как можно более остроумный ответ на вопрос — пусть твоя фантазия унесёт других в новые дали абсурда.",
                "image": "https://entaytion.vercel.app/ae/events/1.jpg"
            },
            2: {
                "name": "Gartic Phone",
                "emoji": "🎨",
                "description": "Gartic Phone — игра на рисование и угадывание! Рисуй, угадывай и смейся над результатами. Чем хуже рисуешь, тем веселее получается!",
                "image": "https://entaytion.vercel.app/ae/events/2.jpg"
            },
            3: {
                "name": "Мафия", 
                "emoji": "🕵️",
                "description": "Мафия — классическая психологическая игра! Вычисли мафию днём и выживи ночью. Блеф, дедукция и актёрское мастерство — всё пригодится!",
                "image": "https://entaytion.vercel.app/ae/events/3.jpg"
            },
            4: {
                "name": "Смертельная вечеринка",
                "emoji": "💀",
                "description": "Смертельная вечеринка — детективная игра с убийством! Раскрой тайну убийства, найди улики и вычисли преступника среди гостей вечеринки.",
                "image": "https://entaytion.vercel.app/ae/events/4.jpg"
            },
            5: {
                "name": "Просмотр фильма",
                "emoji": "🎬",
                "description": "Совместный просмотр фильма! Выберем интересный фильм и посмотрим его вместе, обсуждая самые яркие моменты.",
                "image": "https://entaytion.vercel.app/ae/events/5.jpg"
            },
            6: {
                "name": "Among Us",
                "emoji": "🚀", 
                "description": "Among Us — игра про предательство и командную работу в космосе! Выполняйте задания, вычисляйте предателей и постарайтесь не быть выброшенным в открытый космос.",
                "image": "https://entaytion.vercel.app/ae/events/6.jpg"
            },
            7: {
                "name": "Goose Goose Duck",
                "emoji": "🦆",
                "description": "Goose Goose Duck — социальная игра про дедукцию и обман! Выполняйте задания, раскрывайте гусей-предателей и побеждайте командной работой и хитростью.",
                "image": "https://entaytion.vercel.app/ae/events/7.jpg"
            }
        }

        self.prize_types = {
            1: "Валюта",
            2: "Тайный бокс", 
            3: "Другое"
        }

        # ID каналов
        self.voice_channel_id = 1398694155684679740  # голосовой канал для событий
        self.event_announce_channel_id = 1398694100668252363  # канал объявлений

    @commands.command(name='event', aliases=['событие'])
    @commands.has_permissions(administrator=True)
    async def event_command(self, ctx):
        """Создать событие"""

        # Шаг 1: Выбор игры
        base_embed = Embed.default(
            title="🎮 Выбор игры для события",
            description="Выберите игру из списка ниже:"
        )

        class GameSelectView(discord.ui.View):
            def __init__(self, author: discord.User, games: dict):
                super().__init__(timeout=60)
                self.author = author
                self.selected_game_num = None

                options = [
                    discord.SelectOption(
                        label=g["name"], 
                        description=g["description"][:90] + ("…" if len(g["description"]) > 90 else ""), 
                        emoji=g["emoji"], 
                        value=str(num)
                    )
                    for num, g in games.items()
                ]

                self.select = discord.ui.Select(
                    placeholder="Выберите игру…", 
                    options=options, 
                    min_values=1, 
                    max_values=1
                )

                async def select_callback(interaction: discord.Interaction):
                    if interaction.user.id != self.author.id:
                        await interaction.response.send_message("Это меню не для вас.", ephemeral=True)
                        return
                    self.selected_game_num = int(self.select.values[0])
                    await interaction.response.defer()
                    self.stop()

                self.select.callback = select_callback
                self.add_item(self.select)

        view = GameSelectView(ctx.author, self.games)
        prompt_msg = await ctx.send(embed=base_embed, view=view)
        await view.wait()
        await prompt_msg.edit(view=None)

        if view.selected_game_num is None:
            await ctx.send("⏰ Время ожидания истекло. Попробуйте снова.")
            return

        selected_game = self.games[view.selected_game_num]

        # Шаг 2: Ввод времени
        time_embed = Embed.default(
            title="⏰ Время проведения",
            description="Введите время проведения события:",
            fields=[{
                "name": "Примеры форматов:",
                "value": "- `сегодня 20:00`, `завтра 19:30`, `15:00` (сегодня)",
                "inline": False
            }],
            footer={"text": f"Игра: {selected_game['name']}"}
        )
        await prompt_msg.edit(embed=time_embed)

        def check_message(message):
            return message.author == ctx.author and message.channel == ctx.channel

        try:
            time_msg = await self.bot.wait_for('message', timeout=120.0, check=check_message)
            event_time_dt = self.parse_time_input(time_msg.content)
            if not event_time_dt:
                await ctx.send(f"{Emojis.ERROR} Не удалось распознать время. Попробуйте снова.")
                return
        except asyncio.TimeoutError:
            await ctx.send("⏰ Время ожидания истекло. Попробуйте снова.")
            return

        # Шаг 3: Выбор приза
        prize_list = "\n".join(f"{num}️⃣ {prize_type}" for num, prize_type in self.prize_types.items())

        prize_embed = Embed.default(
            title="🎁 Выбор приза",
            description="Выберите тип приза для события:",
            fields=[{
                "name": "Типы призов:",
                "value": prize_list,
                "inline": False
            }],
            footer={"text": f"Игра: {selected_game['name']} • Время: {self.time.format_datetime(event_time_dt, 'DD.MM.YYYY HH:mm')}"},
            timestamp=event_time_dt
        )

        await prompt_msg.edit(embed=prize_embed)

        # Добавляем реакции для выбора приза
        prize_reactions = ['1️⃣', '2️⃣', '3️⃣']
        for reaction in prize_reactions:
            await prompt_msg.add_reaction(reaction)

        def check_prize_reaction(reaction, user):
            return (user == ctx.author and 
                   str(reaction.emoji) in prize_reactions and 
                   reaction.message.id == prompt_msg.id)

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check_prize_reaction)
            selected_prize_num = prize_reactions.index(str(reaction.emoji)) + 1
        except asyncio.TimeoutError:
            await ctx.send("⏰ Время ожидания истекло. Попробуйте снова.")
            return

        # Шаг 4: Детали приза
        prize_text = await self.get_prize_details(ctx, selected_prize_num, check_message)
        if prize_text is None:
            return

        # Финальное подтверждение
        final_preview = Embed.success(
            title="Подтверждение",
            description="Создаю событие с выбранными параметрами…",
            footer={"text": f"Игра: {selected_game['name']} • Время: {self.time.format_datetime(event_time_dt, 'DD.MM.YYYY HH:mm')} • Приз: {re.sub(r'[**]', '', prize_text)[:50]}"}
        )
        await prompt_msg.edit(embed=final_preview)

        # Создаем и отправляем финальный эмбед
        await self.create_event_embed(ctx, selected_game, event_time_dt, prize_text)

    async def get_prize_details(self, ctx, prize_num: int, check_message) -> str:
        """Получить детали приза от пользователя"""
        if prize_num == 1:  # Валюта
            await ctx.send("💰 Введите количество кривен для приза:")
            try:
                amount_msg = await self.bot.wait_for('message', timeout=60.0, check=check_message)
                amount = amount_msg.content.strip()
                if not amount.isdigit():
                    await ctx.send(f"{Emojis.ERROR} Введите корректное число.")
                    return None
                return f"**{amount}**<:aeMoney:1365684703880810516>"
            except asyncio.TimeoutError:
                await ctx.send("⏰ Время ожидания истекло.")
                return None

        elif prize_num == 2:  # Тайный бокс
            return "**1 тайный бокс в инвентарь.**"

        elif prize_num == 3:  # Другое
            await ctx.send("📝 Введите описание приза:")
            try:
                custom_msg = await self.bot.wait_for('message', timeout=120.0, check=check_message)
                return f"**{custom_msg.content}**"
            except asyncio.TimeoutError:
                await ctx.send("⏰ Время ожидания истекло.")
                return None

    @commands.command(name='eventbox')
    @commands.has_permissions(administrator=True)
    async def event_box(self, ctx, *, args: str = None):
        """Выдать тайные боксы участникам"""
        if not args:
            await ctx.send("Укажите участников и опционально количество боксов.\n"
                        "Примеры: `!eventbox @user1 @user2` или `!eventbox 3 @user1 @user2`")
            return

        parts = args.strip()
        count_per_user = 1

        # Проверяем первый токен на число
        first_token = parts.split()[0]
        if first_token.isdigit():
            count_per_user = max(1, min(100, int(first_token)))
            parts = parts[len(first_token):].strip()

        # Извлекаем участников
        raw_users = [p for p in re.split(r'[\s,]+', parts) if p]
        if not raw_users:
            await ctx.send("Не удалось найти участников.")
            return

        members = []
        for token in raw_users:
            # Поддержка упоминаний <@id>
            match = re.search(r'(\d{15,})', token)
            if match:
                user_id = int(match.group(1))
                member = ctx.guild.get_member(user_id)
                if member:
                    members.append(member)

        if not members:
            await ctx.send("Не найдено участников на сервере.")
            return

        # Выдаем боксы
        total_boxes = 0
        for member in members:
            # Добавляем каждый бокс как отдельную запись в инвентарь
            for i in range(count_per_user):
                now_iso = self.time.now().to_iso8601_string()
                await self.db.ensure_inventory_item(
                    user_id=str(member.id),
                    guild_id=str(ctx.guild.id),
                    item_key=f"eventbox_{now_iso}_{i}",  # Уникальный ключ с ISO временем
                    item_type="eventbox",
                    meta={
                        "source": "event_reward",
                        "awarded_by": str(ctx.author.id),
                        "awarded_at": now_iso,
                    },
                    price_paid=0,
                )

            # Отправляем уведомление в ЛС
            try:
                box_word = "бокс" if count_per_user == 1 else ("бокса" if 2 <= count_per_user <= 4 else "боксов")
                await member.send(
                    f'🎁 Награждение за участие в ивенте! '
                    f'Вам выдано {count_per_user} тайн. {box_word}. '
                    f'Откройте их командой `/inventory`.'
                )
            except:
                pass

            total_boxes += count_per_user

        # Форматируем сообщение о выдаче
        member_word = "участника" if len(members) == 1 else ("участников" if len(members) < 5 else "участников")
        box_word = "бокс" if count_per_user == 1 else ("бокса" if 2 <= count_per_user <= 4 else "боксов")

        success_embed = Embed.success(
            title="Боксы выданы",
            description=f"Выдано **{total_boxes}** тайных боксов (**{count_per_user}** {box_word} на человека) для **{len(members)}** {member_word}.",
            fields=[
                {
                    "name": "Получатели",
                    "value": ", ".join([m.mention for m in members[:10]]) + (f"\n*и ещё {len(members) - 10}...*" if len(members) > 10 else ""),
                    "inline": False
                }
            ]
        )

        await ctx.send(embed=success_embed)

    def parse_time_input(self, time_str: str):
        """Парсинг времени с поддержкой 'сегодня', 'завтра'"""
        time_str = time_str.lower().replace(',', ' ').strip()
        time_str = re.sub(r'\s+', ' ', time_str)

        now = self.time.now()
        time_match = re.search(r'(\d{1,2}:\d{2})', time_str)

        if not time_match:
            return None

        time_part = time_match.group(1)
        date_obj = now

        if 'завтра' in time_str:
            date_obj = self.time.add_duration(now, days=1)

        # Формируем строку для парсинга
        full_datetime_str = f"{date_obj.format('YYYY-MM-DD')} {time_part}:00"

        try:
            return self.time.parse(full_datetime_str)
        except Exception as e:
            print(f"Ошибка парсинга времени '{full_datetime_str}': {e}")
            return None

    async def create_event_embed(self, ctx, game, event_time_dt, prize_text, *, mention_role: bool = True, target_channel = None):
        """Создать и отправить финальный эмбед события"""
        guild = ctx.guild
        end_time = self.time.add_duration(event_time_dt, hours=2)

        # Загружаем изображение для обложки
        image_bytes = None
        if game.get('image'):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(game['image']) as resp:
                        if resp.status == 200:
                            image_bytes = await resp.read()
            except:
                pass

        # Получаем голосовой канал
        voice_channel = guild.get_channel(self.voice_channel_id)
        location_text = voice_channel.name if voice_channel else "⭐〢мероприятия"

        # Создаем Scheduled Event
        scheduled = None
        try:
            create_kwargs = {
                'name': game['name'],
                'start_time': event_time_dt,
                'end_time': end_time,
                'privacy_level': discord.PrivacyLevel.guild_only,
                'description': f"{game['emoji']} {game['description']}",
            }

            if voice_channel and voice_channel.type == discord.ChannelType.voice:
                create_kwargs['entity_type'] = discord.EntityType.voice
                create_kwargs['channel'] = voice_channel
            elif voice_channel and voice_channel.type == discord.ChannelType.stage_voice:
                create_kwargs['entity_type'] = discord.EntityType.stage_instance
                create_kwargs['channel'] = voice_channel
            else:
                create_kwargs['entity_type'] = discord.EntityType.external
                create_kwargs['location'] = location_text

            if image_bytes:
                create_kwargs['image'] = image_bytes

            scheduled = await guild.create_scheduled_event(**create_kwargs)

        except Exception as e:
            await ctx.send(f"⚠️ Не удалось создать Scheduled Event: {e}")

        # Формируем Discord timestamp
        discord_timestamp = int(event_time_dt.timestamp())

        # Формируем эмбед
        embed = Embed.default(
            title=f"🔔 {game['name']}!",
            fields=[
                {"name": "> Ведущий:", "value": ctx.author.mention, "inline": True},
                {"name": "> Время:", "value": f"<t:{discord_timestamp}:F>", "inline": True},
                {"name": "> Канал:", "value": (voice_channel.mention if voice_channel else f"<#{self.voice_channel_id}>"), "inline": True},
                {"name": "> Приз:", "value": prize_text, "inline": True}
            ]
        )

        # Контент с пингом роли
        event_url = scheduled.url if scheduled else None
        if mention_role:
            content = (
                f"-# > <@&1364498609340416040> ➜ {event_url}\n"
                f"-# Не нравятся пинги? Отключите их в канале <#1261069675098279996>"
            ) if event_url else (
                "-# > <@&1364498609340416040>\n"
                "-# Не нравятся пинги? Отключите их в канале <#1261069675098279996>"
            )
        else:
            content = f"-# Событие ➜ {event_url}" if event_url else None

        # Отправляем в канал событий
        event_channel = target_channel or self.bot.get_channel(self.event_announce_channel_id)
        if event_channel:
            await event_channel.send(content=content, embed=embed)
            await ctx.send(f"{Emoji.SUCCESS} Событие успешно создано и отправлено в {event_channel.mention}!")
        else:
            await ctx.send(f"{Emojis.ERROR} Не удалось найти канал для событий.")

async def setup(bot):
    await bot.add_cog(EventCog(bot))

