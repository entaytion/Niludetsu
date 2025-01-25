# Niludetsu - Your Ultimate Discord Companion 🌟

## ✨ Key Features

- 🎵 **Advanced Music System**
  - High-quality music playback
  - Support for multiple platforms
  - Queue management and playlist features
  
- 🛠️ **Powerful Moderation Tools**
  - Comprehensive logging system
  - Auto-moderation capabilities
  - Advanced user management
  
- 🎨 **Creative Tools**
  - Image manipulation and generation
  - QR code creation
  - Custom welcome cards
  
- 🌍 **Global Accessibility**
  - Multi-language support
  - Real-time translation
  - Timezone management
  
- 🤖 **AI Integration**
  - Smart conversation capabilities
  - Text generation
  - Context-aware responses

## 🚀 Installation Guide

### Prerequisites
- Python 3.8 or higher
- Git
- Discord Bot Token
- Required API Keys

### Step-by-Step Setup

1. **Create Your Discord Bot**
   ```bash
   # Visit Discord Developer Portal
   → https://discord.com/developers/applications
   # Create New Application → Bot → Copy Token
   ```

2. **Clone & Setup**
   ```bash
   # Get the code
   git clone https://github.com/yourusername/niludetsu.git
   cd niludetsu
   
   # Create virtual environment (recommended)
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Configure**
   Create `config.json` in the root directory:
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
    "MOD_ROLE_ID": "ID",
    "VOICE_CHANNEL_ID": "ID",
    "VOICE_CHAT_ID": "ID", 
    "MESSAGE_VOICE_CHAT_ID": "ID"
   }
   ```

4. **Launch**
   ```bash
   python main.py
   ```

## 🛠️ Technology Stack

- **discord.py** - Robust Discord API integration
- **wavelink** - Professional audio streaming
- **PIL/Pillow** - Advanced image processing
- **deep_translator** - Seamless language translation
- **aiohttp** - Efficient async HTTP requests
- **transliterate** - Text transliteration
- **qrcode** - QR code generation
- **humanize** - Human-friendly data formatting
- **psutil** - System monitoring
- **pytz** - Global timezone support
- **g4f** - AI-powered interactions
- **easy_pil** - Streamlined image creation

## 💫 Why Choose Niludetsu?

- 🔧 **Reliable Performance**: Built with efficiency and stability in mind
- 🎯 **Feature-Rich**: Comprehensive toolset for all your server needs
- 🔒 **Secure**: Implements best practices for bot security
- 📈 **Scalable**: Handles growing communities with ease
- 🤝 **Community-Driven**: Regular updates based on user feedback
