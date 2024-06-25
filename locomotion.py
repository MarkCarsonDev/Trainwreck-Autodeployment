import discord
import os
import json
import time
from datetime import datetime
from discord.ext import commands
from dotenv import dotenv_values
import asyncio

# Load configuration from .env file 
config = dotenv_values("../.locomotion-env")

intents = discord.Intents.default()
intents.message_content = True

# Discord bot token and target user ID
TOKEN = config["DISCORD_TOKEN"]
TARGET_USER_ID = int(config["TARGET_USER_ID"])

bot = commands.Bot(command_prefix='!', intents=intents)

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
    await bot.change_presence(activity=discord.Game(name="ray is so super sexyyyyyy ahahaaaa"))

# Load the roomfinder module
from modules.roomfinder import setup as roomfinder_setup
roomfinder_setup(bot)

# Load the github module
from modules.github import setup as github_setup
github_setup(bot)

bot.run(TOKEN)
