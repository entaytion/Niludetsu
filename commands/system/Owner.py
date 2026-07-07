import ast
import io
import os
import re

import discord
from discord.ext import commands
from datetime import datetime, timedelta, timezone
from Niludetsu import Embed, Colors
from Niludetsu.database import database

class Owner(commands.Cog):
    """Власницькі команди керування ботом та преміумом"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(name="givepremium", help="Надати серверу преміум статус (Тільки для власника)")
    @commands.is_owner()
    async def give_premium(self, ctx: commands.Context, guild_id: str, days: int):
        """ givepremium [guild_id] [days] """
        if days <= 0:
            # Lifetime premium
            expires_at = datetime(2999, 12, 31, tzinfo=timezone.utc)
            label = "вічний (до 2999 року)"
        else:
            expires_at = datetime.now(timezone.utc) + timedelta(days=days)
            label = f"на {days} днів (до {expires_at.strftime('%Y-%m-%d %H:%M')})"

        try:
            # Вставляємо в БД
            await database._neon.execute(
                """INSERT INTO public.premium_guilds (guild_id, expires_at, created_at) 
                   VALUES ($1, $2, now())
                   ON CONFLICT (guild_id) 
                   DO UPDATE SET expires_at = $2""",
                str(guild_id), expires_at
            )
            # Оновлюємо кеш бота
            await self.bot.config_manager.load_all()

            embed = Embed.success(
                title="✨ Преміум активовано",
                description=f"Серверу `{guild_id}` успішно активовано преміум-статус {label}."
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = Embed.error(
                title="❌ Помилка БД",
                description=f"Не вдалося активувати преміум: {e}"
            )
            await ctx.send(embed=embed)

    @commands.command(name="removepremium", help="Забрати у сервера преміум статус (Тільки для власника)")
    @commands.is_owner()
    async def remove_premium(self, ctx: commands.Context, guild_id: str):
        """ removepremium [guild_id] """
        try:
            await database._neon.execute(
                "DELETE FROM public.premium_guilds WHERE guild_id = $1",
                str(guild_id)
            )
            await self.bot.config_manager.load_all()

            embed = Embed.success(
                title="❌ Преміум деактивовано",
                description=f"З сервера `{guild_id}` знято преміум-статус."
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = Embed.error(
                title="❌ Помилка БД",
                description=f"Не вдалося зняти преміум: {e}"
            )
            await ctx.send(embed=embed)

    @commands.command(name="listpremium", help="Показати всі преміум сервери (Тільки для власника)")
    @commands.is_owner()
    async def list_premium(self, ctx: commands.Context):
        try:
            rows = await database._neon.fetch(
                "SELECT guild_id, expires_at FROM public.premium_guilds"
            )
            if not rows:
                embed = Embed.info(
                    title="💎 Преміум сервери",
                    description="Жоден сервер немає активного преміуму."
                )
                await ctx.send(embed=embed)
                return

            lines = []
            for row in rows:
                gid = row["guild_id"]
                exp = row["expires_at"]
                guild_name = "Невідомий сервер"
                guild = self.bot.get_guild(int(gid))
                if guild:
                    guild_name = guild.name
                
                exp_label = "Вічний" if exp.year >= 2990 else exp.strftime('%Y-%m-%d %H:%M')
                lines.append(f"• **{guild_name}** (`{gid}`) — діє до: `{exp_label}`")

            embed = Embed.info(
                title="💎 Преміум сервери",
                description="\n".join(lines)
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = Embed.error(
                title="❌ Помилка БД",
                description=f"Не вдалося отримати список: {e}"
            )
            await ctx.send(embed=embed)

    @commands.command(name="reloadconfig", help="Перезавантажити кеш налаштувань вручну (Тільки для власника)")
    @commands.is_owner()
    async def reload_config(self, ctx: commands.Context):
        try:
            await self.bot.config_manager.load_all()
            embed = Embed.success(
                title="🔄 Кеш синхронізовано",
                description="Усі кастомні повідомлення та преміум-сервери заново завантажені в кеш бота."
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = Embed.error(
                title="❌ Помилка",
                description=f"Не вдалося перезавантажити конфіг: {e}"
            )
            await ctx.send(embed=embed)

    @commands.command(name="scanlocale", help="Сканировать код на хардкоджені кириличні рядки (Тільки для власника)")
    @commands.is_owner()
    async def scan_locale(self, ctx: commands.Context):
        await ctx.defer()

        cyrillic = re.compile(r'[а-яА-ЯёЁ]')
        base_dirs = [
            os.path.join(os.path.dirname(__file__), ".."),
            os.path.join(os.path.dirname(__file__), "..", "..", "Niludetsu"),
        ]
        base_dirs = [os.path.normpath(d) for d in base_dirs]

        results: list[tuple[str, int, str]] = []

        for base in base_dirs:
            if not os.path.isdir(base):
                continue
            for root, _, files in os.walk(base):
                for fname in files:
                    if not fname.endswith(".py"):
                        continue
                    fpath = os.path.join(root, fname)
                    rel = os.path.relpath(fpath, os.path.join(os.path.dirname(__file__), "..", ".."))
                    try:
                        with open(fpath, "r", encoding="utf-8") as fh:
                            source = fh.read()
                    except Exception:
                        continue

                    docstring_lines: set[int] = set()
                    tree = None
                    try:
                        tree = ast.parse(source)
                        for node in ast.walk(tree):
                            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
                                body = getattr(node, "body", [])
                                if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
                                    docstring_lines.add(body[0].lineno)
                    except SyntaxError:
                        pass

                    if tree is not None:
                        for node in ast.walk(tree):
                            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                                if node.lineno in docstring_lines:
                                    continue
                                val = node.value
                                if len(val) < 2 or not val.strip():
                                    continue
                                if cyrillic.search(val):
                                    snippet = val.strip()[:120]
                                    results.append((rel, node.lineno, snippet))

        if not results:
            await ctx.send("✅ Хардкоджених кириличних рядків не знайдено!")
            return

        lines = []
        for fpath, lineno, snippet in sorted(results, key=lambda x: (x[0], x[1])):
            lines.append(f"{fpath}:{lineno}: {snippet}")

        content = f"Знайдено {len(results)} хардкоджених кириличних рядків:\n\n" + "\n".join(lines)
        buf = io.BytesIO(content.encode("utf-8"))
        file = discord.File(buf, filename="scanlocale_results.txt")
        await ctx.send(file=file)

async def setup(bot: commands.Bot):
    await bot.add_cog(Owner(bot))
