import requests

class GifsAPI:
    """Класс для работы с гифками для различных действий через OtakuGIFs API"""

    BASE_URL = "https://api.otakugifs.xyz/gif"

    def get_random_gif(self, action: str, format: str = "GIF") -> str:
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
        response = requests.get(self.BASE_URL, params=params)

        if response.status_code != 200:
            raise ValueError(f"Ошибка при получении гифки: {response.status_code}")

        data = response.json()
        return data.get('url', '')

