"""
API интеграции для Niludetsu
"""

from .Akinator import AkinatorAPI
from .Currency import CurrencyAPI
from .Gifs import GifsAPI
from .Translate import TranslateAPI
from .Weather import WeatherAPI

__all__ = [
    'AkinatorAPI',
    'CurrencyAPI', 
    'GifsAPI',
    'TranslateAPI',
    'WeatherAPI'
] 