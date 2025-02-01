from typing import List
import random

class GifsAPI:
    """Класс для работы с гифками для различных действий"""
    
    def __init__(self):
        # Гифки для поцелуев
        self.kiss_gifs = [
            "https://media1.tenor.com/m/-FL3wqNmAtEAAAAC/beijo-kiss.gif",
            "https://media1.tenor.com/m/cQzRWAWrN6kAAAAC/ichigo-hiro.gif", 
            "https://media1.tenor.com/m/WN1SVoPkdRIAAAAC/anime-kiss.gif",
            "https://media1.tenor.com/m/Daj-Pn82PagAAAAC/gif-kiss.gif",
            "https://media1.tenor.com/m/NmqGI0KNVcIAAAAd/neko-tan.gif",
            "https://media1.tenor.com/m/NZUQilMD3IIAAAAd/horimiya-izumi-miyamura.gif"
        ]
        
        # Гифки для объятий
        self.hug_gifs = [
            "https://media1.tenor.com/m/NZUQilMD3IIAAAAd/horimiya-izumi-miyamura.gif",
            "https://media1.tenor.com/m/2HxamDEy7XAAAAAC/yukon-child-form-embracing-ulquiorra.gif",
            "https://media1.tenor.com/m/nwxXREHNog0AAAAd/hug-anime.gif",
            "https://media1.tenor.com/m/wWFm70VeC7YAAAAC/hug-darker-than-black.gif",
            "https://media1.tenor.com/m/cBcV5uqNYvYAAAAC/fruits-basket-fruits.gif",
            "https://media1.tenor.com/m/tbzuQSodu58AAAAC/oshi-no-ko-onk.gif"
        ]
        
        # Гифки для ударов
        self.slap_gifs = [
            "https://media1.tenor.com/m/Ws6Dm1ZW_vMAAAAC/girl-slap.gif",
            "https://media1.tenor.com/m/Sv8LQZAoQmgAAAAC/chainsaw-man-csm.gif",
            "https://media1.tenor.com/m/XiYuU9h44-AAAAAC/anime-slap-mad.gif",
            "https://media1.tenor.com/m/E3OW-MYYum0AAAAC/no-angry.gif",
            "https://media1.tenor.com/m/wOCOTBGZJyEAAAAC/chikku-neesan-girl-hit-wall.gif"
        ]
        
        # Гифки для поглаживаний
        self.pat_gifs = [
            "https://media1.tenor.com/m/7xrOS-GaGAIAAAAC/anime-pat-anime.gif",
            "https://media1.tenor.com/m/079CvbmFPe8AAAAC/qualidea-code-head-pat.gif",
            "https://media1.tenor.com/m/E6fMkQRZBdIAAAAC/kanna-kamui-pat.gif",
            "https://media1.tenor.com/m/oGbO8vW_eqgAAAAC/spy-x-family-anya.gif"
        ]
        
        # Гифки для укусов
        self.bite_gifs = [
            "https://media1.tenor.com/m/5mVQ3ffWUTgAAAAC/anime-bite.gif",
            "https://media1.tenor.com/m/KXEaZ6NcHAAAAAAC/anime-bite.gif",
            "https://media1.tenor.com/m/_AkeqheWU-4AAAAC/anime-bite.gif",
            "https://media1.tenor.com/m/QvLlkNlsRDAAAAAC/nom-nom-anime-love.gif",
            "https://media1.tenor.com/m/PDc8mCQNqqcAAAAC/vanitas-no-carte-anime-bite.gif"
        ]
        
        # Гифки для плача
        self.cry_gifs = [
            "https://media1.tenor.com/m/Xowou_HAVZMAAAAd/anime-cry.gif",
            "https://media1.tenor.com/m/fmB1LPfUc5AAAAAC/waaa.gif",
            "https://media1.tenor.com/m/35S_M89zT3sAAAAd/horimiya-anime.gif",
            "https://media1.tenor.com/m/GPuOivyCUjoAAAAC/anime-spyxfamily.gif",
            "https://media1.tenor.com/m/EhwgANzgzdIAAAAC/anime-cry.gif"
        ]
        
        # Гифки для секса
        self.sex_gifs = [
            "https://media1.tenor.com/m/Hu-DzekBgw0AAAAC/sex.gif",
            "https://media1.tenor.com/m/5Me54nLWWE8AAAAC/anime-sex-sign.gif",
            "https://media1.tenor.com/m/9G1zsVIiV6UAAAAC/anime-bed.gif",
            "https://media1.tenor.com/m/FmBSx-Wr1QgAAAAd/anime-redo-of-healer.gif",
            "https://media1.tenor.com/m/WdL_1rUZbhgAAAAC/squeeze-boobs-sexual.gif",
            "https://media1.tenor.com/m/j9FGUPo-9VUAAAAC/cum-cumshot.gif"
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