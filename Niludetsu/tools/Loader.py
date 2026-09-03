from .. import config

import discord
from dataclasses import dataclass, field
from discord.ext import commands

from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

EMOJI_SUCCESS = "✅"
EMOJI_FAIL = "❌"
EMOJI_SKIP = "⏭️"
EMOJI_INFO = "🔍"
EMOJI_SYNC = "🔄"
EMOJI_FOLDER = "📁"

_last_sync_hash: int = 0

EMOJI_SUCCESS = "✅"
EMOJI_FAIL = "❌"
EMOJI_SKIP = "⏭️"
EMOJI_INFO = "🔍"
EMOJI_SYNC = "🔄"
EMOJI_FOLDER = "📁"

@dataclass
class LoadOutcome:
    module: str
    display: str
    success: bool
    message: Optional[str] = None

@dataclass
class LoadSummary:
    categories: Dict[str, Dict[str, List[str]]] = field(
        default_factory=lambda: {}
    )
    total: int = 0
    loaded: int = 0
    failed: int = 0
    skipped: int = 0

    def add(self, outcome: LoadOutcome, status: str) -> None:
        self.total += 1
        category = outcome.display.split("/")[0] if "/" in outcome.display else outcome.display
        bucket = self.categories.setdefault(
            category, {"success": [], "failed": [], "skipped": []}
        )

        item_name = outcome.display.split("/")[-1]

        if status == "skip":
            bucket["skipped"].append(item_name)
            self.skipped += 1
            return

        if outcome.success:
            bucket["success"].append(item_name)
            self.loaded += 1
        else:
            self.failed += 1
            if outcome.message:
                bucket["failed"].append(f"{item_name} ({outcome.message})")
            else:
                bucket["failed"].append(item_name)

    def print_report(self) -> None:
        if self.total == 0:
            print(f"{EMOJI_SKIP} Расширения не найдены — отчёт пуст.")
            return

        print("=== Загруженные расширения ===")
        for category in sorted(self.categories):
            status = self.categories[category]
            if not any(status.values()):
                continue

            ok = len(status["success"])
            bad = len(status["failed"])
            skip = len(status["skipped"])
            summary = f"{EMOJI_SUCCESS} {ok}" if ok else ""
            if bad:
                summary += f" {EMOJI_FAIL} {bad}"
            if skip:
                summary += f" {EMOJI_SKIP} {skip}"
            summary = summary.strip()

            print(f"{EMOJI_FOLDER} {category.upper()} ({summary})")
            if status["success"]:
                print("  ✔ " + ", ".join(sorted(status["success"])))
            if status["failed"]:
                print("  ✖ " + ", ".join(sorted(status["failed"])))
            if status["skipped"]:
                print("  ~ " + ", ".join(sorted(status["skipped"])))

        print(f"{EMOJI_INFO} Итог: {self.loaded}/{self.total} загружено, {self.failed} не удалось, {self.skipped} пропущено.")

