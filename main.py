import discord
from discord.ext import commands
import os
import importlib
from config import TOKEN
import json

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="mrtv!", intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    print(f'Prefix is set to: {bot.command_prefix}')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
        
    if message.content.startswith('mrtv!'):
        print(f"Command detected: {message.content}")
        
    await bot.process_commands(message)

async def load_cogs():
    for f in os.listdir("./cogs"):
        if f.endswith(".py"):
            try:
                module = importlib.import_module(f"cogs.{f[:-3]}")
                if hasattr(module, 'setup'):
                    await module.setup(bot)
                print(f"Loaded: {f[:-3]}")
            except Exception as e:
                print(f"Failed to load {f[:-3]}: {e}")

    try:
        levels = importlib.import_module("levels")
        if hasattr(levels, 'setup'):
            await levels.setup(bot)
        print("Loaded: levels")
    except Exception as e:
        print(f"Failed to load levels: {e}")

    try:
        music = importlib.import_module("music")
        if hasattr(music, 'setup'):
            await music.setup(bot)
        print("Loaded: music")
    except Exception as e:
        print(f"Failed to load music: {e}")

async def create_default_files():
    if not os.path.exists('config'):
        os.makedirs('config')
        
    if not os.path.exists('config/roles.db'):
        open('config/roles.db', 'w').close()
        
    if not os.path.exists('config/users.db'):
        open('config/users.db', 'w').close()
        
    if not os.path.exists('config.json'):
        with open('config.json', 'w') as f:
            json.dump({"TOKEN": "YOUR_BOT_TOKEN_HERE"}, f, indent=4)
            
    if not os.path.exists('lavalink_config.json'):
        default_config = {
            "host": "localhost",
            "port": 2333,
            "password": "youshallnotpass",
            "region": "europe"
        }
        with open('lavalink_config.json', 'w') as f:
            json.dump(default_config, f, indent=4)

async def main():
    await create_default_files()
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)

import asyncio
asyncio.run(main())