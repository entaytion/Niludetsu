from typing import Union

from Niludetsu.tools.Emojis import Emojis
from Niludetsu.tools.Validator import Check
from Niludetsu import Exceptions


class ParseAmount(Check):
    """Парсит строковый параметр в int, кладёт результат в data["amount"]."""

    def __init__(self, param: str = "bet"):
        self.param = param

    async def run(self, ctx, data: dict) -> dict:
        raw: Union[str, int, None] = data.get(self.param)
        raw_str = str(raw).strip() if raw is not None else ""

        if not raw_str:
            raise Exceptions.ValidationError(f"Сумма не может быть пустой! Пример: 100 {Emojis.MONEY}")
        if any(s in raw_str for s in (".", ",")):
            raise Exceptions.ValidationError(f"Сумма должна быть целым числом! Пример: 100 {Emojis.MONEY}")
        if raw_str.startswith("-") or (len(raw_str) > 1 and raw_str.startswith("0")):
            raise Exceptions.ValidationError(f"Только положительные числа! Пример: 100 {Emojis.MONEY}")
        if not raw_str.isdigit():
            raise Exceptions.ValidationError("Сумма должна содержать только цифры")

        value = int(raw_str)
        if value < 1:
            raise Exceptions.BetTooLow(min_bet=1)

        data["amount"] = value
        return data


class EnsureBalance(Check):
    """Проверяет что wallet >= data["amount"]."""

    async def run(self, ctx, data: dict) -> dict:
        cog = data["cog"]
        user_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id)
        amount = data["amount"]

        balance = await cog.economy.get_wallet(user_id, guild_id)
        if balance < amount:
            raise Exceptions.NotEnoughMoney(amount=(amount - balance))
        return data


class DeductMoney(Check):
    """Снимает data["amount"] с кошелька автора."""

    def __init__(self, event: str = ""):
        self.event = event

    async def run(self, ctx, data: dict) -> dict:
        cog = data["cog"]
        user_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id)
        amount = data["amount"]

        removed, msg = await cog.economy.remove_money(
            user_id, guild_id, amount, event=self.event
        )
        if not removed:
            # Если есть активная игра — снимаем блокировку
            game_name = data.get("_game_name")
            if game_name:
                await cog.validator.release_game(game_name, user_id, guild_id)
            raise Exceptions.ValidationError(msg)
        return data


class CheckCooldown(Check):
    """Проверяет кулдаун команды."""

    DEFAULT_MESSAGES = {
        "daily": "Вы уже забирали ежедневную награду, поэтому подождите ещё",
        "work": "Вы уже работали недавно, поэтому подождите ещё",
        "rob": "Вы уже проворачивали дельце недавно, поэтому подождите ещё",
        "slut": "Вы уже использовали эту команду недавно, поэтому подождите ещё",
    }

    def __init__(self, command: str, message: str = ""):
        self.command = command
        self.message = message

    async def run(self, ctx, data: dict) -> dict:
        cog = data["cog"]
        user_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id)

        can_use, error_msg = await cog.economy.check_cooldown(
            user_id, guild_id, self.command
        )
        if not can_use:
            cooldown_message = self.message or self.DEFAULT_MESSAGES.get(
                self.command,
                "Эта команда пока недоступна, поэтому подождите ещё",
            )
            text = f"{cooldown_message} {error_msg}" if error_msg else cooldown_message
            raise Exceptions.ValidationError(text)
        return dict(data)


class UpdateCooldown(Check):
    """Ставит кулдаун (вызывается после основных проверок)."""

    def __init__(self, command: str):
        self.command = command

    async def run(self, ctx, data: dict) -> dict:
        cog = data["cog"]
        user_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id)

        await cog.economy.update_cooldown(user_id, guild_id, self.command)
        return data


class ClaimGame(Check):
    """Блокирует мультисессию. Кладёт имя игры в data["_game_name"]."""

    def __init__(self, name: str):
        self.name = name

    async def run(self, ctx, data: dict) -> dict:
        cog = data["cog"]
        user_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id)

        claimed, clash_embed = await cog.validator.claim_game(
            self.name, user_id, guild_id
        )
        if not claimed:
            raise Exceptions.ActiveGameExists(game_name=self.name)
        data["_game_name"] = self.name
        return data


class NotSelf(Check):
    """Проверяет что ctx.author != data["member"]."""

    def __init__(self, error_message: str = "Нельзя выбрать самого себя"):
        self.error_message = error_message

    async def run(self, ctx, data: dict) -> dict:
        member = data.get("member")
        if member and member.id == ctx.author.id:
            raise Exceptions.ValidationError(self.error_message)
        return data


class NotBot(Check):
    """Проверяет что data["member"] не бот."""

    def __init__(self, error_message: str = "Нельзя выбрать бота"):
        self.error_message = error_message

    async def run(self, ctx, data: dict) -> dict:
        member = data.get("member")
        if member and member.bot:
            raise Exceptions.ValidationError(self.error_message)
        return data
