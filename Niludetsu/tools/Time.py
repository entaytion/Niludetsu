import pendulum, re
from datetime import timedelta
from typing import Optional, Union, Dict, Tuple, Any

KYIV_TIMEZONE = "Europe/Kiev"
DEFAULT_FORMAT = "DD-MM-YYYY HH:mm:ss"

DurationResult = Tuple[Optional[int], Optional[str], Optional[str]]
DateLike = Union[str, pendulum.DateTime, None]

class TimeService:
    _duration_aliases: Dict[str, int] = {
        "с": 1, "сек": 1, "секунд": 1, "секунда": 1, "секунды": 1,
        "s": 1, "sec": 1, "second": 1, "seconds": 1,
        "м": 60, "мин": 60, "минут": 60, "минута": 60, "минуты": 60,
        "m": 60, "min": 60, "minute": 60, "minutes": 60,
        "ч": 3600, "час": 3600, "часа": 3600, "часов": 3600,
        "h": 3600, "hour": 3600, "hours": 3600, "hr": 3600,
        "д": 86400, "день": 86400, "дня": 86400, "дней": 86400,
        "d": 86400, "day": 86400, "days": 86400,
        "н": 604800, "неделя": 604800, "недели": 604800, "недель": 604800,
        "w": 604800, "week": 604800, "weeks": 604800,
    }

    _duration_pattern = re.compile(r"(\d+)([a-zа-я]+)", re.IGNORECASE)

    def __init__(self, timezone: str = KYIV_TIMEZONE):
        self.timezone = timezone
        self._cooldowns: Dict[str, pendulum.DateTime] = {}

    def now(self) -> pendulum.DateTime:
        return pendulum.now(self.timezone)

    def ensure_datetime(self, value: DateLike) -> Optional[pendulum.DateTime]:
        if value is None:
            return None
        if isinstance(value, pendulum.DateTime):
            return value.in_timezone(self.timezone)
        value = str(value).strip()
        if not value:
            return None
        try:
            dt = pendulum.parse(value)
        except Exception:
            return None
        return dt.in_timezone(self.timezone)

    def parse(self, value: DateLike) -> Optional[pendulum.DateTime]:
        return self.ensure_datetime(value)

    def parse_duration(self, duration_str: str) -> Optional[timedelta]:
        """
        Парсит строку длительности в timedelta.

        Поддерживаемые форматы:
        - 30s, 5m, 2h, 7d, 1w

        Parameters
        ----------
        duration_str : str
            Строка длительности

        Returns
        -------
        Optional[timedelta]
            timedelta или None, если не удалось распарсить
        """
        if not duration_str:
            return None

        # Регулярка для парсинга (30s, 5m, 2h, 7d, 1w)
        pattern = r'^(\d+)([smhdwсмчдн]+)$'  
        match = re.match(pattern, duration_str.lower().strip())

        if not match:
            return None

        value = int(match.group(1))
        unit = match.group(2)

        unit_mapping = {
            's': 'seconds', 'sec': 'seconds',
            'm': 'minutes', 'min': 'minutes',
            'h': 'hours', 'hr': 'hours',
            'd': 'days',
            'w': 'weeks',
            # Русские
            'с': 'seconds', 'сек': 'seconds',
            'м': 'minutes', 'мин': 'minutes',
            'ч': 'hours',
            'д': 'days',
            'н': 'weeks',
        }

        unit_key = unit_mapping.get(unit)
        if not unit_key:
            return None

        return timedelta(**{unit_key: value})

    def from_timestamp(self, value: Union[int, float]) -> pendulum.DateTime:
        return pendulum.from_timestamp(float(value), tz=self.timezone)

    def format_datetime(
        self,
        dt: DateLike = None,
        fmt: str = DEFAULT_FORMAT,
    ) -> str:
        dt_obj = self.ensure_datetime(dt) or self.now()
        return dt_obj.format(fmt)

    def to_iso(self, dt: DateLike = None) -> str:
        return (self.ensure_datetime(dt) or self.now()).to_iso8601_string()

    def add_duration(
        self,
        base: DateLike = None,
        *,
        years: int = 0,
        months: int = 0,
        weeks: int = 0,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
    ) -> pendulum.DateTime:
        dt = self.ensure_datetime(base) or self.now()
        return dt.add(
            years=years,
            months=months,
            weeks=weeks,
            days=days,
            hours=hours,
            minutes=minutes,
            seconds=seconds,
        )

    def add_hours(self, base: DateLike = None, hours: int = 1) -> pendulum.DateTime:
        return self.add_duration(base, hours=hours)

    def add_minutes(self, base: DateLike = None, minutes: int = 1) -> pendulum.DateTime:
        return self.add_duration(base, minutes=minutes)

    def diff(
        self,
        end: Union[str, pendulum.DateTime],
        start: Optional[Union[str, pendulum.DateTime]] = None,
        *,
        absolute: bool = True,
    ) -> pendulum.Duration:
        start_dt = self.ensure_datetime(start) if start is not None else self.now()
        end_dt = self.ensure_datetime(end)
        if not end_dt:
            raise ValueError("Нельзя вычислить diff: конечное время не распознано")
        return start_dt.diff(end_dt, abs=absolute)

    def seconds_between(
        self,
        end: Union[str, pendulum.DateTime],
        start: Optional[Union[str, pendulum.DateTime]] = None,
        *,
        absolute: bool = True,
    ) -> int:
        return int(self.diff(end, start, absolute=absolute).total_seconds())

    def validate_duration(self, duration: Union[str, int], max_days: int = 30, min_seconds: int = 5) -> DurationResult:
        if isinstance(duration, int):
            seconds = duration
        else:
            cleaned = duration.strip().lower().replace(" ", "").replace(",", "").replace(".", "")
            if not cleaned:
                return None, None, "Время не указано"

            matches = self._duration_pattern.findall(cleaned)
            if not matches:
                return None, None, "Неверный формат времени"

            seconds = 0
            for number, alias in matches:
                alias = alias.lower()
                if alias not in self._duration_aliases:
                    return None, None, f"Неизвестная единица времени: {alias}"
                seconds += int(number) * self._duration_aliases[alias]

        if seconds <= 0:
            return None, None, "Время должно быть больше 0"
        if seconds < min_seconds:
            return None, None, f"Минимальное время — {min_seconds} секунд"
        max_seconds = max_days * 86400
        if seconds > max_seconds:
            return None, None, f"Максимальное время — {max_days} дней"

        return seconds, self.format_duration(seconds), None

    def format_duration(self, seconds: int) -> str:
        if seconds <= 0:
            return "0 секунд"

        units = [
            ("неделя", "недели", "недель", 604800),
            ("день", "дня", "дней", 86400),
            ("час", "часа", "часов", 3600),
            ("минута", "минуты", "минут", 60),
            ("секунда", "секунды", "секунд", 1),
        ]

        parts = []
        for singular, few, many, step in units:
            value, seconds = divmod(seconds, step)
            if not value:
                continue
            parts.append(self._pluralize(value, singular, few, many))
        return " ".join(parts) if parts else "0 секунд"

    def is_time_passed(self, target: DateLike) -> bool:
        dt = self.ensure_datetime(target)
        if not dt:
            return False
        return dt <= self.now()

    def format_remaining_time(self, target: DateLike) -> Tuple[int, str]:
        dt = self.ensure_datetime(target)
        if not dt:
            return 0, "0 секунд"
        now = self.now()
        if dt <= now:
            return 0, "0 секунд"

        diff = now.diff(dt, abs=False)
        seconds = int(diff.total_seconds())
        return seconds, self.format_duration(seconds)

    @staticmethod
    def _pluralize(value: int, singular: str, few: str, many: str) -> str:
        mod10, mod100 = value % 10, value % 100
        if mod10 == 1 and mod100 != 11:
            return f"{value} {singular}"
        if 2 <= mod10 <= 4 and not 12 <= mod100 <= 14:
            return f"{value} {few}"
        return f"{value} {many}"

    def check_cooldown(self, key: str, seconds: int) -> Tuple[bool, int]:
        now = self.now()
        until = self._cooldowns.get(key)
        if not until or until <= now:
            self._cooldowns[key] = now.add(seconds=seconds)
            return True, 0
        remaining = int((until - now).total_seconds())
        return False, max(remaining, 0)

    def clear_cooldown(self, key: str) -> None:
        self._cooldowns.pop(key, None)

