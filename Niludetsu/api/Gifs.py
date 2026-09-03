from typing import Optional

import aiohttp

class GifsAPI:

    BASE_URL = "https://api.otakugifs.xyz/gif"

    def __init__(self, session: Optional[aiohttp.ClientSession] = None):
        self.session = session

    def bind_session(self, session: Optional[aiohttp.ClientSession]) -> None:
        self.session = session

    async def get_random_gif(self, action: str, format: str = "GIF") -> str:
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

