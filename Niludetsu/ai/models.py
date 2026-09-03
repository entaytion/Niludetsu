from __future__ import annotations
from ..logging import logger

import asyncio
import base64
import os
import random
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import aiohttp
from duckduckgo_search import DDGS
from google import genai
from google.genai import types

from .prompts import NILU_SYSTEM_PROMPT, WELCOME_QUESTION_PROMPT

HISTORY_LIMIT = 200
LONG_REQUEST_THRESHOLD = 100
GEMINI_TIMEOUT = 45.0
GEMINI_CHAT_MODEL = "gemini-3.1-flash-lite-preview"
MISTRAL_SMALL_MODEL = "mistral-small-latest"

IMAGE_MODEL_CHOICES: tuple[tuple[str, str], ...] = (
    ("Puter GPT Image 1.5 (Дефолт)", "gpt-image-1.5"),
    ("FLUX.1 Schnell (Высокое качество)", "togetherai:black-forest-labs/FLUX.1-schnell"),
    ("Stable Diffusion XL 1.0", "togetherai:stabilityai/stable-diffusion-xl-base-1.0"),
    ("Gemini 3.1 Flash Image (Экспериментально)", "openrouter:google/gemini-3.1-flash-image-preview"),
    ("GPT-5 Image Mini", "openrouter:openai/gpt-5-image"),
    ("Gemini 2.5 Flash Image", "openrouter:google/gemini-2.5-flash-image"),
)
IMAGE_MODEL_VALUES: tuple[str, ...] = tuple(value for _, value in IMAGE_MODEL_CHOICES)
PUTER_IMAGE_API_URL = "https://api.puter.com/drivers/call"

WELCOME_FALLBACK_QUESTIONS: tuple[str, ...] = (
    "какую привычку ты считаешь своей самой полезной?",
    "если бы у тебя было лишних 2 часа в день, на что бы ты их тратил?",
    "как выглядел бы твой идеальный выходной?",
    "какой навык ты хотел бы выучить в этом месяце?",
    "что приносит тебе ощущение спокойствия?",
    "в каком вымышленном мире ты хотел бы пожить день?",
    "какое маленькое достижение сегодня тобой гордится?",
)

class AiohttpSessionMixin:

    def _init_session(self, session: Optional[aiohttp.ClientSession] = None) -> None:
        self._session = session
        self._owns_session = False

    def bind_session(self, session: Optional[aiohttp.ClientSession]) -> None:
        self._session = session
        self._owns_session = False

    async def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
            self._owns_session = True
        return self._session

    async def close(self) -> None:
        if self._owns_session and self._session and not self._session.closed:
            await self._session.close()

class WelcomeQuestionGenerator(AiohttpSessionMixin):
    def __init__(
        self,
        session: Optional[aiohttp.ClientSession] = None,
        *,
        api_key: Optional[str] = None,
    ) -> None:
        self._init_session(session)
        self.api_key = api_key if api_key is not None else os.getenv("MISTRAL_API_KEY")
        self.api_url = "https://api.mistral.ai/v1/chat/completions"
        self.model_name = MISTRAL_SMALL_MODEL

    async def generate(self) -> str:
        if not self.api_key:
            return random.choice(WELCOME_FALLBACK_QUESTIONS)

        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": WELCOME_QUESTION_PROMPT}],
            "temperature": 0.8,
            "max_tokens": 60,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            session = await self._ensure_session()
            async with session.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status != 200:
                    return random.choice(WELCOME_FALLBACK_QUESTIONS)

                result = await response.json()
                question = result["choices"][0]["message"]["content"].strip()
                if question.startswith('"') and question.endswith('"'):
                    question = question[1:-1]
                if not question.endswith("?"):
                    question += "?"
                return question
        except Exception as exc:
            logger.warning(f"QuestionGenerator failed: {exc}")
            return random.choice(WELCOME_FALLBACK_QUESTIONS)

@dataclass(slots=True)
class GeneratedImageResult:
    data: bytes
    model: str
    content_type: str

