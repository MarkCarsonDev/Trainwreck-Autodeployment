import discord
from discord.ext import commands
from dotenv import dotenv_values
import asyncio
import os

# Load configuration from .env file 
config = dotenv_values("../.locomotion-env")

intents = discord.Intents.default()
intents.message_content = True

# Discord bot token and target user ID
TOKEN = config["DISCORD_TOKEN"]
TARGET_USER_ID = int(config["TARGET_USER_ID"])

class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def setup_hook(self):
        # Load the example module
        from modules.example_module import setup as example_module_setup
        example_module_setup(self)

        # Load the roomfinder module
        from modules.roomfinder import setup as roomfinder_setup
        roomfinder_setup(self)

        # Load the github module
        from modules.github import setup as github_setup
        github_setup(self)

        # Load the github_schedule module
        from modules.github_shamer import setup as github_schedule_setup
        github_schedule_setup(self)

        # Load the user manager module
        from modules.user_manager import setup as user_manager_setup
        user_manager_setup(self)

        # Load the hunter_pictures module
        from modules.hunter_pictures import setup as hunter_pictures_setup
        hunter_pictures_setup(self)

        # Start the scheduler
        from scheduler import start_scheduler
        start_scheduler()

# Initialize the bot
bot = MyBot(command_prefix='!', intents=intents, activity=discord.Activity(type=discord.ActivityType.watching, name="github.com/MarkCarsonDev/Trainwreck-Autodeployment"))

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

bot.run(TOKEN)
