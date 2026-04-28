from ..tools.Embed import Embed
"""
Модуль для генерации хешей из текста
Поддерживает MD5, SHA1, SHA256, SHA512
"""

import hashlib

from typing import Optional

class HashAPI:
    """Класс для генерации хешей"""

    def __init__(self):
        self.supported_algorithms = {
            'md5': hashlib.md5,
            'sha1': hashlib.sha1,
            'sha256': hashlib.sha256,
            'sha512': hashlib.sha512
        }

    def _calculate_hash(self, text: str, algorithm: str) -> Optional[str]:
        """Вычисляет хеш текста используя указанный алгоритм"""
        try:
            hash_func = self.supported_algorithms.get(algorithm.lower())
            if not hash_func:
                return None

            return hash_func(text.encode('utf-8')).hexdigest()
        except Exception:
            return None

    def _create_hash_embed(self, text: str, hashes: dict) -> Embed:
        """Создает embed с результатами хеширования"""

        # Обрезаем длинный текст для отображения
        display_text = text if len(text) <= 50 else text[:47] + "..."

        embed = Embed(
            title="🔐 Хеширование текста",
            description=f"Исходный текст: `{display_text}`"
        )

        # Добавляем хеши
        for algo, hash_value in hashes.items():
            embed.add_field(
                name=f"**{algo.upper()}**",
                value=f"```{hash_value}```",
                inline=False
            )

        embed.set_footer(text="💡 Хеши необратимы и используются для проверки целостности данных")

        return embed

    async def generate_hash(self, ctx, text: str, algorithm: Optional[str] = None):
        """
        Генерирует хеш(и) для текста

        Parameters
        ----------
        ctx : Union[discord.Interaction, commands.Context]
            Контекст команды
        text : str
            Текст для хеширования
        algorithm : Optional[str]
            Конкретный алгоритм (md5/sha1/sha256/sha512) или None для всех
        """
        if not text:
            await ctx.reply(embed=Embed.error(description="Укажите текст для хеширования!"))
            return

        # Если указан конкретный алгоритм
        if algorithm:
            algorithm = algorithm.lower()
            if algorithm not in self.supported_algorithms:
                available = ", ".join(self.supported_algorithms.keys())
                await ctx.reply(embed=Embed.error(
                    description=f"Неподдерживаемый алгоритм!\nДоступные: `{available}`"
                ))
                return

            hash_value = self._calculate_hash(text, algorithm)
            if not hash_value:
                await ctx.reply(embed=Embed.error(description="Ошибка при вычислении хеша"))
                return

            hashes = {algorithm: hash_value}
        else:
            # Генерируем все хеши
            hashes = {}
            for algo in ['md5', 'sha256']:  # Показываем только основные
                hash_value = self._calculate_hash(text, algo)
                if hash_value:
                    hashes[algo] = hash_value

        embed = self._create_hash_embed(text, hashes)
        await ctx.reply(embed=embed)

# Глобальный экземпляр
hash_api = HashAPI()

