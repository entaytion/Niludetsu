<div align="center">
  <a href="https://github.com/Entaytion/Niludetsu">
    <img src="https://cdn.discordapp.com/avatars/1264591814208262154/76e24f700481aa7e7531c25e5ad5448b.webp?size=300" alt="Niludetsu Logo">
  </a>
  <h1>Niludetsu — Discord-бот з великими амбіціями</h1>
  <p><i>Зроблений на 100% за допомогою ШІ, тому що автор — бездар без жодного таланту до програмування.</i></p>
</div>

> [!WARNING]
> **Дисклеймер:** Цей бот написаний повністю штучним інтелектом. Автор ([@Entaytion](https://github.com/Entaytion)) не написав жодного рядка коду власноруч — він лише натискав кнопки та молився, щоб воно запрацювало. Будь-які баги — це фіча, а будь-які фічі — щасливий випадок.

## 🌟 Що воно вміє?

- **🛡️ Модерація** — мут, бан, таймери — все для підтримки порядку на сервері.
- **📊 Економіка** — віртуальна валюта, щоденні нагороди, пограбування та робота.
- **📈 Рівні** — система досвіду та прогресу для учасників серверу.
- **🎁 Розіграші** — організація гівевеїв з гнучкими умовами участі.
- **🔊 Голосові кімнати** — тимчасові приватні канали для спілкування.
- **🔍 Аналітика** — статистика активності: повідомлення, голос, канали.
- **💍 Шлюби** — система віртуальних шлюбів та усиновлення.
- **🏆 Досягнення** — система ачівок за активність на сервері.
- **🤖 ШІ-асистент** — інтеграція з Google Gemini для розмов та аналізу зображень.
- **💻 Утиліти** — корисні інструменти для адміністрування.

## ⚙️ Встановлення

Використовуємо **uv** для керування залежностями:
```bash
uv sync
uv run main.py
```

Створіть файл `.env` та заповніть його:

```env
# Токен бота
MAIN_TOKEN=your_discord_token
DISCORD_CLIENT_ID=your_client_id

# API-ключі
EXCHANGE_RATE_API_KEY=your_exchange_rate_api_key
LANGUAGE_DETECTION_API_KEY=your_language_detection_key
WEATHER_API_KEY=your_weather_api_key
E621_API_KEY=your_e621_api_key
GEMINI_API_KEY=your_gemini_api_key
MISTRAL_API_KEY=your_mistral_api_key
PASTEBIN_API_KEY=your_pastebin_api_key
ISTD_API_KEY=your_istd_api_key
SCREENSHOT_MACHINE_API_KEY=your_screenshot_machine_key

# Neon Postgres
DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require
```

## 📜 Ліцензія
GNU General Public License v3.0 — деталі у файлі `LICENSE`.

---
### 🙏 Подяки:
- **Antigravity, Codex, Gemini CLI, Bonsai** — ШІ-асистенти, які допомагали мені писати цей код, бо автор даун.
- **Vintro** — за допомогу з бібліотекою discord.py
- **Google Gemini** — за те, що не відмовився працювати посеред ночі