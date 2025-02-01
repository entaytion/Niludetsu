# Niludetsu - Advanced Discord Management Bot 🌟

## ✨ Key Features

- 🎵 **Music System**
  - High-quality music playback via Wavelink
  - Queue management and playlist features
  - Bitrate control and voice channel settings
  
- 🛠️ **Advanced Moderation**
  - Multi-level staff system (Admin, Moderator, Helper roles)
  - Command cooldown management
  - Comprehensive logging system
  
- 🎨 **Creative Tools**
  - Image manipulation with Pillow/easy_pil
  - QR code generation
  - Custom status indicators and emojis
  
- 🌍 **Internationalization**
  - Translation support via deep_translator
  - Transliteration capabilities
  - Multi-language interface
  
- 🤖 **AI Features**
  - AI-powered interactions using g4f
  - Smart responses
  - Context-aware commands

## 🚀 Installation Guide

### Prerequisites
- Python 3.11 or higher
- Git
- Discord Bot Token
- Required API Keys

### Step-by-Step Setup

1. **Clone & Setup**
   ```bash
   git clone https://github.com/yourusername/niludetsu.git
   cd niludetsu
   
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   Create `.env` file in the root directory with your configuration settings.
   
3. **Configure YAML**
   Create `data/config.yaml` for role configurations and other settings.

4. **Launch**
   ```bash
   python main.py
   ```

## 🛠️ Technology Stack

- **discord.py 2.4.0** - Core Discord API framework
- **wavelink 3.4.1** - Music streaming functionality
- **easy_pil 0.4.0** - Image creation and manipulation
- **Pillow 11.1.0** - Advanced image processing
- **deep_translator 1.11.4** - Language translation services
- **aiohttp 3.11.11** - Async HTTP client/server
- **transliterate 1.10.2** - Text transliteration
- **qrcode 8.0** - QR code generation
- **humanize 4.11.0** - Human-readable timestamps
- **psutil 6.1.1** - System resource monitoring
- **pytz 2024.2** - Timezone handling
- **g4f 0.4.2.4** - AI integration
- **mcstatus 11.1.1** - Minecraft server status checking
- **python_whois 0.9.5** - Domain information lookup

## 💫 Features & Benefits

- 🔧 **Role-Based Permissions**: Hierarchical staff system with Admin, Moderator, and Helper roles
- 🎯 **Custom Emojis**: Rich set of custom status and action emojis
- 🔒 **Secure Command System**: Built-in cooldown and permission management
- 📈 **Efficient Resource Usage**: Asynchronous operation for optimal performance
- 🤝 **Extensible Design**: Modular architecture for easy feature additions
