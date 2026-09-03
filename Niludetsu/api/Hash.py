from ..locale import _
from ..tools.Embed import Embed
"""
Модуль для генерации хешей из текста
Поддерживает MD5, SHA1, SHA256, SHA512
"""

import hashlib

from typing import Optional

class HashAPI:

    def __init__(self):
        self.supported_algorithms = {
            'md5': hashlib.md5,
            'sha1': hashlib.sha1,
            'sha256': hashlib.sha256,
            'sha512': hashlib.sha512
        }

    def _calculate_hash(self, text: str, algorithm: str) -> Optional[str]:
        try:
            hash_func = self.supported_algorithms.get(algorithm.lower())
            if not hash_func:
                return None

            return hash_func(text.encode('utf-8')).hexdigest()
        except Exception:
            return None

    def _create_hash_embed(self, text: str, hashes: dict, t) -> Embed:

        display_text = text if len(text) <= 50 else text[:47] + "..."

        embed = Embed(
            title=t("api_hash", "title"),
            description=f"{t('api_hash', 'source_text')}: `{display_text}`"
        )

        for algo, hash_value in hashes.items():
            embed.add_field(
                name=f"**{algo.upper()}**",
                value=f"```{hash_value}```",
                inline=False
            )

        embed.set_footer(text=t("api_hash", "footer"))

        return embed

    async def generate_hash(self, ctx, text: str, algorithm: Optional[str] = None):
        if not text:
            t = _(ctx=ctx)
            await ctx.reply(embed=Embed.error(description=t("api_hash", "specify_text")))
            return

        if algorithm:
            algorithm = algorithm.lower()
            if algorithm not in self.supported_algorithms:
                t = _(ctx=ctx)
                available = ", ".join(self.supported_algorithms.keys())
                await ctx.reply(embed=Embed.error(
                    description=t("api_hash", "unsupported_algorithm", available=available)
                ))
                return

            hash_value = self._calculate_hash(text, algorithm)
            if not hash_value:
                t = _(ctx=ctx)
                await ctx.reply(embed=Embed.error(description=t("api_hash", "calc_error")))
                return

            hashes = {algorithm: hash_value}
        else:
            hashes = {}
            for algo in ['md5', 'sha256']:
                hash_value = self._calculate_hash(text, algo)
                if hash_value:
                    hashes[algo] = hash_value

        t = _(ctx=ctx)
        embed = self._create_hash_embed(text, hashes, t)
        await ctx.reply(embed=embed)

hash_api = HashAPI()

