from typing import List
import random

class GifsAPI:
    """Класс для работы с гифками для различных действий"""
    
    def __init__(self):
        # Гифки для поцелуев
        self.kiss_gifs = [
            "https://media.tenor.com/F02Ep3b2jJgAAAAC/cute-kawaii.gif",
            "https://media.tenor.com/YHxJ9NvLYKsAAAAC/anime-kiss.gif", 
            "https://media.tenor.com/EP_-1UGmkJEAAAAC/anime-kiss.gif",
            "https://media.tenor.com/F5-GH4_yf2AAAAAC/anime-kiss.gif",
            "https://media.tenor.com/Ogthkl9rYBEAAAAC/ichigo-hiro.gif",
            "https://media.tenor.com/2tB89ikESPEAAAAC/kiss-anime.gif",
            "https://media.tenor.com/06lp3B45VB0AAAAC/kiss-anime.gif",
            "https://media.tenor.com/9jB6M6aoW0AAAAAC/val-ally-kiss.gif",
            "https://media.tenor.com/G954PGQ5Zl8AAAAC/cute-anime.gif",
            "https://media.tenor.com/Daj-Pn9LqCEAAAAC/anime-love.gif"
        ]
        
        # Гифки для объятий
        self.hug_gifs = [
            "https://media.tenor.com/kCZjTqCKiggAAAAC/hug.gif",
            "https://media.tenor.com/1T1B8HcWalQAAAAC/anime-hug.gif",
            "https://media.tenor.com/RWD2XL_CxdcAAAAC/hug-anime.gif",
            "https://media.tenor.com/wUQH5CF2DJ4AAAAC/horimiya-hug-anime.gif",
            "https://media.tenor.com/HYkaTQBybO4AAAAC/hug-anime.gif",
            "https://media.tenor.com/mmQyXP3JvKwAAAAC/anime-cute.gif",
            "https://media.tenor.com/XyMvYx1xcJAAAAAC/super-hug.gif",
            "https://media.tenor.com/J7eGDvGeP9IAAAAC/enage-kiss-anime-hug.gif",
            "https://media.tenor.com/cGFtCNuJE6AAAAAC/anime-hug.gif",
            "https://media.tenor.com/mB_y2KUsyuoAAAAC/cuddle-anime-hug.gif"
        ]
        
        # Гифки для ударов
        self.slap_gifs = [
            "https://media.tenor.com/PeJyQRCSHHkAAAAC/saki-saki-mukai-naoya.gif",
            "https://media.tenor.com/rVXByOZKidMAAAAC/anime-slap.gif",
            "https://media.tenor.com/Ws6Dm1ZW_vMAAAAC/girl-slap.gif",
            "https://media.tenor.com/CvBTA0GyrogAAAAC/anime-slap.gif",
            "https://media.tenor.com/klNTzZNDmEgAAAAC/slap-hit.gif",
            "https://media.tenor.com/eU5H6GbVjrcAAAAC/slap-jjk.gif",
            "https://media.tenor.com/E3OW-MYYum0AAAAC/no-angry.gif",
            "https://media.tenor.com/yJmrNruFNtEAAAAC/slap.gif",
            "https://media.tenor.com/XiYuU9h44-AAAAAC/anime-slap-mad.gif",
            "https://media.tenor.com/GBShVmDnx9kAAAAC/anime-slap.gif"
        ]
        
        # Гифки для поглаживаний
        self.pat_gifs = [
            "https://media.tenor.com/N41zKEDABuUAAAAC/anime-head-pat-anime-pat.gif",
            "https://media.tenor.com/wLqFGYigJuIAAAAC/mai-sakurajima.gif",
            "https://media.tenor.com/8DaE6qzF0DwAAAAC/neet-anime.gif",
            "https://media.tenor.com/YroVxwiL2dcAAAAC/ao-haru-ride-head-pat.gif",
            "https://media.tenor.com/6dLDH0npv6IAAAAC/nogamenolife-shiro.gif",
            "https://media.tenor.com/E6fMkQRZBdIAAAAC/kanna-kamui-pat.gif",
            "https://media.tenor.com/jEfC8czH_P0AAAAC/anime-pat.gif",
            "https://media.tenor.com/RDfGm9ftwx0AAAAC/anime-pat.gif",
            "https://media.tenor.com/rZBnbfYGYIkAAAAC/pat-head-good-girl.gif",
            "https://media.tenor.com/lnoDyTqMk24AAAAC/anime-pat.gif"
        ]
        
        # Гифки для укусов
        self.bite_gifs = [
            "https://media.tenor.com/w4T323o46uQAAAAC/anime-bite.gif",
            "https://media.tenor.com/6HhJw-4zmQUAAAAC/anime-bite.gif",
            "https://media.tenor.com/7eAyqtZlZ7wAAAAC/anime-bite.gif",
            "https://media.tenor.com/y8qPMnGg5IkAAAAC/anime-bite.gif",
            "https://media.tenor.com/MKjpPw-QbW0AAAAC/anime-vampire.gif",
            "https://media.tenor.com/CJb1ZYCFQp0AAAAC/anime-bite.gif",
            "https://media.tenor.com/4j3hMz-dUz0AAAAC/anime-bite.gif",
            "https://media.tenor.com/8UjO54apiYsAAAAC/anime-bite.gif",
            "https://media.tenor.com/TKmVH1OkwHAAAAAC/anime-bite.gif",
            "https://media.tenor.com/PvH1hWtxQHkAAAAC/bite-anime.gif"
        ]
        
        # Гифки для плача
        self.cry_gifs = [
            "https://media.tenor.com/fxPJctPqKvAAAAAC/anime-cry.gif",
            "https://media.tenor.com/dXTLCTsLtpEAAAAC/anime-cry.gif",
            "https://media.tenor.com/N2qZ0YPzpToAAAAC/anime-girl.gif",
            "https://media.tenor.com/6RpzedxMWwUAAAAC/anime-cry.gif",
            "https://media.tenor.com/Yxe2-3m8oWcAAAAC/anime-cry.gif",
            "https://media.tenor.com/35hmBwYHYikAAAAC/cry-sad.gif",
            "https://media.tenor.com/d_P1ag43RVcAAAAC/anime-cry.gif",
            "https://media.tenor.com/OjlNyUMUqpgAAAAC/anime-cry.gif",
            "https://media.tenor.com/pQzq4kgZgQgAAAAC/cry-sad.gif",
            "https://media.tenor.com/1Yb7AzHVjbEAAAAC/anime-cry.gif"
        ]
        
        # Гифки для секса
        self.sex_gifs = [
            "https://media.tenor.com/jWZ6_t8DqYoAAAAC/bonk-anime.gif",
            "https://media.tenor.com/jWZ6_t8DqYoAAAAC/bonk-anime.gif",
            "https://media.tenor.com/jWZ6_t8DqYoAAAAC/bonk-anime.gif",
            "https://media.tenor.com/jWZ6_t8DqYoAAAAC/bonk-anime.gif",
            "https://media.tenor.com/jWZ6_t8DqYoAAAAC/bonk-anime.gif",
            "https://media.tenor.com/jWZ6_t8DqYoAAAAC/bonk-anime.gif",
            "https://media.tenor.com/jWZ6_t8DqYoAAAAC/bonk-anime.gif",
            "https://media.tenor.com/jWZ6_t8DqYoAAAAC/bonk-anime.gif",
            "https://media.tenor.com/jWZ6_t8DqYoAAAAC/bonk-anime.gif",
            "https://media.tenor.com/jWZ6_t8DqYoAAAAC/bonk-anime.gif"
        ]

    def get_random_gif(self, action: str) -> str:
        """
        Получить случайную гифку для указанного действия
        
        Args:
            action (str): Тип действия ('kiss', 'hug', 'slap', 'pat', 'bite', 'cry', 'sex')
            
        Returns:
            str: URL случайной гифки
        """
        gifs_map = {
            'kiss': self.kiss_gifs,
            'hug': self.hug_gifs,
            'slap': self.slap_gifs,
            'pat': self.pat_gifs,
            'bite': self.bite_gifs,
            'cry': self.cry_gifs,
            'sex': self.sex_gifs
        }
        
        if action not in gifs_map:
            raise ValueError(f"Неизвестное действие: {action}")
            
        return random.choice(gifs_map[action]) 