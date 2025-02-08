import discord
from discord.ext import commands
from discord import app_commands
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.constants import Emojis
import g4f
import asyncio
from typing import Optional, List, Dict
from enum import Enum

class ProviderCategory(Enum):
    NO_AUTH = "Без авторизации"
    OPTIONAL_API = "Опциональный API ключ"
    AUTO_COOKIES = "Автоматические куки"
    MANUAL_COOKIES = "Ручные куки"

class AI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Эмодзи для ИИ
        self.AI_EMOJI = "🤖"
        # Словарь провайдеров с их характеристиками
        self.provider_info: Dict[g4f.Provider, Dict] = {
            g4f.Provider.AIUncensored: {
                "name": "AI Uncensored",
                "auth": ProviderCategory.OPTIONAL_API,
                "models": ["hermes-3"],
                "default_model": "hermes-3"
            },
            g4f.Provider.AutonomousAI: {
                "name": "Autonomous AI",
                "auth": ProviderCategory.NO_AUTH,
                "models": ["llama-3.3-70b", "qwen-2.5-coder-32b", "hermes-3", "llama-3.2-90b"],
                "default_model": "llama-3.3-70b"
            },
            g4f.Provider.Blackbox: {
                "name": "Blackbox.ai",
                "auth": ProviderCategory.NO_AUTH,
                "models": ["blackboxai", "gpt-4", "gpt-4o", "gemini-1.5-flash", "gemini-1.5-pro", 
                          "claude-3.5-sonnet", "blackboxai-pro", "llama-3.1-8b", "llama-3.1-70b",
                          "mixtral-7b", "deepseek-chat", "dbrx-instruct"],
                "default_model": "gpt-4"
            },
            g4f.Provider.CablyAI: {
                "name": "Cably AI",
                "auth": ProviderCategory.NO_AUTH,
                "models": ["cably-80b"],
                "default_model": "cably-80b"
            },
            g4f.Provider.ChatGLM: {
                "name": "ChatGLM",
                "auth": ProviderCategory.NO_AUTH,
                "models": ["glm-4"],
                "default_model": "glm-4"
            },
            g4f.Provider.ChatGpt: {
                "name": "ChatGPT",
                "auth": ProviderCategory.NO_AUTH,
                "models": ["gpt-3.5-turbo"],
                "default_model": "gpt-3.5-turbo"
            },
            g4f.Provider.ChatGptEs: {
                "name": "ChatGPT ES",
                "auth": ProviderCategory.NO_AUTH,
                "models": ["gpt-4", "gpt-4o", "gpt-4o-mini"],
                "default_model": "gpt-4"
            },
            g4f.Provider.ChatGptt: {
                "name": "ChatGPTT",
                "auth": ProviderCategory.NO_AUTH,
                "models": ["gpt-4", "gpt-4o", "gpt-4o-mini"],
                "default_model": "gpt-4"
            },
            g4f.Provider.Cloudflare: {
                "name": "Cloudflare AI",
                "auth": ProviderCategory.AUTO_COOKIES,
                "models": ["llama-2-7b", "llama-3-8b", "llama-3.1-8b", "llama-3.2-1b", "qwen-1.5-7b"],
                "default_model": "llama-3.1-8b"
            },
            g4f.Provider.Copilot: {
                "name": "Copilot",
                "auth": ProviderCategory.OPTIONAL_API,
                "models": ["gpt-4", "gpt-4o"],
                "default_model": "gpt-4"
            },
            g4f.Provider.DarkAI: {
                "name": "Dark AI",
                "auth": ProviderCategory.NO_AUTH,
                "models": ["gpt-3.5-turbo", "gpt-4o", "llama-3.1-70b"],
                "default_model": "gpt-4o"
            },
            g4f.Provider.DDG: {
                "name": "DuckDuckGo AI",
                "auth": ProviderCategory.NO_AUTH,
                "models": ["gpt-4", "gpt-4o-mini", "claude-3-haiku", "llama-3.1-70b", "mixtral-8x7b"],
                "default_model": "gpt-4"
            },
            g4f.Provider.DeepInfraChat: {
                "name": "DeepInfra Chat",
                "auth": ProviderCategory.NO_AUTH,
                "models": ["llama-3.1-8b", "llama-3.1-70b", "deepseek-chat", "qwen-2.5-72b"],
                "default_model": "llama-3.1-70b"
            },
            g4f.Provider.Free2GPT: {
                "name": "Free2GPT",
                "auth": ProviderCategory.NO_AUTH,
                "models": ["mistral-7b"],
                "default_model": "mistral-7b"
            },
            g4f.Provider.FreeGpt: {
                "name": "FreeGPT",
                "auth": ProviderCategory.NO_AUTH,
                "models": ["gemini-1.5-pro"],
                "default_model": "gemini-1.5-pro"
            },
            g4f.Provider.GizAI: {
                "name": "Giz AI",
                "auth": ProviderCategory.NO_AUTH,
                "models": ["gemini-1.5-flash"],
                "default_model": "gemini-1.5-flash"
            },
            g4f.Provider.GPROChat: {
                "name": "GPRO Chat",
                "auth": ProviderCategory.NO_AUTH,
                "models": ["gemini-1.5-pro"],
                "default_model": "gemini-1.5-pro"
            },
            g4f.Provider.ImageLabs: {
                "name": "Image Labs",
                "auth": ProviderCategory.NO_AUTH,
                "models": ["gemini-1.5-pro"],
                "default_model": "gemini-1.5-pro"
            },
            g4f.Provider.HuggingSpace: {
                "name": "HuggingFace Space",
                "auth": ProviderCategory.OPTIONAL_API,
                "models": ["qvq-72b", "qwen-2-72b", "command-r", "command-r-plus", "command-r7b"],
                "default_model": "qwen-2-72b"
            },
            g4f.Provider.Jmuz: {
                "name": "Jmuz",
                "auth": ProviderCategory.OPTIONAL_API,
                "models": ["claude-3-haiku", "claude-3-opus", "claude-3.5-sonnet", "gemini-1.5-pro",
                          "gpt-4", "gpt-4o", "llama-3.3-70b", "mixtral-8x7b"],
                "default_model": "gpt-4"
            },
            g4f.Provider.Liaobots: {
                "name": "Liaobots",
                "auth": ProviderCategory.AUTO_COOKIES,
                "models": ["grok-2", "gpt-4o", "claude-3-opus", "gemini-1.5-pro", "claude-3.5-sonnet"],
                "default_model": "gpt-4o"
            },
            g4f.Provider.OIVSCode: {
                "name": "OI VSCode",
                "auth": ProviderCategory.NO_AUTH,
                "models": ["gpt-4o-mini"],
                "default_model": "gpt-4o-mini"
            },
            g4f.Provider.PerplexityLabs: {
                "name": "Perplexity Labs",
                "auth": ProviderCategory.NO_AUTH,
                "models": ["sonar-online", "sonar-chat", "llama-3.3-70b", "llama-3.1-8b"],
                "default_model": "sonar-chat"
            },
            g4f.Provider.Pi: {
                "name": "Pi AI",
                "auth": ProviderCategory.MANUAL_COOKIES,
                "models": ["pi"],
                "default_model": "pi"
            },
            g4f.Provider.Pizzagpt: {
                "name": "Pizza GPT",
                "auth": ProviderCategory.NO_AUTH,
                "models": ["gpt-4o-mini"],
                "default_model": "gpt-4o-mini"
            },
            g4f.Provider.PollinationsAI: {
                "name": "Pollinations AI",
                "auth": ProviderCategory.NO_AUTH,
                "models": ["gpt-4o-mini", "gpt-4o", "qwen-2.5-72b", "llama-3.3-70b", "deepseek-chat"],
                "default_model": "gpt-4o"
            },
            g4f.Provider.TeachAnything: {
                "name": "Teach Anything",
                "auth": ProviderCategory.NO_AUTH,
                "models": ["llama-3.1-70b"],
                "default_model": "llama-3.1-70b"
            },
            g4f.Provider.You: {
                "name": "You.com",
                "auth": ProviderCategory.MANUAL_COOKIES,
                "models": ["gpt-3.5-turbo"],
                "default_model": "gpt-3.5-turbo"
            },
            g4f.Provider.Yqcloud: {
                "name": "YQ Cloud",
                "auth": ProviderCategory.NO_AUTH,
                "models": ["gpt-3.5-turbo"],
                "default_model": "gpt-3.5-turbo"
            }
        }
        
        # Активные провайдеры
        self.providers = list(self.provider_info.keys())
        self.current_provider_index = 0
        self.last_used_provider = None

    async def get_ai_response(self, prompt: str) -> tuple[Optional[str], Optional[str]]:
        """Получение ответа от ИИ через g4f"""
        # Начинаем с последнего успешного провайдера, если он есть
        if self.last_used_provider and self.last_used_provider in self.providers:
            start_index = self.providers.index(self.last_used_provider)
            providers_list = self.providers[start_index:] + self.providers[:start_index]
        else:
            providers_list = self.providers

        tried_providers = []  # Список провайдеров, которые мы уже попробовали
        
        for provider in providers_list:
            if provider in tried_providers:
                continue
                
            tried_providers.append(provider)
            provider_info = self.provider_info[provider]
            model = provider_info["default_model"]
            
            try:
                # Проверяем, поддерживает ли провайдер асинхронную работу
                if hasattr(provider, 'create_async'):
                    try:
                        response = await asyncio.wait_for(
                            provider.create_async(
                                model=model,
                                messages=[{
                                    "role": "system",
                                    "content": "Ты - полезный ассистент, который отвечает на русском языке."
                                }, {
                                    "role": "user",
                                    "content": prompt
                                }]
                            ),
                            timeout=30.0  # Таймаут 30 секунд
                        )
                    except asyncio.TimeoutError:
                        continue
                else:
                    # Для синхронных провайдеров используем run_in_executor с таймаутом
                    try:
                        response = await asyncio.wait_for(
                            asyncio.get_event_loop().run_in_executor(
                                None,
                                lambda: g4f.ChatCompletion.create(
                                    model=model,
                                    messages=[{
                                        "role": "system",
                                        "content": "Ты - полезный ассистент, который отвечает на русском языке."
                                    }, {
                                        "role": "user",
                                        "content": prompt
                                    }],
                                    provider=provider
                                )
                            ),
                            timeout=30.0  # Таймаут 30 секунд
                        )
                    except asyncio.TimeoutError:
                        continue

                if response and isinstance(response, str):
                    self.last_used_provider = provider
                    return response, provider_info["name"]
                    
            except Exception as e:
                continue
        
        # Если все провайдеры перепробованы и ни один не сработал
        return None, None

    ai_group = app_commands.Group(name="ai", description="Команды для работы с ИИ")

    @ai_group.command(name="ask", description="Спросить что-то у ИИ")
    @app_commands.describe(вопрос="Ваш вопрос к ИИ")
    async def ai_ask(self, interaction: discord.Interaction, вопрос: str):
        """Команда для взаимодействия с ИИ"""
        await interaction.response.defer()
        
        response, provider_name = await self.get_ai_response(вопрос)
        
        if response:
            embed=Embed(
                title=f"{self.AI_EMOJI} Ответ ИИ",
                description=response,
                color=0x2b2d31
            )
            
            embed.add_field(
                name="📝 Запрос",
                value=f"{вопрос[:1000]}{'...' if len(вопрос) > 1000 else ''}",
                inline=False
            )
            
            if provider_name:
                embed.set_footer(text=f"Провайдер: {provider_name}")
            
            await interaction.followup.send(embed=embed)
        else:
            error_embed=Embed(
                title=f"{Emojis.ERROR} Ошибка",
                description="Не удалось получить ответ от ИИ. Все доступные провайдеры временно недоступны. Попробуйте позже.",
                color=0xe74c3c
            )
            await interaction.followup.send(embed=error_embed)

    @ai_group.command(name="providers", description="Показать список доступных провайдеров ИИ")
    async def providers_list(self, interaction: discord.Interaction):
        """Показывает список доступных провайдеров ИИ"""
        embeds = []  # Список для хранения нескольких эмбедов
        current_embed=Embed(
            title=f"{self.AI_EMOJI} Доступные провайдеры ИИ (Часть 1)",
            color=0x2b2d31
        )
        
        # Группируем провайдеры по типу авторизации
        providers_by_auth = {}
        for provider, info in self.provider_info.items():
            auth_type = info["auth"]
            if auth_type not in providers_by_auth:
                providers_by_auth[auth_type] = []
            
            status = "🟢" if provider == self.last_used_provider else "⚪"
            # Сокращаем информацию о моделях
            models_str = ", ".join(info["models"][:2])
            if len(info["models"]) > 2:
                models_str += f" +{len(info['models'])-2}"
                
            provider_text = (
                f"{status} **{info['name']}** (`{info['default_model']}`)"
            )
            providers_by_auth[auth_type].append(provider_text)

        field_count = 0
        embed_count = 1
        
        # Добавляем провайдеры в эмбед по категориям
        for auth_type in ProviderCategory:
            if auth_type in providers_by_auth:
                providers_text = "\n".join(providers_by_auth[auth_type])
                
                # Если текст слишком длинный, разбиваем на части
                while len(providers_text) > 1024:
                    # Находим последний полный провайдер до лимита
                    split_index = providers_text.rfind("\n", 0, 1024)
                    if split_index == -1:
                        split_index = 1024
                    
                    current_embed.add_field(
                        name=f"📁 {auth_type.value}",
                        value=providers_text[:split_index],
                        inline=False
                    )
                    providers_text = providers_text[split_index:].strip()
                    field_count += 1
                    
                    # Если достигли лимита полей или это последняя часть
                    if field_count >= 25 or len(providers_text) == 0:
                        embeds.append(current_embed)
                        embed_count += 1
                        current_embed=Embed(
                            title=f"{self.AI_EMOJI} Доступные провайдеры ИИ (Часть {embed_count})",
                            color=0x2b2d31
                        )
                        field_count = 0
                
                # Добавляем оставшийся текст
                if providers_text:
                    current_embed.add_field(
                        name=f"📁 {auth_type.value}",
                        value=providers_text,
                        inline=False
                    )
                    field_count += 1
                    
                    # Если достигли лимита полей
                    if field_count >= 25:
                        embeds.append(current_embed)
                        embed_count += 1
                        current_embed=Embed(
                            title=f"{self.AI_EMOJI} Доступные провайдеры ИИ (Часть {embed_count})",
                            color=0x2b2d31
                        )
                        field_count = 0
        
        # Добавляем последний эмбед, если он не пустой
        if field_count > 0:
            embeds.append(current_embed)
        
        # Добавляем футер к последнему эмбеду
        if embeds:
            embeds[-1].set_footer(text="🟢 - Последний использованный | ⚪ - Доступный")
        
        # Отправляем все эмбеды
        for i, embed in enumerate(embeds):
            if i == 0:
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.followup.send(embed=embed)

    @ai_group.command(name="info", description="Показать информацию о конкретном провайдере")
    @app_commands.describe(provider="Имя провайдера")
    async def provider_info(self, interaction: discord.Interaction, provider: str):
        """Показывает детальную информацию о провайдере"""
        # Ищем провайдера по имени
        found_provider = None
        for p, info in self.provider_info.items():
            if info["name"].lower() == provider.lower():
                found_provider = (p, info)
                break
        
        if not found_provider:
            await interaction.response.send_message(
                embed=Embed(
                    title=f"{Emojis.ERROR} Ошибка",
                    description=f"Провайдер '{provider}' не найден",
                    color=0xe74c3c
                ),
                ephemeral=True
            )
            return
        
        provider_class, info = found_provider
        embed=Embed(
            title=f"{self.AI_EMOJI} Информация о провайдере {info['name']}",
            color=0x2b2d31
        )
        
        embed.add_field(
            name="🔑 Тип авторизации",
            value=info["auth"].value,
            inline=False
        )
        
        embed.add_field(
            name="📚 Доступные модели",
            value="\n".join([f"• {model}" for model in info["models"]]),
            inline=False
        )
        
        embed.add_field(
            name="⭐ Модель по умолчанию",
            value=f"`{info['default_model']}`",
            inline=False
        )
        
        if provider_class == self.last_used_provider:
            embed.add_field(
                name="📊 Статус",
                value="🟢 Последний использованный провайдер",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(AI(bot)) 