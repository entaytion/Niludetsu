import aiohttp, asyncio, discord, io, json, random, typing, urllib.parse
from discord.ext import commands
from selectolax.parser import HTMLParser


class BooruFetcher:
    """Универсальный фетчер для booru-сайтов."""

    def __init__(self, session: aiohttp.ClientSession | None = None):
        self.headers = {
            "User-Agent": "Niludetsu/1.0 (by Entaytion on Discord)"
        }
        # Лимит размера файла для скачивания (25 МБ — лимит Discord)
        self.max_file_size = 24 * 1024 * 1024
        self.session = session

    def bind_session(self, session: aiohttp.ClientSession | None) -> None:
        self.session = session

    async def _request_text(self, url: str, *, timeout: int = 15) -> str | None:
        """Shared safe GET helper for booru endpoints."""
        if self.session is None or self.session.closed:
            return None

        try:
            async with self.session.get(
                url,
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as resp:
                if resp.status != 200:
                    return None
                text = await resp.text()
                if not text or text.strip() in ("", "[]", "{}"):
                    return None
                return text
        except Exception:
            return None

    async def _get_json(self, url: str) -> list | dict | None:
        """GET-запрос, вернуть JSON или None."""
        text = await self._request_text(url)
        if text is None:
            return None
        try:
            return json.loads(text)
        except Exception:
            return None

    async def _get_html(self, url: str) -> str | None:
        """GET-запрос, вернуть HTML или None."""
        return await self._request_text(url)

    async def download_file(self, url: str) -> tuple[io.BytesIO, str] | None:
        """
        Скачать файл в память (BytesIO).
        Возвращает (BytesIO, filename) или None если файл слишком большой / ошибка.
        """
        if self.session is None or self.session.closed:
            return None

        try:
            async with self.session.get(
                url,
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status != 200:
                    return None

                # Проверяем размер если сервер его отдает
                content_length = resp.headers.get("Content-Length")
                if content_length and int(content_length) > self.max_file_size:
                    return None

                # Читаем файл чанками чтобы не взорвать память
                data = io.BytesIO()
                total = 0
                async for chunk in resp.content.iter_chunked(1024 * 64):
                    total += len(chunk)
                    if total > self.max_file_size:
                        return None
                    data.write(chunk)

                data.seek(0)

                # Определяем имя файла из URL
                path = urllib.parse.urlparse(url).path
                filename = path.split("/")[-1] or "file.jpg"
                # Убираем query-параметры из имени
                if "?" in filename:
                    filename = filename.split("?")[0]

                return data, filename
        except Exception:
            return None

    # ================================================================
    #  Xbooru — JSON DAPI (аниме/хентай контент)
    #  Возвращает: (file_url, post_url, tags)
    # ================================================================

    async def fetch_xbooru(self, tags: str = None) -> tuple[str, str, str] | None:
        safe_tags = urllib.parse.quote(tags, safe="") if tags else ""

        # Рандомная страница, потом fallback на pid=0
        pid = random.randint(0, 5)
        url = (
            f"https://xbooru.com/index.php?page=dapi&s=post&q=index"
            f"&json=1&limit=100&pid={pid}&tags={safe_tags}"
        )
        data = await self._get_json(url)

        if not data or not isinstance(data, list) or len(data) == 0:
            url = (
                f"https://xbooru.com/index.php?page=dapi&s=post&q=index"
                f"&json=1&limit=100&pid=0&tags={safe_tags}"
            )
            data = await self._get_json(url)

        if not data or not isinstance(data, list) or len(data) == 0:
            return None

        post = random.choice(data)
        file_url = post.get("file_url") or post.get("sample_url")
        post_id = post.get("id")

        if not file_url:
            return None

        post_url = f"https://xbooru.com/index.php?page=post&s=view&id={post_id}" if post_id else ""
        return file_url, post_url, tags or "random"

    # ================================================================
    #  Realbooru — HTML-скрапинг (реальный контент)
    #  Возвращает: (file_url, post_url, tags)
    # ================================================================

    async def fetch_realbooru(self, tags: str = None) -> tuple[str, str, str] | None:
        safe_tags = urllib.parse.quote(tags, safe="") if tags else ""

        # Пробуем несколько страниц
        pids_to_try = [0, 42, 84]
        random.shuffle(pids_to_try)

        post_id = None
        for pid in pids_to_try:
            list_url = (
                f"https://realbooru.com/index.php?page=post&s=list"
                f"&tags={safe_tags}&pid={pid}"
            )
            html = await self._get_html(list_url)
            if not html:
                continue

            tree = HTMLParser(html)
            thumbs = tree.css("span.thumb a[href*='s=view']")
            if not thumbs:
                thumbs = tree.css("a[href*='page=post'][href*='s=view'][href*='id=']")
            if not thumbs:
                continue

            thumb = random.choice(thumbs)
            href = thumb.attributes.get("href", "")
            if "id=" in href:
                post_id = href.split("id=")[-1].split("&")[0]
                break

        if not post_id:
            return None

        # Загружаем страницу поста
        post_url = f"https://realbooru.com/index.php?page=post&s=view&id={post_id}"
        post_html = await self._get_html(post_url)
        if not post_html:
            return None

        tree = HTMLParser(post_html)
        file_url = None

        if (img := tree.css_first("img#image")):
            file_url = img.attributes.get("src")
        elif (vid := tree.css_first("video source")):
            file_url = vid.attributes.get("src")
        elif (vid := tree.css_first("source")):
            file_url = vid.attributes.get("src")

        if not file_url:
            return None

        if file_url.startswith("//"):
            file_url = "https:" + file_url
        elif file_url.startswith("/"):
            file_url = "https://realbooru.com" + file_url

        return file_url, post_url, tags or "random"


class NSFW(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.fetcher = BooruFetcher(getattr(bot, "http_session", None))

    async def cog_load(self):
        self.fetcher.bind_session(getattr(self.bot, "http_session", None))

    async def _send_posts(self, ctx, source_name: str, fetch_func, count: int, tags: str):
        """Общая логика: фетчим посты, скачиваем файлы, отправляем как аттачменты."""
        if not ctx.channel.is_nsfw():
            await ctx.send("🚫 Только в NSFW-канале!")
            return

        # Отправляем "typing" пока скачиваем
        async with ctx.typing():
            # Параллельный фетч URL-ов
            tasks = [fetch_func(tags) for _ in range(count)]
            results = await asyncio.gather(*tasks)

            # Фильтруем + дедупликация по file_url
            seen = set()
            posts = []
            for res in results:
                if res and res[0] and res[0] not in seen:
                    seen.add(res[0])
                    posts.append(res)

            # Retry если пусто
            if not posts:
                retry = await fetch_func(tags)
                if retry and retry[0]:
                    posts = [retry]

        if not posts:
            tag_display = f"`{tags}`" if tags else "случайного тега"
            await ctx.send(
                f"🚫 Не удалось найти посты для {tag_display} на **{source_name}**.\n"
                f"-# Попробуй другой тег."
            )
            return

        # Отправляем по одному файлу
        last_msg = ctx.message
        for i, (file_url, post_url, tags_out) in enumerate(posts, 1):
            async with ctx.typing():
                # Скачиваем файл в память
                downloaded = await self.fetcher.download_file(file_url)

            if downloaded:
                data, filename = downloaded
                # Формируем текст сообщения
                content = f"**[{i}/{len(posts)}]** с {source_name}\n"
                if post_url:
                    content += f"-# Оригинал: [ссылка](<{post_url}>)"

                try:
                    last_msg = await ctx.channel.send(
                        content=content,
                        file=discord.File(data, filename=filename),
                        reference=last_msg,
                        mention_author=False
                    )
                except discord.HTTPException:
                    # Если не удалось отправить файл — отправляем просто URL
                    fallback = f"**[{i}/{len(posts)}]** с {source_name}: <{file_url}>\n"
                    if post_url:
                        fallback += f"-# Оригинал: [ссылка](<{post_url}>)"
                    last_msg = await ctx.send(fallback)
            else:
                # Файл слишком большой или ошибка скачивания — шлём URL
                content = f"**[{i}/{len(posts)}]** с {source_name}: <{file_url}>\n"
                if post_url:
                    content += f"-# Оригинал: [ссылка](<{post_url}>)"
                content += "\n-# ⚠️ Файл слишком большой для загрузки"

                try:
                    last_msg = await ctx.channel.send(
                        content=content,
                        reference=last_msg,
                        mention_author=False
                    )
                except discord.HTTPException:
                    last_msg = await ctx.send(content)

        # Реакция-подсказка на последнем сообщении (3 минуты)
        try:
            await last_msg.add_reaction("❓")
        except discord.HTTPException:
            return

        def check(reaction, user):
            return (
                user != self.bot.user
                and reaction.message.id == last_msg.id
                and str(reaction.emoji) == "❓"
            )

        try:
            await self.bot.wait_for("reaction_add", timeout=180.0, check=check)
        except asyncio.TimeoutError:
            # Время вышло — убираем реакцию
            try:
                await last_msg.remove_reaction("❓", self.bot.user)
            except discord.HTTPException:
                pass
            return

        # Кто-то нажал — убираем реакцию полностью и показываем подсказку на 30 секунд
        try:
            await last_msg.clear_reaction("❓")
        except discord.HTTPException:
            pass

        help_embed = discord.Embed(
            description=(
                "`📖 Как искать:`\n"
                "`!nsfw` — аниме/хентай (3 поста)\n"
                "`!rnsfw` — реальное (3 поста)\n"
                "`!nsfw 5 furry` — 5 постов с тегом furry\n"
                "`!rnsfw 4 lesbian` — 4 реальных поста с тегом lesbian\n"
                "`!nsfw big_breasts blonde_hair` — несколько тегов через пробел\n"
                "Иногда бот может тупить (отправлять не по тегам), тут уж сорри, парсим вручную..."
            ),
            color=0x2b2d31
        )
        try:
            help_msg = await ctx.channel.send(embed=help_embed, reference=last_msg, mention_author=False)
        except discord.HTTPException:
            return

        await asyncio.sleep(30)
        try:
            await help_msg.delete()
        except discord.HTTPException:
            pass

    # --- Команды ---

    @commands.command(name="nsfw", description="NSFW контент (аниме/хентай)")
    async def nsfw(self, ctx: commands.Context, count: typing.Optional[int] = 3, *, tags: str = None):
        await self._send_posts(ctx, "Xbooru", self.fetcher.fetch_xbooru, count, tags)

    @commands.command(name="rnsfw", aliases=["nsfwreal"], description="Реальный NSFW контент")
    async def rnsfw(self, ctx: commands.Context, count: typing.Optional[int] = 3, *, tags: str = None):
        await self._send_posts(ctx, "Realbooru", self.fetcher.fetch_realbooru, count, tags)


async def setup(bot):
    await bot.add_cog(NSFW(bot))
