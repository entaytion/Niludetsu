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
       "TOKEN": "your-bot-token-here",
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