class PuterImageService(AiohttpSessionMixin):
    def __init__(self, session: Optional[aiohttp.ClientSession] = None) -> None:
        self._init_session(session)

    async def generate(
        self,
        *,
        prompt: str,
        token: str,
        preferred_model: Optional[str] = None,
    ) -> tuple[Optional[GeneratedImageResult], str]:
        models_to_try = [preferred_model] if preferred_model else []
        models_to_try.extend(IMAGE_MODEL_VALUES)

        selected_models: list[str] = []
        seen: set[str] = set()
        for model_name in models_to_try:
            if model_name and model_name not in seen:
                selected_models.append(model_name)
                seen.add(model_name)

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "PuterGenAI/3.5.0",
            "Origin": "https://puter.com",
            "Referer": "https://puter.com/",
        }

        session = await self._ensure_session()
        last_error = "Не удалось получить данные от всех моделей"

        for current_model in selected_models:
            try:
                payload = {
                    "interface": "puter-image-generation",
                    "driver": "ai-image",
                    "method": "generate",
                    "args": {
                        "prompt": prompt,
                        "model": current_model,
                        "testMode": False,
                    },
                }
                async with session.post(
                    PUTER_IMAGE_API_URL,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        if not image_data or len(image_data) < 500:
                            last_error = (
                                f"Модель {current_model} вернула пустой результат "
                                "(вероятно, промпт заблокирован)"
                            )
                            continue

                        content_type = response.headers.get(
                            "Content-Type",
                            "image/png",
                        )
                        return (
                            GeneratedImageResult(
                                data=image_data,
                                model=current_model,
                                content_type=content_type,
                            ),
                            last_error,
                        )

                    try:
                        error_message = await response.text()
                        last_error = (
                            f"Model {current_model} failed "
                            f"(Status {response.status}): {error_message[:100]}"
                        )
                    except Exception:
                        last_error = (
                            f"Model {current_model} failed "
                            f"(Status {response.status})"
                        )
                    logger.warning(last_error)
            except Exception as exc:
                last_error = f"Исключение при вызове {current_model}: {exc}"
                logger.error(last_error)

        return None, last_error

class GeminiChatService(AiohttpSessionMixin):
    SEARCH_KEYWORDS = (
        "погугли",
        "найди",
        "новости",
        "что нового",
        "кто такой",
        "как там",
        "инфо",
        "поиск",
        "курс",
        "поищи",
        "изучи",
        "узнай",
    )

    def __init__(self, session: Optional[aiohttp.ClientSession] = None) -> None:
        self.api_keys = {
            "primary": os.getenv("GEMINI_API_KEY"),
            "secondary": os.getenv("2GEMINI_API_KEY"),
        }
        self.model_name = GEMINI_CHAT_MODEL
        self.client: Optional[genai.Client] = None
        self._configure_client(self.api_keys["primary"])
        self._init_session(session)

    def _configure_client(self, api_key: Optional[str]) -> None:
        if not api_key:
            self.client = None
            return
        self.client = genai.Client(api_key=api_key)

    async def _web_search(self, query: str) -> str:
        try:
            clean_query = re.sub(
                r"^(погугли|найди|новости|поиск|что там по|инфо)\s*",
                "",
                query,
                flags=re.I,
            ).strip()
            if not clean_query:
                clean_query = query

            logger.info(f"Searching Web for: {clean_query}")

            def do_search() -> str:
                with DDGS() as ddgs:
                    results = ddgs.text(clean_query, max_results=5, timelimit="m")
                    if not results:
                        return "Ничего не найдено по этому запросу."
                    return "\n".join(
                        f"- {item['title']} ({item['body']})"
                        for item in results
                    )

            return await asyncio.to_thread(do_search)
        except Exception as exc:
            logger.error(f"Search error: {exc}")
            return f"Ошибка при поиске: {exc}"

    def _build_system_prompt(self, search_context: str = "") -> str:
        current_date_str = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        current_system = (
            NILU_SYSTEM_PROMPT
            + f"\n\nТЕКУЩЕЕ ВРЕМЯ И ДАТА: {current_date_str}\n"
        )
        if search_context:
            current_system += (
                f"\n[ДАННЫЕ ИЗ ИНТЕРНЕТА]:\n{search_context}\n\n"
                "Обязательно используй эти данные в ответе, если они актуальны."
            )
        return current_system

    async def _fetch_image_as_base64(self, image_url: str) -> types.Part:
        session = await self._ensure_session()
        async with session.get(image_url) as response:
            if response.status != 200:
                raise RuntimeError(f"Не удалось загрузить изображение: {response.status}")

            image_data = await response.read()
            image_base64 = base64.b64encode(image_data).decode("utf-8")
            return types.Part(
                inline_data=types.Blob(
                    mime_type="image/jpeg",
                    data=image_base64,
                )
            )

    async def generate_response(
        self,
        prompt: str,
        image_url: Optional[str],
        user_history: list[dict[str, str]],
    ) -> tuple[str, bool]:
        contents: list[types.Content] = []
        need_search = any(word in prompt.lower() for word in self.SEARCH_KEYWORDS)
        search_context = await self._web_search(prompt) if need_search else ""
        current_system = self._build_system_prompt(search_context)

        for msg in user_history:
            api_role = "user" if msg["role"] == "user" else "model"
            contents.append(
                types.Content(
                    role=api_role,
                    parts=[types.Part(text=msg["content"])],
                )
            )

        current_parts: list[types.Part] = [types.Part(text=prompt)]
        if image_url:
            current_parts.append(await self._fetch_image_as_base64(image_url))
        contents.append(types.Content(role="user", parts=current_parts))

        last_error: Optional[Exception] = None

        for key_label, api_key in self.api_keys.items():
            if not api_key:
                continue

            try:
                self._configure_client(api_key)
                if not self.client:
                    continue

                response = await asyncio.wait_for(
                    self.client.aio.models.generate_content(
                        model=self.model_name,
                        contents=contents,
                        config=types.GenerateContentConfig(
                            system_instruction=current_system,
                            temperature=0.7,
                            top_p=0.8,
                            top_k=40,
                        ),
                    ),
                    timeout=GEMINI_TIMEOUT,
                )
                return response.text, key_label == "secondary"
            except asyncio.TimeoutError:
                logger.warning(f"Gemini timeout ({key_label} key)")
                if key_label == "secondary":
                    return (
                        "⚠️ Запрос превысил лимит времени. Попробуйте сформулировать вопрос проще.",
                        False,
                    )
            except Exception as exc:
                last_error = exc
                logger.warning(f"Gemini key {key_label} failed: {exc}")

        self._configure_client(self.api_keys["primary"])
        if last_error:
            return self._handle_error(last_error), False
        return "⚠️ Не удалось выполнить запрос: ключи не настроены.", False

    def _handle_error(self, error: Exception) -> str:
        error_str = str(error)

        if "429" in error_str or "quota" in error_str.lower():
            logger.error(f"Quota exceeded: {error_str}")
            return "⚠️ Достигнут дневной лимит запросов к Gemini API (250/день). Попробуйте позже."

        if (
            "PROHIBITED_CONTENT" in error_str
            or "SAFETY" in error_str
            or "block_reason" in error_str
        ):
            logger.warning(f"Content blocked: {error_str}")
            return "⚠️ Ваш запрос был заблокирован системой безопасности. Попробуйте переформулировать."

        if (
            "response.text quick accessor requires" in error_str
            or "finish_reason" in error_str
        ):
            logger.warning(f"Empty response: {error_str}")
            return "⚠️ Не удалось сгенерировать ответ. Попробуйте переформулировать запрос."

        if "403" in error_str or "ACCESS_TOKEN_SCOPE_INSUFFICIENT" in error_str:
            logger.error(f"Auth error: {error_str}")
            return "⚠️ Ошибка доступа к API. Обратитесь к администратору."

        if "400" in error_str and "image" in error_str.lower():
            logger.warning(f"Invalid image: {error_str}")
            return "⚠️ Не удалось обработать изображение. Попробуйте другой формат (PNG/JPG)."

        logger.error(f"Gemini API error [{type(error).__name__}]: {error_str}")
        return "⚠️ Произошла техническая ошибка. Администратор уведомлён."
