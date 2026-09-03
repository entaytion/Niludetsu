# Niludetsu — Agent Guide

Discord bot (v2.1.2) for the nullther server, written entirely in Python 3.13 with discord.py 2.7+. Also runs a FastAPI web dashboard (Jinja2 templates) for guild settings and locale customization.

## Quick Start

```bash
uv sync            # Install deps (uses uv, not pip)
uv run main.py     # Run bot + dashboard together (merged process)
```

## Architecture

### Entry Point
- **`main.py`** — `NiludetsuBot(commands.Bot)` subclass. `setup_hook()` initializes: database pool, settings cache, ConfigManager, AccessGuard, ModerationManager, Loader, QuestTracker, LevelTracker, then spawns FastAPI (`uvicorn.Server`) as `asyncio.create_task`.
- **`web/run.py`** — standalone web-only launcher (`uvicorn.run("app:app", reload=True)`).

### Project Structure

```
Niludetsu/               # Core library package
  __init__.py             # Re-exports all managers, tools, config
  config.py               # _ConfigProxy — reads from DB (settings cache), falls back to hardcoded _DEFAULTS
  config_manager.py       # ConfigManager — premium guilds + custom messages cache; 60s sync loop
  settings.py             # Settings — DB-backed key-value config with TTL cache (300s)
  locale.py               # _(ctx=ctx) → t(module, key, **kwargs) localization; DEFAULT_LOCALE dict
  logging.py              # loguru config — WARNING+ to stderr, intercepts stdlib logging
  database/
    __init__.py           # Exports Database instance + class
    database.py           # Database class (mixin-based, ~15 tables via CRUD mixins)
    models.py             # TypedDicts: UserBundle, UserEconomyRow, UserProfileRow, etc.
    pool.py               # NeonPool — asyncpg pool with retry logic (3 retries, exp backoff)
    query.py              # QueryBuilder — fluent SELECT builder
    errors.py             # DatabaseConnectionError, RetryExhaustedError
    mixins/
      base.py             # CRUD: get_row, get_rows, insert, upsert, update_record, delete
      economy.py          # EconomyMixin: update_economy, inventory, transactions
      social.py           # Marriage, adoption queries
      analytics.py        # AnalyticsMixin: message/voice stats upserts
      quests.py           # QuestsMixin: quest progress tracking
      shop.py             # ShopMixin: purchases
  economy/
    manager.py            # EconomyManager — balances, work, daily, rob, etc.
    checks.py             # Permission/cooldown checks for economy commands
    validators.py         # Amount validation
  moderation/
    manager.py            # ModerationManager — warn/mute/ban CRUD + auto-expire timer
    checks.py             # check_moderation_target, @moderationcommand decorator
    config.py             # ActionType enum
    embed.py              # moderationembed() — embed factory for moderation actions
    exceptions.py         # ModerationError
    system/               # Moderation sub-modules
    automod/              # AutoModManager, rules engine
  levels/
    manager.py            # LevelManager — XP awards, level-up logic
    tracker.py            # LevelTracker — voice/message XP accumulation
    image.py              # Rank card image generation
  quests/
    definitions.py        # Quest definitions/templates
    manager.py            # QuestManager
    tracker.py            # QuestTracker — listens for events, progresses quests
  marriage/
    marriage_manager.py   # MarriageManager
    adoption_manager.py   # AdoptionManager
  achievements/
    config.py             # Achievement definitions
    manager.py            # AchievementsManager
  analytics/
    manager.py            # AnalyticsManager
    repository.py         # DB queries for analytics
    tracker.py            # AnalyticsTracker — records messages, voice time
  giveaways/
    giveaway_manager.py   # GiveawayManager
    repository.py         # DB CRUD for giveaways
    conditions.py         # Entry requirement checks
    ui.py                 # Discord UI views for giveaways
  temprooms/
    service.py            # TempRoomService — voice channel lifecycle
    repository.py         # DB CRUD
    cache.py              # In-memory cache
    views.py              # UI for temp room controls
  ai/
    __init__.py            # Exports GeminiChatService, PuterImageService, WelcomeQuestionGenerator
    models.py              # AI service clients (Gemini, Mistral, Puter image gen)
    prompts.py             # System prompts (nilu, welcome questions)
  image/
    core.py               # Image manipulation helpers (Pillow)
  profile/
    image.py              # Profile card image generation
  webhooks/
    base.py               # Webhook audit logging infrastructure
    ... (20+ webhook modules)  # Per-event webhook loggers (member join/leave, messages, voice, etc.)
  tools/
    AccessControl.py      # AccessGuard — guild whitelist + per-cog toggle check
    Discord.py            # resolve_member, safe_edit, safe_delete, safe_fetch_message, etc.
    Embed.py              # Custom Embed subclass (extends discord.Embed) with factory methods
    Emojis.py             # Custom emoji constants (<:aeXXX:123...>)
    Errors.py             # ErrorHandler — hierarchical error reporting to bug channel
    GameView.py           # Generic game view base class
    Loader.py             # Extension auto-discover + slash sync engine
    Patterns.py           # PatternChecker — regex utilities
    SendHybrid.py         # send(), defer(), send_moderation() — unified prefix+slash output
    Time.py               # TimeService — pendulum-based time parsing + formatting
    Validator.py          # Input validation helpers
  embeds/
    Economy.py            # EconomyEmbed factory
    Achievements.py       # AchievementEmbed factory
  api/                    # External API wrappers (ASCII, Color, Currency, EightBall, Gifs, Hash, LGBT, MCServer, Math, QRCode, Random, Screenshot, Translate, Translit, Weather, Whois)
  development/
    Webhooks.py           # Webhook audit logger
  Exceptions.py           # Custom exceptions

commands/                 # Auto-discovered command cogs (organized by category)
  main/                   # Core commands (help, say, staff, panel, logger, event, pm)
  economy/                # Economy commands (17 files)
  moderation/             # Moderation commands (13 files)
  profile/                # Profile commands (7 files)
  fun/                    # Fun commands (4 files)
  marriage/               # Marriage commands (2 files)
  partnership/            # Partnership commands (4 files)
  system/                 # System/admin commands (6 files)
  utilities/              # Utility commands (6 files)
  tools/                  # Tool commands (5 files)
  customization/          # Customization cogs (Banner, Form, Structure, Views)

web/                      # FastAPI dashboard
  __init__.py
  app.py                  # FastAPI app — mounts routers, serves Jinja2 templates
  auth.py                 # Discord OAuth2 + JWT session management
  bot.py                  # Bridge module — holds singleton reference to bot instance
  config.py               # Web config (client ID, JWT secret, host/port)
  database.py             # WebDatabase proxy — writes through to ConfigManager cache
  migrations.sql          # SQL for premium_guilds table
  run.py                  # Standalone web launcher (uvicorn reload)
  routes/
    __init__.py
    auth.py               # /auth/login, /auth/callback, /auth/logout
    dashboard.py          # /dashboard, /dashboard/guild/{id}
    locale.py             # /dashboard/guild/{id}/locale — locale override editor
  templates/
    base.html             # Base template
    dashboard.html        # Guild list
    guild.html            # Per-guild settings
    locale.html           # Locale editor
    index.html            # Landing page
    me.html               # User profile
  static/js/              # Frontend JS

data/
  fonts/                  # TTF fonts for image generation
  images/                 # Static images (banners, profile templates)
  conversations/          # AI conversation history storage (JSON)
```