class Loader:

    def __init__(
        self,
        bot: commands.Bot,
        *,
        command_dirs: Optional[Sequence[str]] = None,
        recursive: bool = True,
        show_first_n: int = 0,
    ) -> None:
        self.bot = bot
        self.command_dirs = command_dirs or ("commands",)
        self.recursive = recursive
        self.project_root = Path(__file__).resolve().parents[2]
        self.summary = LoadSummary()
        self.show_first_n = show_first_n
        self._loaded_shown = 0
        self._loaded_modules: list[str] = []

        servers = getattr(config, "SERVERS", {})
        self.main_guild_id: int = servers.get("MAIN_ID", 0)
        allowed = servers.get("ALLOWED_ID", [])
        self.allowed_guilds: set[int] = set(int(g) for g in allowed)

    async def load_everything(self) -> None:
        await self.load_extensions()
        self.summary.print_report()
        await self.sync_interactions()

    async def load_extensions(self) -> None:
        modules = self._discover_modules()
        if not modules:
            print(f"{EMOJI_SKIP} Нет расширений для загрузки.")
            return

        print(f"{EMOJI_INFO} Найдено расширений: {len(modules)} — начинаем загрузку...")

        self._loaded_modules = []
        for module, display in modules:
            outcome, status = await self._load_single(module, display)
            if status != "skip":
                self._loaded_modules.append(module)
            self.summary.add(outcome, status)

        if self._loaded_shown and self._loaded_shown < self.summary.loaded:
            remaining = self.summary.loaded - self._loaded_shown
            print(f"{EMOJI_SUCCESS} ... и ещё {remaining} расширений загружено без вывода.")

    async def sync_interactions(self) -> None:
        current_hash = hash(tuple(sorted(self._loaded_modules))) if self._loaded_modules else 0
        global _last_sync_hash
        if current_hash and current_hash == _last_sync_hash:
            print(f"{EMOJI_SKIP} Набор расширений не изменился — синхронизация пропущена.")
            return
        _last_sync_hash = current_hash

        print(f"{EMOJI_SYNC} Синхронизация слеш-команд...")

        if not self.main_guild_id:
            print(f"{EMOJI_FAIL} MAIN_ID не указан в конфиге. Пропускаю синхронизацию.")
            return

        main_obj = discord.Object(id=self.main_guild_id)
        self.bot.tree.copy_global_to(guild=main_obj)
        main_commands = await self.bot.tree.sync(guild=main_obj)
        print(
            f"{EMOJI_SUCCESS} {len(main_commands)} команд синхронизировано с главным сервером {self.main_guild_id}."
        )

        cleaned = 0
        for guild in self.bot.guilds:
            if guild.id == self.main_guild_id:
                continue

            target = discord.Object(id=guild.id)
            self.bot.tree.clear_commands(guild=target)
            await self.bot.tree.sync(guild=target)
            cleaned += 1

            if guild.id in self.allowed_guilds:
                print(
                    f"{EMOJI_INFO} {guild.name} ({guild.id}): slash-команды очищены, остались только префиксные."
                )
            else:
                print(
                    f"{EMOJI_INFO} {guild.name} ({guild.id}): не в ALLOWED_ID, slash-команды тоже очищены."
                )

        if cleaned == 0:
            print(f"{EMOJI_SKIP} Бот пока ни на одном другом сервере не состоит — чистка не требуется.")
        else:
            print(f"{EMOJI_SUCCESS} Очистка завершена: обработано серверов — {cleaned}.")

    def _discover_modules(self) -> List[Tuple[str, str]]:
        modules: List[Tuple[str, str]] = []
        seen: set[str] = set()

        for base in self.command_dirs:
            base_path = (self.project_root / base).resolve()
            if not base_path.exists():
                print(f"{EMOJI_SKIP} Каталог «{base}» не найден — пропускаю.")
                continue

            iterator = base_path.rglob("*.py") if self.recursive else base_path.glob("*.py")
            for file_path in iterator:
                if file_path.name.startswith("_") or file_path.name == "__init__.py":
                    continue

                try:
                    rel_path = file_path.with_suffix("").relative_to(self.project_root)
                except ValueError:
                    continue

                module = ".".join(rel_path.parts)
                if module in seen:
                    continue

                seen.add(module)
                display = "/".join(rel_path.parts)
                modules.append((module, display))

        modules.sort(key=lambda item: item[0])
        return modules

    async def _load_single(self, module: str, display: str) -> Tuple[LoadOutcome, str]:
        try:
            await self.bot.load_extension(module)
            outcome = LoadOutcome(module, display, True)
            status = "success"

            if self.show_first_n <= 0:
                return outcome, status

            if self._loaded_shown < self.show_first_n:
                print(f"{EMOJI_SUCCESS} {display}")
                self._loaded_shown += 1

            return outcome, status

        except commands.errors.ExtensionAlreadyLoaded:
            outcome = LoadOutcome(module, display, True, "already loaded")
            if self.show_first_n <= 0 and self._loaded_shown < self.summary.loaded:
                print(f"{EMOJI_SKIP} {display}: уже загружено")
            return outcome, "skip"

        except commands.errors.NoEntryPointError:
            message = "отсутствует функция setup()"
            print(f"{EMOJI_FAIL} {display}: {message}")
            return LoadOutcome(module, display, False, message), "failure"

        except commands.errors.ExtensionFailed as exc:
            original = exc.original
            message = f"{type(original).__name__}: {original}" if original else str(exc)
            print(f"{EMOJI_FAIL} {display}: {message}")
            return LoadOutcome(module, display, False, message), "failure"

        except Exception as exc:
            message = f"{type(exc).__name__}: {exc}"
            print(f"{EMOJI_FAIL} {display}: {message}")
            return LoadOutcome(module, display, False, message), "failure"

