"""
Система логирования Niludetsu
Включает логгеры для различных событий Discord: сообщения, роли, каналы, и т.д.
"""
from .applications import ApplicationLogger
from .automod import AutoModLogger
from .channels import ChannelLogger
from .emojis import EmojiLogger
from .entitlements import EntitlementLogger
from .errors import ErrorLogger
from .events import EventLogger
from .invites import InviteLogger
from .messages import MessageLogger
from .polls import PollLogger
from .roles import RoleLogger
from .server import ServerLogger
from .soundboards import SoundboardLogger
from .stage import StageLogger
from .stickers import StickerLogger
from .threads import ThreadLogger
from .users import UserLogger
from .voice import VoiceLogger
from .webhooks import WebhookLogger

__all__ = [
    # Основные логгеры
    'ApplicationLogger',
    'AutoModLogger',
    'ChannelLogger',
    'EmojiLogger',
    'EntitlementLogger',
    'ErrorLogger',
    'EventLogger',
    'InviteLogger',
    'MessageLogger',
    'PollLogger',
    'RoleLogger',
    'ServerLogger',
    'SoundboardLogger',
    'StageLogger',
    'StickerLogger',
    'ThreadLogger',
    'UserLogger',
    'VoiceLogger',
    'WebhookLogger'
] 