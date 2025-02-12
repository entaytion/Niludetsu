"""
Niludetsu - библиотека для создания Discord бота.
Основной функционал, работа с серверами, музыка, игры, API, и многое другое.
"""

from . import core
from . import utils
from . import logging
from . import music
from . import api
from . import moderation

__version__ = "beta-9"
__author__ = "Entaytion"
__license__ = "GNU General Public License v3.0"

__all__ = [
    'core',
    'utils',
    'logging',
    'music',
    'api',
    'moderation'
] 