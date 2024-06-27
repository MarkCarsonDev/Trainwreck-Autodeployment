# locomotion.py

import time
import aiohttp
from bs4 import BeautifulSoup
import discord
from discord.ext import commands
from dotenv import dotenv_values
import asyncio
from datetime import datetime
import os
import json
import re
from scheduler import start_scheduler
import importlib

# Load configuration from .env file 
config = dotenv_values("../.locomotion-env")

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True  # Ensure reaction intents are enabled

# Discord bot token and target user ID
TOKEN = config["DISCORD_TOKEN"]
TARGET_USER_ID = int(config["TARGET_USER_ID"])

bot = commands.Bot(command_prefix='!', intents=intents, activity=discord.Activity(type=discord.ActivityType.watching, name="github.com/MarkCarsonDev/Trainwreck-Autodeployment"))

async def send_message(user_id: int, message=None):
    """
    Sends a message to a specified user on Discord.

    Args:
        user_id (int): The Discord user ID to whom the message will be sent.
        message (str, optional): The content of the message. Defaults to a generic message.
    """
    user = await bot.fetch_user(user_id)
    message = message or "This was an attempt to send an unspecified message."
    await user.send(message)

@bot.event
async def on_ready():
    """
    Called when the bot is ready. Sets up the monitoring task.
    """
    print(f'{bot.user} is now running')
    await send_message(TARGET_USER_ID, "Bot has been started.")

@bot.event
async def setup_hook():
    """
    Asynchronous setup hook for the bot.
    """
    modules_dir = os.path.join(os.path.dirname(__file__), 'modules')
    for filename in os.listdir(modules_dir):
        if filename.endswith('.py') and not filename.startswith('__'):
            module_name = filename[:-3]  # Strip .py extension
            module_path = f'modules.{module_name}'
            module = importlib.import_module(module_path)
            if hasattr(module, 'setup'):
                module.setup(bot)

    # Start the scheduler
    start_scheduler()

@bot.event
async def on_reaction_add(reaction, user):
    """
    Event listener for reactions added to messages.
    """
    if user.bot:
        return

    if str(reaction.emoji) == '❌':
        message = reaction.message
        with open('../hunter_pic_blacklist.json', 'r+') as file:
            try:
                blacklist = json.load(file)
            except json.JSONDecodeError:
                blacklist = []

            if message.content not in blacklist:
                blacklist.append(message.content)
                file.seek(0)
                json.dump(blacklist, file)

        channel = bot.get_channel(HUNTER_PICS_CHANNEL)
        media_links = await get_media_links(channel)
        if not media_links:
            await message.edit(content="No more available media.")
        else:
            new_media = random.choice(media_links)
            await message.edit(content=new_media)
        await reaction.remove(user)

bot.run(TOKEN)
