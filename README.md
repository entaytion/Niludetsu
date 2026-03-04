<div align="center">
  <a href="https://github.com/Entaytion/Niludetsu">
    <img src="https://cdn.discordapp.com/avatars/1264591814208262154/76e24f700481aa7e7531c25e5ad5448b.webp?size=1024" alt="Niludetsu Logo">
  </a>
  <h1>Niludetsu — ёбаное говно, но оно работает!</h1>
</div>

## 🌟 Нахуя оно надо?
Запихали сюда всё подряд, как в мусорку. Но оно ебашит:

- **🎵 Музыка** — чтобы хуярило в уши, пока ты играешь в какие-то игры.
- **🛡️ Модерация** — для того, чтобы мутить долбоёбов и банить неадекватов, ещё и с таймером.
- **📊 Экономика** — фарми бабки из воздуха, как настоящий мамкин криптоинвестор.
- **📈 Левлы** — меряйтесь письками, у кого больше экспы.
- **🎁 Розыгрыши** — раздавай всякую халявную залупу активным юзерам.
- **🔊 Войсы** — управление канальчиками, чтобы вас никто не подслушивал.
- **🔍 Аналитика** — смотри, сколько времени ты проёбываешь в дискорде.
- **💻 Утилиты** — базовые фичи просто шоб было для админов.

Большую часть этого кала я буду переписывать, потому что глаза вытекают из орбит.

## ⚙️ Как завести эту хуйню?
Во-первых, юзай **uv** (потому что стандартный pip — это для казуалов без уважения к своему времени):
```bash
uv venv
uv pip install -r requirements.txt # или uv sync, если юзаешь pyproject
```

Во-вторых, делаешь файл `.env` и пиздуешь туда эту залупу:

```env
# Токены бота - не проеби
MAIN_TOKEN=твой_дискорд_токен
DISCORD_CLIENT_ID=твой_client_id

# Ключи от АПИшек (ищи и регистрируй)
EXCHANGE_RATE_API_KEY=your_exchange_rate_api_key
LANGUAGE_DETECTION_API_KEY=your_language_detection_key
WEATHER_API_KEY=your_weather_api_key
E621_API_KEY=your_e621_api_key
GEMINI_API_KEY=your_gemini_api_key
MISTRAL_API_KEY=your_mistral_api_key
PASTEBIN_API_KEY=your_pastebin_api_key
ISTD_API_KEY=your_istd_api_key
SCREENSHOT_MACHINE_API_KEY=your_screenshot_machine_key

# Музон (Lavalink)
LAVALINK_HOST=localhost
LAVALINK_PORT=2333
LAVALINK_PASSWORD=youshallnotpass
LAVALINK_IDENTIFIER=MyLavalinkNode
LAVALINK_SECURE=false

# Supabase: База Данных
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
```

## 📜 Лицензия
GNU General Public License v3.0. Почитай `LICENSE`, если не впадлу.

---
### 🙏 Благодарочка:
- **Antigravity** — потому что Cursor мы уже слали нахуй, теперь тут рулит мой персональный украинский демон.
- **Vintro** — за помощь с корявой библиотекой discord.py