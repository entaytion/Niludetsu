import discord
from discord.ext import commands
import os
import importlib
import json

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="mrtv!", intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    print(f'Prefix is set to: {bot.command_prefix}')
    print("Syncing commands...")
    await bot.tree.sync()
    print("Commands synced successfully!")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
        
    if message.content.startswith('mrtv!'):
        print(f"Command detected: {message.content}")
        
    await bot.process_commands(message)

async def load_cogs():
    cog_directories = [
        "./cogs",
        "./cogs/utilities",
        "./cogs/economy", 
        "./cogs/fun",
        "./cogs/moderation"
    ]
    
    for directory in cog_directories:
        category = directory.split('/')[-1]
        for f in os.listdir(directory):
            if f.endswith(".py"):
                try:
                    module = importlib.import_module(f"{directory[2:].replace('/', '.')}.{f[:-3]}")
                    if hasattr(module, 'setup'):
                        await module.setup(bot)
                    print(f"Loaded {category}: {f[:-3]}")
                except Exception as e:
                    print(f"Failed to load {category} {f[:-3]}: {e}")

with open('config/config.json', 'r') as f:
    config = json.load(f)
    TOKEN = config['TOKEN'] 

async def create_default_files():
    if not os.path.exists('config'):
        os.makedirs('config')
        
    if not os.path.exists('config/database.db'):
        open('config/database.db', 'w').close()
                
    if not os.path.exists('config/config.json'):
        default_config = {
            "TOKEN": "YOUR_BOT_TOKEN_HERE",
            "LAVALINK": {
            "host": "localhost",
            "port": 2333, 
            "password": "youshallnotpass",
            "region": "europe"
            }
        }
        with open('config/config.json', 'w') as f:
            json.dump(default_config, f, indent=4)

async def main():
    await create_default_files()
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)

import asyncio
asyncio.run(main())