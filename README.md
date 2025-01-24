# Niludetsu - Discord Bot

## 🚀 Quick Start Guide

1. **Bot Setup**
   - Create a new application at [Discord Developer Portal](https://discord.com/developers/applications)
   - Navigate to the "Bot" section and create a bot
   - Copy your bot token
   - Enable required Privileged Gateway Intents

2. **Configuration**
   - Create a `config.json` file in the root directory:
   ```json
   {
    "TOKEN": "YOUR_BOT_TOKEN_HERE",
    "WEATHER_API_KEY": "YOUR_WEATHER_API_KEY_HERE", 
    "DETECT_LANG_API_KEY": "YOUR_DETECT_LANG_API_KEY_HERE",
    "LAVALINK": {
        "host": "localhost",
        "port": 2333,
        "password": "youshallnotpass",
        "region": "europe"
    },
    "LOG_CHANNEL_ID": "ID",
    "MOD_ROLE_ID": "ID"
   }
   ```

3. **Installation**
   ```bash
   # Clone the repository
   git clone https://github.com/yourusername/niludetsu.git
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Run the bot
   python main.py
   ```

## 📚 Used Libraries

- **discord.py** - Main library for working with Discord API
- **wavelink** - Library for music and audio handling
- **PIL** - For image processing and manipulation
- **deep_translator** - For text translation
- **aiohttp** - For making HTTP requests
- **transliterate** - For transliteration
- **sqlite3** - For database handling
- **qrcode** - For generating QR codes
- **requests** - For making HTTP requests
