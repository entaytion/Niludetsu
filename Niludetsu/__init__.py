"""
Niludetsu — библиотека для Discord.
Оптимизация проекта, улучшение функционала и удобство использования.
"""

__title__ = 'Niludetsu'
__author__ = 'Entaytion'
__version__ = 'beta-1'

from .core.base import BaseLogger
from .logging.logs import Logger
from .logging.users import UserLogger
from .logging.errors import ErrorLogger
from .logging.messages import MessageLogger
from .logging.channels import ChannelLogger
from .logging.server import ServerLogger
from .logging.applications import ApplicationLogger
from .logging.emojis import EmojiLogger
from .logging.events import EventLogger
from .logging.invites import InviteLogger
from .logging.roles import RoleLogger
from .logging.webhooks import WebhookLogger
from .logging.stickers import StickerLogger
from .logging.soundboards import SoundboardLogger
from .logging.threads import ThreadLogger
from .logging.voice import VoiceLogger

# Для удобного импорта
__all__ = [
    'BaseLogger',
    'Logger',
    'UserLogger',
    'MessageLogger',
    'ChannelLogger',
    'ServerLogger',
    'ApplicationLogger',
    'EmojiLogger',
    'EventLogger',
    'ErrorLogger',
    'InviteLogger',
    'RoleLogger',
    'WebhookLogger',
    'StickerLogger',
    'SoundboardLogger',
    'ThreadLogger',
    'VoiceLogger',
] 