### Control Flow

```
bot startup → setup_hook() →
  database (asyncpg pool) → settings.load() (DB → Settings._cache) →
  ConfigManager.load_all() (custom_messages + premium_guilds) →
  AccessGuard.bootstrap() (leave unwhitelisted guilds) →
  Loader.load_everything() (discovers commands/* + cogs/*, loads as extensions, syncs slash) →
  QuestTracker/LevelTracker init →
  FastAPI server asyncio task →
```

### Key Patterns

- **Cog structure**: Each command file in `commands/` or `cogs/` is a standard discord.py `commands.Cog` subclass, with `async def setup(bot)` at module level.
- **Hybrid commands**: Most commands use `@commands.hybrid_command(name=..., description=...)` + optional `@app_commands.describe()` for dual prefix/slash support.
- **Localization**: `from Niludetsu.locale import _` then `t = _(ctx=ctx)` then `t("economy", "daily_success", user_mention=...)`. Guilds can override strings via the web dashboard (stored in `custom_messages` table, module="locale"), but only premium guilds can customize.
- **Embed factory**: `Niludetsu.Embed` extends `discord.Embed` with `.success()`, `.error()`, `.default()`, `.user_action()` class methods — pass keyword args, not raw dicts.
- **Send hybrid**: `from Niludetsu import send` — use instead of `ctx.send()` for transparency between prefix and slash commands.
- **Error handling**: `bot.on_command_error` ignores `CommandNotFound` and `UserInputError` (sends ephemeral), reports everything else to bug channel via Webhooks reporter. `_on_app_command_error` handles slash errors similarly.
- **Moderation decorator**: `@moderationcommand(required_level=3, cooldown=5)` on any moderation command handles permission checks, cooldowns, and hierarchy validation.
- **Access control**: `AccessGuard` checks `config.SERVERS["ALLOWED_ID"]` — bot auto-leaves servers not in the whitelist. Per-cog toggling via `ConfigManager.get_custom_text(guild_id, "cogs", cog_name, "enabled")`.
- **Database**: `Database` class uses mixin pattern (BaseMixin + domain mixins). `NeonPool` wraps asyncpg with retry logic. All queries go through `_neon.execute/fetch/fetchrow` (public methods on NeonPool). JSONB columns auto-serialize/deserialize via pool init.

### Database Schema

Tables live in `public` schema:

