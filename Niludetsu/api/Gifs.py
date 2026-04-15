from typing import Optional

import aiohttp

class GifsAPI:
    """Класс для работы с гифками для различных действий через OtakuGIFs API"""

    BASE_URL = "https://api.otakugifs.xyz/gif"

    def __init__(self, session: Optional[aiohttp.ClientSession] = None):
        self.session = session

    def bind_session(self, session: Optional[aiohttp.ClientSession]) -> None:
        self.session = session

    async def get_random_gif(self, action: str, format: str = "GIF") -> str:
        """
        Получить случайную гифку для указанного действия через OtakuGIFs API

        Args:
            action (str): Тип действия ('kiss', 'hug', 'slap', 'pat', 'bite', 'cry')
            format (str): Формат гифки ('GIF', 'WebP', 'AVIF'). По умолчанию 'GIF'.

        Returns:
            str: URL случайной гифки
        """
        params = {
            'reaction': action,
            'format': format
        }
        if self.session is None or self.session.closed:
            raise RuntimeError("HTTP session is not available")

        async with self.session.get(
            self.BASE_URL,
            params=params,
            timeout=aiohttp.ClientTimeout(total=5),
        ) as response:
            if response.status != 200:
                raise ValueError(f"Ошибка при получении гифки: {response.status}")

            data = await response.json()
        return data.get('url', '')

