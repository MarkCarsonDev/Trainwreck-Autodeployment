import time
import aiohttp
from bs4 import BeautifulSoup
import discord
from discord.ext import commands
from dotenv import dotenv_values
import importlib
import asyncio
from datetime import datetime
import os
import json
import re
from scheduler import start_scheduler

# Load configuration from .env file 
config = dotenv_values("../.locomotion-env")
from scheduler import start_scheduler

intents = discord.Intents.default()
intents.message_content = True

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
    # await bot.change_presence(activity=discord.Game(name="ray is so super sexyyyyyy ahahaaaa"))

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

    from modules.hunter_pictures import setup as hunter_pictures_setup
    await hunter_pictures_setup(bot)

    # Start the scheduler
    start_scheduler()

bot.run(TOKEN)