- `users` (user_id, guild_id, created_at)
- `user_economy` (balance, deposit, spousal_balance, spousal_enabled, cooldowns JSONB)
- `user_profile` (level, experience, reputation)
- `user_analytics` (messages_total, messages_deleted, voice_seconds, message_channels JSONB, voice_channels JSONB)
- `user_quests` (quest_key, progress, target, reward, quest_type, expires_at, claimed)
- `user_inventory` (item_type, item_key, quantity, metadata JSONB)
- `user_transactions` (event, amount, balance_after, related_user_id, metadata JSONB)
- `user_marriages` (partner_a_id, partner_b_id, status, metadata JSONB)
- `user_marriage_children` (marriage_id, user_id)
- `user_rudiments` (moderation punishments — action_type, reason, duration, expires_at, active)
- `user_achievements` (achievement_id, unlocked_at)
- `settings` (key, value — arbitrary config)
- `custom_messages` (guild_id, module, key, value JSONB — premium localization/customization)
- `premium_guilds` (guild_id, expires_at)
- `temprooms` (channel_id, owner_id, etc.)
- `partnership` / `partnermanager` (partner server management)
- `giveaway_participants` (giveaway_id, user_id)

## Gotchas & Non-Obvious

1. **Config is dynamic**: `from Niludetsu.config import PREFIX` goes through `_ConfigProxy.__getattr__` → checks `Settings._cache` (loaded from Neon at startup) → falls back to hardcoded `_DEFAULTS` dict. Setting config values at runtime must use `await settings.set("KEY", value)` — direct assignment only touches the in-memory cache, not the DB.
2. **Loader scans `commands/`**: All command cogs live organized by category in `commands/`. Each `.py` file (except `__init__.py` and `_`-prefixed) becomes a cog. The Loader also syncs slash commands to main guild and clears them from all others.
3. **Web app lives inside the bot process**: `main.py` starts FastAPI via `asyncio.create_task(self._run_web_server())` inside the same event loop. The `web/bot.py` bridge module provides `get_bot()` so web route handlers can access bot internals.
4. **`web/database.py` != `Niludetsu/database/database.py`**: `WebDatabase` is a proxy that writes through to ConfigManager (cache-aware). It's imported as `from ..database import db` in web routes — not to be confused with the main `database` instance from the core package.
5. **Premium guilds**: Not all guilds can use custom locale/messages. Check `is_premium` before allowing customization in commands.
6. **Emojis class**: All custom emoji constants use Discord's `<:aeName:ID>` format. The "ae" prefix is a branding artifact — these are the bot's own emoji.
7. **All strings in Russian**: Code comments, locale strings, and user-facing text are in Russian. The bot is built for a Russian-speaking community.
8. **`@moderationcommand` wrapper**: This isn't a standard discord.py check — it's a custom decorator defined in `Niludetsu/moderation/checks.py` that wraps handlers with hierarchy checks + cooldowns.
9. **AI image generation**: Uses Puter API (not Discord's). Multiple model fallbacks in `IMAGE_MODEL_CHOICES`. The `PuterImageService` tries models sequentially until one works.
10. **Polling loops**: ConfigManager reloads from DB every 60s (`_sync_loop`). Settings cache TTL is 300s. Status updates run every 300s.
11. **Merged Process**: `main.py` runs both Discord bot and FastAPI web dashboard together in the same event loop with zero port conflicts.
12. **Reaction data in JSON**: `commands/system/ReactionSystem.py` loads reactions from `data/reactions.json`. Edit that file to customize reaction texts; the duplicate `commands/fun/ReactionSystem.py` was deleted.
13. **Transaction queue**: `EconomyManager._schedule_transaction` pushes to a shared `asyncio.Queue` consumed by a single worker — not fire-and-forget tasks. This prevents task leaks under load.
14. **`_safe_col` / `_safe_table`**: `BaseMixin` validates all SQL identifiers against `^[a-z_][a-z0-9_]*$` before interpolation. Wrap new CRUD identifiers with these helpers.
15. **Loader slash-sync skip**: `sync_interactions()` hashes loaded module names and skips the Discord API round-trip if extensions haven't changed.
16. **Discord OAuth in web**: The web dashboard uses Discord OAuth2 with JWT sessions (24h expiry). Only server admins (permissions & 0x8 or owner) can access guild settings.

## Naming Conventions

- Files: PascalCase for command modules (`Balance.py`, `Help.py`), snake_case for library modules (`config_manager.py`, `locale.py`)
- Classes: PascalCase (`AccessGuard`, `EconomyManager`)
- Functions/methods: snake_case
- Variables: snake_case
- DB columns: snake_case
- Command names: lowercase, aliases in Russian as well (e.g., `aliases=("баланс", "b")`)
- Import style: `from Niludetsu import Embed, config` or `from Niludetsu.tools.SendHybrid import send`

## Testing

No test suite found. No pytest config, no test directory. Testing is manual.

## Deployment

- **Procfile**: `web: python main.py` (for Railway.app)
- **Platform**: Python 3.13, PostgreSQL (Neon), uv package manager
- **Env vars**: Required — `MAIN_TOKEN`, `DISCORD_CLIENT_ID`, `DATABASE_URL` (Neon Postgres with `?sslmode=require`), plus various API keys
- **.env.save**: Template for required env vars
