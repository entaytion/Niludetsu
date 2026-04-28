from ..tools.Embed import Embed
"""
Модуль для взаимодействия с Minecraft серверами
"""

import datetime, discord, re
from discord.ext import commands
from mcstatus import JavaServer, BedrockServer

from typing import Optional, Dict, Any, Tuple

class MinecraftServerAPI:
    """Класс для работы с Minecraft серверами"""

    def __init__(self):
        """Инициализация класса"""
        self.java_default_port = 25565
        self.bedrock_default_port = 19132

    async def get_java_server_data(self, address: str, port: Optional[int] = None) -> Dict[str, Any]:
        """
        Получает данные о Java-сервере Minecraft

        Parameters
        ----------
        address : str
            IP-адрес или доменное имя сервера
        port : Optional[int]
            Порт сервера (по умолчанию: 25565)

        Returns
        -------
        Dict[str, Any]
            Словарь с информацией о сервере
        """
        try:
            # Создаем объект сервера
            if port:
                server = JavaServer(address, port)
            else:
                server = JavaServer.lookup(address)

            # Получаем статус сервера
            status = await server.async_status()

            # Получаем пинг сервера
            try:
                ping = await server.async_ping()
            except:
                ping = None

            # Собираем информацию о сервере
            server_info = {
                'online': True,
                'version': status.version.name,
                'protocol': status.version.protocol,
                'players_online': status.players.online,
                'players_max': status.players.max,
                'players_sample': [player.name for player in (status.players.sample or [])],
                'description': status.description,
                'favicon': getattr(status, 'favicon', None),
                'ping': ping,
                'type': 'Java Edition'
            }

            return server_info
        except Exception as e:
            # Возвращаем информацию об ошибке
            return {
                'online': False,
                'error': f"Ошибка подключения: {str(e)}"
            }

    async def get_bedrock_server_data(self, address: str, port: Optional[int] = None) -> Dict[str, Any]:
        """
        Получает данные о Bedrock-сервере Minecraft

        Parameters
        ----------
        address : str
            IP-адрес или доменное имя сервера
        port : Optional[int]
            Порт сервера (по умолчанию: 19132)

        Returns
        -------
        Dict[str, Any]
            Словарь с информацией о сервере
        """
        try:
            # Создаем объект сервера
            if port:
                server = BedrockServer(address, port)
            else:
                server = BedrockServer(address, self.bedrock_default_port)

            # Получаем статус сервера
            status = await server.async_status()

            # Собираем информацию о сервере
            server_info = {
                'online': True,
                'version': status.version.version,
                'protocol': status.version.protocol,
                'players_online': status.players_online,
                'players_max': status.players_max,
                'edition': status.edition,
                'game_mode': status.game_mode,
                'map_name': status.map_name,
                'motd': status.motd,
                'latency': status.latency,
                'type': 'Bedrock Edition'
            }

            return server_info
        except Exception as e:
            # Возвращаем информацию об ошибке
            return {
                'online': False,
                'error': f"Ошибка подключения: {str(e)}"
            }

    def validate_server_address(self, address: str, port: Optional[int] = None) -> Tuple[bool, str]:
        """
        Валидирует адрес сервера

        Parameters
        ----------
        address : str
            Адрес сервера
        port : Optional[int]
            Порт сервера

        Returns
        -------
        Tuple[bool, str]
            Кортеж (валидность, сообщение об ошибке)
        """
        if not address or not address.strip():
            return False, "Адрес сервера не может быть пустым"

        if len(address) > 253:
            return False, "Адрес сервера слишком длинный"

        if port is not None:
            if not isinstance(port, int) or port < 1 or port > 65535:
                return False, "Порт должен быть числом от 1 до 65535"

        # Проверяем на недопустимые символы
        if any(char in address for char in ['<', '>', '"', '|', '?', '*']):
            return False, "Адрес содержит недопустимые символы"

        return True, ""

    def check_server_status(self, server_info: Dict[str, Any]) -> Tuple[str, discord.Color]:
        """
        Определяет статус сервера и возвращает соответствующий эмодзи и цвет

        Parameters
        ----------
        server_info : Dict[str, Any]
            Информация о сервере

        Returns
        -------
        Tuple[str, discord.Color]
            Кортеж (эмодзи, цвет)
        """
        if not server_info.get('online', False):
            return "🔴", discord.Color.red()

        players_online = server_info.get('players_online', 0)
        players_max = server_info.get('players_max', 0)

        # Если сервер заполнен более чем на 90%
        if players_max > 0 and players_online / players_max > 0.9:
            return "🟠", discord.Color.orange()

        # Если сервер пустой
        if players_online == 0:
            return "🟡", discord.Color.gold()

        # Обычное состояние
        return "🟢", discord.Color.green()

    async def get_server_info(self, ctx: commands.Context, address: str, port: Optional[int] = None, bedrock: bool = False):
        """
        Получает информацию о сервере и отправляет пользователю

        Parameters
        ----------
        ctx : commands.Context
            Контекст команды Discord
        address : str
            Адрес сервера
        port : Optional[int]
            Порт сервера
        bedrock : bool
            Флаг Bedrock Edition
        """
        # Валидация входных данных
        is_valid, error_message = self.validate_server_address(address, port)
        if not is_valid:
            await ctx.reply(embed=Embed.error(title="Ошибка валидации", description=error_message))
            return

        try:
            # Формируем полный адрес для отображения
            server_address = address
            if port:
                server_address = f"{address}:{port}"

            # Получаем информацию о сервере
            if bedrock:
                server_info = await self.get_bedrock_server_data(address, port)
            else:
                server_info = await self.get_java_server_data(address, port)

            # Проверяем результат
            if not server_info or not server_info.get('online', False):
                error_message = "Сервер не отвечает или недоступен"
                if server_info and server_info.get('error'):
                    error_message = server_info.get('error')

                error_embed = Embed.error(
                    title=f"Сервер {server_address} недоступен", 
                    description=error_message
                )
                await ctx.reply(embed=error_embed)
                return

            # Форматируем и отправляем результат
            embed = self._format_server_embed(server_info, server_address, bedrock)
            await ctx.reply(embed=embed)

        except Exception as e:
            error_embed = Embed.error(description=f"Произошла ошибка: {str(e)}")
            await ctx.reply(embed=error_embed)

    def _format_server_embed(self, server_info: Dict[str, Any], address: str, is_bedrock: bool) -> Embed:
        """
        Форматирует эмбед с информацией о сервере

        Parameters
        ----------
        server_info : Dict[str, Any]
            Информация о сервере
        address : str
            Адрес сервера
        is_bedrock : bool
            Флаг для определения типа сервера

        Returns
        -------
        Embed
            Отформатированный эмбед
        """
        # Определяем статус и цвет
        emoji, color = self.check_server_status(server_info)

        # Формируем заголовок эмбеда
        title = f"{emoji} {address} | {server_info.get('type', '')}"

        # Создаем эмбед
        embed = Embed(title=title, color=color)

        # Формируем описание
        description = self._build_server_description(server_info, is_bedrock)
        embed.description = "\n".join(description)

        # Добавляем иконку сервера для Java, если доступна
        if not is_bedrock and server_info.get('favicon'):
            if self._is_valid_favicon(server_info.get('favicon', '')):
                try:
                    embed.set_thumbnail(url=server_info.get('favicon'))
                except Exception as e:
                    print(f"Ошибка при установке иконки сервера: {e}")

        # Добавляем футер с меткой времени
        embed.set_footer(text="Запрос выполнен")
        embed.timestamp = datetime.datetime.now()

        return embed

    def _build_server_description(self, server_info: Dict[str, Any], is_bedrock: bool) -> list:
        """
        Строит описание для эмбеда сервера

        Parameters
        ----------
        server_info : Dict[str, Any]
            Информация о сервере
        is_bedrock : bool
            Флаг Bedrock Edition

        Returns
        -------
        list
            Список строк описания
        """
        description = []

        # Добавляем информацию о версии
        version_str = f"**Версия:** `{server_info.get('version', 'Неизвестно')}`"
        if server_info.get('protocol'):
            version_str += f" (протокол: {server_info.get('protocol')})"
        description.append(version_str)

        # Добавляем информацию об игроках
        players_online = server_info.get('players_online', 0)
        players_max = server_info.get('players_max', 0)
        players_str = f"**Игроки:** `{players_online}/{players_max}`"
        description.append(players_str)

        # Добавляем пинг/задержку
        if not is_bedrock and server_info.get('ping') is not None:
            ping_str = f"**Пинг:** `{round(server_info.get('ping', 0))} мс`"
            description.append(ping_str)
        elif is_bedrock and server_info.get('latency') is not None:
            latency_str = f"**Задержка:** `{round(server_info.get('latency', 0) * 1000)} мс`"
            description.append(latency_str)

        # Дополнительная информация для Bedrock
        if is_bedrock:
            if server_info.get('edition'):
                description.append(f"**Издание:** `{server_info.get('edition')}`")
            if server_info.get('game_mode'):
                description.append(f"**Режим игры:** `{server_info.get('game_mode')}`")
            if server_info.get('map_name'):
                description.append(f"**Карта:** `{server_info.get('map_name')}`")

        # MOTD или описание
        description_text = self._get_server_description_text(server_info, is_bedrock)
        if description_text:
            description.append(f"**Описание:**\n```{description_text}```")

        # Добавляем список игроков
        if not is_bedrock and server_info.get('players_sample'):
            players_list_str = self._format_players_list(server_info.get('players_sample', []))
            if players_list_str:
                description.append(f"**Игроки online:** {players_list_str}")

        return description

    def _get_server_description_text(self, server_info: Dict[str, Any], is_bedrock: bool) -> str:
        """
        Получает и очищает описание сервера

        Parameters
        ----------
        server_info : Dict[str, Any]
            Информация о сервере
        is_bedrock : bool
            Флаг Bedrock Edition

        Returns
        -------
        str
            Очищенное описание сервера
        """
        description_text = ""

        if is_bedrock and server_info.get('motd'):
            description_text = self._clean_minecraft_formatting(server_info.get('motd', ''))
        elif not is_bedrock and server_info.get('description'):
            if isinstance(server_info.get('description'), str):
                description_text = self._clean_minecraft_formatting(server_info.get('description', ''))
            else:
                # Для Java серверов с JSON-форматированным описанием
                try:
                    description_text = server_info.get('description').to_plain()
                except:
                    description_text = str(server_info.get('description', ''))

        return description_text

    def _format_players_list(self, players_sample: list) -> str:
        """
        Форматирует список игроков

        Parameters
        ----------
        players_sample : list
            Список игроков

        Returns
        -------
        str
            Отформатированный список игроков
        """
        if not players_sample:
            return ""

        players_list = ", ".join(f"`{player}`" for player in players_sample[:10])
        if len(players_sample) > 10:
            players_list += f" и еще {len(players_sample) - 10}..."

        return players_list

    def _is_valid_favicon(self, favicon: str) -> bool:
        """
        Проверяет, является ли favicon валидным URL для Discord embed

        Parameters
        ----------
        favicon : str
            URL или Data URI иконки сервера

        Returns
        -------
        bool
            True, если favicon валидный, иначе False
        """
        # Проверяем длину URL (Discord ограничивает длину до 2048 символов)
        if len(favicon) > 2000:
            return False

        # Проверяем, является ли это data URL для изображения
        if favicon.startswith('data:image/'):
            # Для data:image URL используем стандартную иконку Minecraft
            return False

        # Проверяем, начинается ли URL с http:// или https://
        if not favicon.startswith(('http://', 'https://')):
            return False

        return True

    def _clean_minecraft_formatting(self, text: str) -> str:
        """
        Удаляет цветовые и форматирующие коды Minecraft из текста

        Parameters
        ----------
        text : str
            Текст для очистки

        Returns
        -------
        str
            Очищенный текст
        """
        # Удаляем все коды форматирования (§0-§9, §a-§f, §k-§r)
        return re.sub(r'§[0-9a-fk-r]', '', text)

# Создаем экземпляр для импорта
minecraft_server_api = MinecraftServerAPI()

