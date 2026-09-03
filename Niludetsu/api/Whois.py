from ..locale import _
from ..tools.Embed import Colors, Embed
from ..tools.Time import TimeService
"""
Модуль для получения информации о доменах и IP-адресах (WhoIs)
"""

import aiohttp, asyncio, dns.exception, dns.resolver, ipaddress, re, whois
from datetime import datetime
from functools import lru_cache

from typing import Dict, Any, Tuple, Optional, List
from urllib.parse import urlparse

class WhoisAPI:
    """Класс для работы с WhoIs информацией"""

    # Константы класса (используются всеми экземплярами)
    REQUEST_TIMEOUT = 10
    WHOIS_TIMEOUT = 15
    MAX_INPUT_LENGTH = 253
    MAX_SUBDOMAINS = 5

    DOMAIN_PATTERN = re.compile(
        r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*'
        r'[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$'
    )

    PUBLIC_DNS_SERVERS = ('8.8.8.8', '1.1.1.1', '208.67.222.222')
    BLOCKED_DOMAINS = frozenset(['localhost', '127.0.0.1', '0.0.0.0'])

    IP_API_URLS = (
        "http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,"
        "region,regionName,city,zip,lat,lon,timezone,isp,org,as,query",
        "https://ipapi.co/{ip}/json/"
    )

    def __init__(self):
        """Инициализация WhoIs API"""
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Ленивая инициализация aiohttp сессии"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.REQUEST_TIMEOUT),
                headers={'User-Agent': 'Discord Bot WhoIs Lookup'}
            )
        return self._session

    async def close(self):
        """Закрытие сессии"""
        if self._session and not self._session.closed:
            await self._session.close()

    @staticmethod
    @lru_cache(maxsize=256)
    def normalize_input(target: str) -> str:
        """
        Нормализует входную строку (с кешированием)

        Parameters
        ----------
        target : str
            Исходная строка (домен или IP)

        Returns
        -------
        str
            Нормализованная строка
        """
        if not target:
            return ""

        target = target.strip().lower()

        # Извлечение домена из URL
        if target.startswith(('http://', 'https://', 'ftp://', 'ftps://')):
            try:
                parsed = urlparse(target)
                target = parsed.hostname or parsed.netloc
            except Exception:
                pass

        # Удаление порта (если не IPv6)
        if ':' in target and '[' not in target:
            try:
                ipaddress.IPv6Address(target)
            except ipaddress.AddressValueError:
                target = target.split(':')[0]

        # Удаление www. префикса
        return target[4:] if target.startswith('www.') else target

    def validate_input(self, target: str) -> Tuple[bool, str, str]:
        """
        Валидирует входные данные

        Parameters
        ----------
        target : str
            Цель для проверки (домен или IP)

        Returns
        -------
        Tuple[bool, str, str]
            Кортеж (валидность, тип, сообщение об ошибке)
        """
        if not target:
            return False, "", "Цель не может быть пустой"

        if len(target) > self.MAX_INPUT_LENGTH:
            return False, "", f"Слишком длинная строка (максимум {self.MAX_INPUT_LENGTH} символов)"

        if target in self.BLOCKED_DOMAINS:
            return False, "", "Эта цель заблокирована"

        # Проверка IP-адреса
        if ip_type := self._validate_ip(target):
            return True, ip_type, ""

        # Проверка домена
        if self._validate_domain(target):
            return True, "domain", ""

        return False, "", "Некорректный формат домена или IP-адреса"

    @staticmethod
    def _validate_ip(target: str) -> Optional[str]:
        """Проверяет, является ли строка корректным IP-адресом"""
        try:
            ip = ipaddress.ip_address(target)

            if ip.is_private or ip.is_reserved or ip.is_loopback:
                return None

            return "ipv4" if ip.version == 4 else "ipv6"

        except ipaddress.AddressValueError:
            return None

    def _validate_domain(self, target: str) -> bool:
        """Проверяет, является ли строка корректным доменом"""
        if not target or len(target) > 253:
            return False

        if not self.DOMAIN_PATTERN.match(target):
            return False

        parts = target.split('.')
        if len(parts) < 2:
            return False

        return all(
            part and len(part) <= 63 and not part.startswith('-') and not part.endswith('-')
            for part in parts
        )

    async def get_ip_info(self, ip: str) -> Dict[str, Any]:
        """
        Получает информацию об IP-адресе (асинхронно с aiohttp)

        Parameters
        ----------
        ip : str
            IP-адрес для поиска

        Returns
        -------
        Dict[str, Any]
            Словарь с информацией об IP-адресе
        """
        session = await self._get_session()

        for api_url in self.IP_API_URLS:
            try:
                url = api_url.format(ip=ip)
                async with session.get(url) as response:
                    if response.status != 200:
                        continue

                    data = await response.json()

                    # Нормализация данных
                    if 'ip-api.com' in api_url and data.get('status') == 'success':
                        return self._normalize_ip_api_data(data)
                    elif 'ipapi.co' in api_url and not data.get('error'):
                        return self._normalize_ipapi_data(data)

            except Exception as e:
                print(f"Ошибка при запросе к {api_url}: {e}")
                continue

        return {"status": "error", "message": "Не удалось получить информацию"}

    @staticmethod
    def _normalize_ip_api_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Нормализует данные от ip-api.com"""
        return {
            "status": "success",
            "ip": data.get("query"),
            "country": data.get("country"),
            "country_code": data.get("countryCode"),
            "region": data.get("regionName"),
            "city": data.get("city"),
            "zip": data.get("zip"),
            "latitude": data.get("lat"),
            "longitude": data.get("lon"),
            "timezone": data.get("timezone"),
            "isp": data.get("isp"),
            "org": data.get("org"),
            "as": data.get("as"),
        }

    @staticmethod
    def _normalize_ipapi_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Нормализует данные от ipapi.co"""
        return {
            "status": "success",
            "ip": data.get("ip"),
            "country": data.get("country_name"),
            "country_code": data.get("country_code"),
            "region": data.get("region"),
            "city": data.get("city"),
            "zip": data.get("postal"),
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "timezone": data.get("timezone"),
            "isp": data.get("org"),
            "org": data.get("org"),
        }

    async def get_domain_info(self, domain: str) -> Optional[Any]:
        """
        Получает информацию о домене

        Parameters
        ----------
        domain : str
            Домен для поиска

        Returns
        -------
        Optional[Any]
            Объект с информацией о домене или None
        """
        try:
            loop = asyncio.get_event_loop()
            domain_info = await asyncio.wait_for(
                loop.run_in_executor(None, whois.whois, domain),
                timeout=self.WHOIS_TIMEOUT
            )
            return domain_info

        except asyncio.TimeoutError:
            print(f"Таймаут при получении whois для {domain}")
            return None
        except Exception as e:
            print(f"Ошибка при получении whois для {domain}: {e}")
            return None

    async def get_dns_info(self, domain: str) -> Dict[str, List[str]]:
        """
        Получает DNS информацию о домене

        Parameters
        ----------
        domain : str
            Домен для поиска

        Returns
        -------
        Dict[str, List[str]]
            Словарь с DNS записями
        """
        dns_info = {
            'A': [], 'AAAA': [], 'MX': [],
            'NS': [], 'TXT': [], 'CNAME': []
        }

        try:
            resolver = dns.resolver.Resolver()
            resolver.timeout = 5
            resolver.lifetime = 5

            # Параллельный запрос всех типов записей
            tasks = [
                self._resolve_dns_record(resolver, domain, record_type)
                for record_type in dns_info.keys()
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for record_type, result in zip(dns_info.keys(), results):
                if isinstance(result, list):
                    dns_info[record_type] = result

        except Exception as e:
            print(f"Ошибка при получении DNS информации для {domain}: {e}")

        return dns_info

    @staticmethod
    async def _resolve_dns_record(resolver, domain: str, record_type: str) -> List[str]:
        """Резолвит конкретный тип DNS записи"""
        try:
            loop = asyncio.get_event_loop()
            answers = await loop.run_in_executor(
                None, resolver.resolve, domain, record_type
            )

            if record_type == 'MX':
                return [f"{answer.preference} {answer.exchange}" for answer in answers]
            return [str(answer) for answer in answers]

        except dns.exception.DNSException:
            return []

    def format_ip_embed(self, embed: Embed, ip: str, ip_info: Dict[str, Any], t) -> Embed:
        """Форматирует эмбед с информацией об IP-адресе"""
        if ip_info.get("status") != "success":
            embed.color = Colors.ERROR
            embed.add_field(
                name=t("api_whois", "error"),
                value=f"`{ip_info.get('message', t('api_whois', 'unknown_ip'))}`",
                inline=False
            )
            return embed

        embed.color = Colors.SUCCESS

        # Список полей для добавления
        fields = [
            (t("api_whois", "ip_address"), f"`{ip}`", True),
        ]

        if country := ip_info.get('country'):
            flag = self._get_country_flag(ip_info.get('country_code', ''))
            fields.append((t("api_whois", "country"), f"{flag} `{country}`", True))

        if region := ip_info.get('region'):
            fields.append((t("api_whois", "region"), f"`{region}`", True))

        if city := ip_info.get('city'):
            fields.append((t("api_whois", "city"), f"`{city}`", True))

        if isp := ip_info.get('isp'):
            fields.append((t("api_whois", "provider"), f"`{isp}`", True))

        if (org := ip_info.get('org')) and org != ip_info.get('isp'):
            fields.append((t("api_whois", "organization"), f"`{org}`", True))

        if timezone := ip_info.get('timezone'):
            fields.append((t("api_whois", "timezone"), f"`{timezone}`", True))

        if (lat := ip_info.get('latitude')) and (lon := ip_info.get('longitude')):
            fields.extend([
                (t("api_whois", "coordinates"), f"`{lat}, {lon}`", True),
                (t("api_whois", "map"), f"[{t('api_whois', 'show_on_map')}](https://www.google.com/maps?q={lat},{lon})", True)
            ])

        if as_info := ip_info.get('as'):
            fields.append(("🔗 AS", f"`{as_info}`", False))

        # Массовое добавление полей
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)

        return embed

    def format_domain_embed(
        self, 
        embed: Embed, 
        domain: str, 
        domain_info: Any, 
        dns_info: Optional[Dict[str, List[str]]] = None,
        t = None
    ) -> Embed:
        """Форматирует эмбед с информацией о домене"""
        if t is None:
            from ..locale import _ as _lf
            t = _lf()
        if not domain_info:
            embed.color = Colors.ERROR
            embed.add_field(
                name=t("api_whois", "error"),
                value=t("api_whois", "domain_error"),
                inline=False
            )
            return embed

        embed.color = Colors.SUCCESS
        embed.add_field(name=t("api_whois", "domain"), value=f"`{domain}`", inline=True)

        # Регистратор
        if registrar := self._extract_field(domain_info, 'registrar'):
            embed.add_field(name=t("api_whois", "registrar"), value=f"`{registrar}`", inline=True)

        # Статус
        if status := self._extract_field(domain_info, 'status'):
            if isinstance(status, list):
                status = ', '.join(status[:3])
            embed.add_field(name=t("api_whois", "status"), value=f"`{status}`", inline=True)

        # Даты
        now = TimeService.now()

        if creation_date := self._extract_date(domain_info, 'creation_date'):
            formatted = TimeService.format(creation_date, '%d.%m.%Y')
            days_ago = (now - creation_date).days
            embed.add_field(
                name=t("api_whois", "created_date"),
                value=f"`{formatted}`\n*({days_ago} {t('api_whois', 'days_ago')})*",
                inline=True
            )

        if expiration_date := self._extract_date(domain_info, 'expiration_date'):
            formatted = TimeService.format(expiration_date, '%d.%m.%Y')
            days_left = (expiration_date - now).days
            emoji = "🟢" if days_left > 30 else "🟡" if days_left > 7 else "🔴"
            embed.add_field(
                name=t("api_whois", "expiration_date"),
                value=f"{emoji} `{formatted}`\n*({days_left} {t('api_whois', 'days_left')})*",
                inline=True
            )

        if updated_date := self._extract_date(domain_info, 'updated_date'):
            formatted = TimeService.format(updated_date, '%d.%m.%Y')
            embed.add_field(name=t("api_whois", "updated_date"), value=f"`{formatted}`", inline=True)

        # Серверы имён
        if ns_list := self._extract_field(domain_info, 'name_servers'):
            if isinstance(ns_list, list):
                ns_text = '\n'.join([f"`{server.lower()}`" for server in ns_list[:5]])
                if len(ns_list) > 5:
                    ns_text += f"\n*{t('api_whois', 'more_servers', count=len(ns_list) - 5)}*"
            else:
                ns_text = f"`{ns_list}`"
            embed.add_field(name=t("api_whois", "name_servers"), value=ns_text, inline=False)

        # DNS информация
        if dns_info:
            self._add_dns_info_to_embed(embed, dns_info, t)

        return embed

    @staticmethod
    def _extract_field(domain_info: Any, field_name: str) -> Any:
        """Извлекает поле из объекта домена"""
        if not hasattr(domain_info, field_name):
            return None
        value = getattr(domain_info, field_name)
        return value[0] if isinstance(value, list) and value else value

    @staticmethod
    def _extract_date(domain_info: Any, field_name: str) -> Optional[datetime]:
        """Извлекает дату из объекта домена"""
        if not hasattr(domain_info, field_name):
            return None
        date_value = getattr(domain_info, field_name)
        return date_value[0] if isinstance(date_value, list) and date_value else date_value

    @staticmethod
    def _add_dns_info_to_embed(embed: Embed, dns_info: Dict[str, List[str]], t):
        """Добавляет DNS информацию в эмбед с локализацией"""
        dns_fields = []

        if a_records := dns_info.get('A'):
            dns_fields.append(f"**A {t('api_whois', 'dns_records')}:** {', '.join([f'`{r}`' for r in a_records[:3]])}")

        if aaaa_records := dns_info.get('AAAA'):
            dns_fields.append(f"**AAAA {t('api_whois', 'dns_records')}:** {', '.join([f'`{r}`' for r in aaaa_records[:2]])}")

        if mx_records := dns_info.get('MX'):
            dns_fields.append(f"**MX {t('api_whois', 'dns_records')}:** {', '.join([f'`{r}`' for r in mx_records[:3]])}")

        if dns_fields:
            embed.add_field(
                name=t("api_whois", "dns_section"),
                value='\n'.join(dns_fields),
                inline=False
            )

    @staticmethod
    @lru_cache(maxsize=128)
    def _get_country_flag(country_code: str) -> str:
        """Получает эмодзи флага по коду страны (с кешированием)"""
        if not country_code or len(country_code) != 2:
            return "🏳️"

        try:
            return ''.join(chr(ord(c) + 127397) for c in country_code.upper())
        except Exception:
            return "🏳️"

    async def whois_lookup(self, ctx, target: str):
        """
        Выполняет WhoIs поиск и отправляет результат

        Parameters
        ----------
        ctx : commands.Context
            Контекст команды Discord
        target : str
            Цель для поиска (домен или IP)
        """
        t = _(ctx=ctx)
        
        if not target:
            embed = Embed.error(
                title=t("api_whois", "missing_params"),
                description=t("api_whois", "specify_param"),
            )
            await ctx.reply(embed=embed)
            return

        normalized_target = self.normalize_input(target)
        is_valid, target_type, error_message = self.validate_input(normalized_target)

        if not is_valid:
            await ctx.reply(embed=Embed.error(
                title=t("api_whois", "validation_error"),
                description=f"{error_message}\n**{t('api_whois', 'input_was')}:** `{target}`"
            ))
            return

        loading_embed = Embed(
            title=t("api_whois", "searching"),
            description=t("api_whois", "fetching_info", target=normalized_target),
            color=Colors.WARNING
        )
        message = await ctx.reply(embed=loading_embed)

        try:
            embed = Embed(
                title=t("api_whois", "result_title", target=normalized_target),
                color=Colors.PRIMARY
            )

            if target_type in ('ipv4', 'ipv6'):
                ip_info = await self.get_ip_info(normalized_target)
                embed = self.format_ip_embed(embed, normalized_target, ip_info, t)

            elif target_type == 'domain':
                # Параллельное выполнение whois и DNS запросов
                domain_info, dns_info = await asyncio.gather(
                    self.get_domain_info(normalized_target),
                    self.get_dns_info(normalized_target)
                )
                embed = self.format_domain_embed(embed, normalized_target, domain_info, dns_info, t)

            if normalized_target != target:
                embed.set_footer(text=f"Исходный запрос: {target}")

            await message.edit(embed=embed)

        except Exception as e:
            error_embed = Embed.error(
                title="Ошибка при получении информации",
                description=f"Произошла ошибка при обработке запроса для `{normalized_target}`"
            )
            await message.edit(embed=error_embed)
            print(f"Ошибка в whois_lookup: {e}")

# Создаем экземпляр для импорта
whois_api = WhoisAPI()

