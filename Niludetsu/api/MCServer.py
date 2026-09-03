from ..locale import _
from ..tools.Embed import Embed
"""
Модуль для взаимодействия с Minecraft серверами
"""

import datetime, discord, re
from discord.ext import commands
from mcstatus import JavaServer, BedrockServer

from typing import Optional, Dict, Any, Tuple

class MinecraftServerAPI:

    def __init__(self):
        self.java_default_port = 25565
        self.bedrock_default_port = 19132

    async def get_java_server_data(self, address: str, port: Optional[int] = None) -> Dict[str, Any]:
        try:
            if port:
                server = JavaServer(address, port)
            else:
                server = JavaServer.lookup(address)

            status = await server.async_status()

            try:
                ping = await server.async_ping()
            except:
                ping = None

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
            return {
                'online': False,
                'error': f"Ошибка подключения: {str(e)}"
            }

    async def get_bedrock_server_data(self, address: str, port: Optional[int] = None) -> Dict[str, Any]:
        try:
            if port:
                server = BedrockServer(address, port)
            else:
                server = BedrockServer(address, self.bedrock_default_port)

            status = await server.async_status()

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
            return {
                'online': False,
                'error': f"Ошибка подключения: {str(e)}"
            }

    def validate_server_address(self, address: str, port: Optional[int] = None, t=None) -> Tuple[bool, str]:
        if t is None:
            from ..locale import _ as locale_fn
            t = locale_fn()
        
        if not address or not address.strip():
            return False, t("api_mcserver", "invalid_address")

        if len(address) > 253:
            return False, t("api_mcserver", "address_too_long")

        if port is not None:
            if not isinstance(port, int) or port < 1 or port > 65535:
                return False, t("api_mcserver", "invalid_port")

        if any(char in address for char in ['<', '>', '"', '|', '?', '*']):
            return False, t("api_mcserver", "invalid_chars")

        return True, ""

    def check_server_status(self, server_info: Dict[str, Any]) -> Tuple[str, discord.Color]:
        if not server_info.get('online', False):
            return "🔴", discord.Color.red()

        players_online = server_info.get('players_online', 0)
        players_max = server_info.get('players_max', 0)

        if players_max > 0 and players_online / players_max > 0.9:
            return "🟠", discord.Color.orange()

        if players_online == 0:
            return "🟡", discord.Color.gold()

        return "🟢", discord.Color.green()

    async def get_server_info(self, ctx: commands.Context, address: str, port: Optional[int] = None, bedrock: bool = False):
        is_valid, error_message = self.validate_server_address(address, port)
        if not is_valid:
            await ctx.reply(embed=Embed.error(title="Ошибка валидации", description=error_message))
            return

        try:
            server_address = address
            if port:
                server_address = f"{address}:{port}"

            if bedrock:
                server_info = await self.get_bedrock_server_data(address, port)
            else:
                server_info = await self.get_java_server_data(address, port)

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

            embed = self._format_server_embed(server_info, server_address, bedrock)
            await ctx.reply(embed=embed)

        except Exception as e:
            error_embed = Embed.error(description=f"Произошла ошибка: {str(e)}")
            await ctx.reply(embed=error_embed)

    def _format_server_embed(self, server_info: Dict[str, Any], address: str, is_bedrock: bool, t) -> Embed:
        emoji, color = self.check_server_status(server_info)

        title = f"{emoji} {address} | {server_info.get('type', '')}"

        embed = Embed(title=title, color=color)

        description = self._build_server_description(server_info, is_bedrock, t)
        embed.description = "\n".join(description)

        if not is_bedrock and server_info.get('favicon'):
            if self._is_valid_favicon(server_info.get('favicon', '')):
                try:
                    embed.set_thumbnail(url=server_info.get('favicon'))
                except Exception as e:
                    print(f"Ошибка при установке иконки сервера: {e}")

        embed.set_footer(text=t("api_mcserver", "footer_done"))
        embed.timestamp = datetime.datetime.now()

        return embed

    def _build_server_description(self, server_info: Dict[str, Any], is_bedrock: bool, t) -> list:
        description = []

        version_str = f"**{t('api_mcserver', 'version')}:** `{server_info.get('version', t('api_mcserver', 'unknown'))}`"
        if server_info.get('protocol'):
            version_str += f" ({t('api_mcserver', 'protocol')}: {server_info.get('protocol')})"
        description.append(version_str)

        players_online = server_info.get('players_online', 0)
        players_max = server_info.get('players_max', 0)
        players_str = f"**{t('api_mcserver', 'players')}:** `{players_online}/{players_max}`"
        description.append(players_str)

        if not is_bedrock and server_info.get('ping') is not None:
            ping_str = f"**{t('api_mcserver', 'ping')}:** `{round(server_info.get('ping', 0))} мс`"
            description.append(ping_str)
        elif is_bedrock and server_info.get('latency') is not None:
            latency_str = f"**{t('api_mcserver', 'latency')}:** `{round(server_info.get('latency', 0) * 1000)} мс`"
            description.append(latency_str)

        if is_bedrock:
            if server_info.get('edition'):
                description.append(f"**{t('api_mcserver', 'edition')}:** `{server_info.get('edition')}`")
            if server_info.get('game_mode'):
                description.append(f"**{t('api_mcserver', 'game_mode')}:** `{server_info.get('game_mode')}`")
            if server_info.get('map_name'):
                description.append(f"**{t('api_mcserver', 'map')}:** `{server_info.get('map_name')}`")

        description_text = self._get_server_description_text(server_info, is_bedrock)
        if description_text:
            description.append(f"**{t('api_mcserver', 'description')}:**\n```{description_text}```")

        if not is_bedrock and server_info.get('players_sample'):
            players_list_str = self._format_players_list(server_info.get('players_sample', []))
            if players_list_str:
                description.append(f"**{t('api_mcserver', 'players_online')}:** {players_list_str}")

        return description

    def _get_server_description_text(self, server_info: Dict[str, Any], is_bedrock: bool) -> str:
        description_text = ""

        if is_bedrock and server_info.get('motd'):
            description_text = self._clean_minecraft_formatting(server_info.get('motd', ''))
        elif not is_bedrock and server_info.get('description'):
            if isinstance(server_info.get('description'), str):
                description_text = self._clean_minecraft_formatting(server_info.get('description', ''))
            else:
                try:
                    description_text = server_info.get('description').to_plain()
                except:
                    description_text = str(server_info.get('description', ''))

        return description_text

    def _format_players_list(self, players_sample: list) -> str:
        if not players_sample:
            return ""

        players_list = ", ".join(f"`{player}`" for player in players_sample[:10])
        if len(players_sample) > 10:
            players_list += f" и еще {len(players_sample) - 10}..."

        return players_list

    def _is_valid_favicon(self, favicon: str) -> bool:
        if len(favicon) > 2000:
            return False

        if favicon.startswith('data:image/'):
            return False

        if not favicon.startswith(('http://', 'https://')):
            return False

        return True

    def _clean_minecraft_formatting(self, text: str) -> str:
        return re.sub(r'§[0-9a-fk-r]', '', text)

minecraft_server_api = MinecraftServerAPI()

