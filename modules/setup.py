import json
import discord
from discord.ext import commands
import aiohttp
import re

# Load and save user info
def load_user_info():
    try:
        with open('../user_info.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_user_info(data):
    with open('../user_info.json', 'w') as file:
        json.dump(data, file, indent=4)

async def validate_github_username(username):
    """Verify that a GitHub username exists"""
    url = f'https://api.github.com/users/{username}'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return response.status == 200

@commands.command()
async def setupuser(ctx, github_username=None):
    """
    Set up your profile with your GitHub username.
    Example: !setupuser johndoe
    """
    if github_username is None:
        await ctx.send("Please provide your GitHub username. Example: `!setupuser johndoe`")
        return
    
    # Validate GitHub username
    if not await validate_github_username(github_username):
        await ctx.send(f"❌ GitHub username `{github_username}` doesn't seem to exist. Please check the spelling and try again.")
        return
    
    user_info = load_user_info()
    user_id = str(ctx.author.id)
    
    # Initialize user if not exists
    if user_id not in user_info:
        user_info[user_id] = {}
    
    # Update GitHub username
    user_info[user_id]['github_username'] = github_username
    
    # Initialize other fields if they don't exist
    if 'points' not in user_info[user_id]:
        user_info[user_id]['points'] = 0
    if 'streak_weeks' not in user_info[user_id]:
        user_info[user_id]['streak_weeks'] = 0
    if 'shame_count' not in user_info[user_id]:
        user_info[user_id]['shame_count'] = 0
    
    # Save updated user info
    save_user_info(user_info)
    
    # Create confirmation embed
    embed = discord.Embed(
        title="✅ Profile Setup Complete",
        description=f"{ctx.author.mention}, your profile has been set up successfully!",
        color=discord.Color.green()
    )
    
    embed.add_field(
        name="GitHub Username",
        value=f"[{github_username}](https://github.com/{github_username})",
        inline=False
    )
    
    embed.add_field(
        name="Getting Started",
        value="You're all set to start earning points for your GitHub contributions!\n\n"
              "• Use `!stats` to see your profile\n"
              "• Use `!leaderboard` to see the rankings\n"
              "• Every Friday, you'll earn points based on your GitHub activity",
        inline=False
    )
    
    embed.set_thumbnail(url=ctx.author.display_avatar.url)
    embed.set_footer(text="Welcome to the coding game! 🎮")
    
    await ctx.send(embed=embed)

@commands.command()
async def addinfo(ctx, key=None, *, value=None):
    """
    Add custom information to your profile.
    Example: !addinfo favorite_language Python
    """
    if key is None or value is None:
        await ctx.send("Please provide both a key and value. Example: `!addinfo favorite_language Python`")
        return
    
    # Make sure key doesn't contain spaces and is lowercase
    key = key.lower().strip()
    if " " in key:
        await ctx.send("❌ The key cannot contain spaces. Use underscores instead.")
        return
    
    # Prevent overriding critical fields
    protected_keys = ['github_username', 'points', 'streak_weeks', 'shame_count']
    if key in protected_keys:
        await ctx.send(f"❌ The key `{key}` is protected and cannot be modified directly.")
        return
    
    user_info = load_user_info()
    user_id = str(ctx.author.id)
    
    # Initialize user if not exists
    if user_id not in user_info:
        await ctx.send("❌ You need to set up your profile first. Use `!setup <github_username>`")
        return
    
    # Update the custom information
    user_info[user_id][key] = value
    
    # Save updated user info
    save_user_info(user_info)
    
    await ctx.send(f"✅ Added `{key}: {value}` to your profile. View your profile with `!stats`")

@commands.command()
async def removeinfo(ctx, key=None):
    """
    Remove custom information from your profile.
    Example: !removeinfo favorite_language
    """
    if key is None:
        await ctx.send("Please provide a key to remove. Example: `!removeinfo favorite_language`")
        return
    
    # Make sure key is lowercase
    key = key.lower().strip()
    
    # Prevent removing critical fields
    protected_keys = ['github_username', 'points', 'streak_weeks', 'shame_count']
    if key in protected_keys:
        await ctx.send(f"❌ The key `{key}` is protected and cannot be removed.")
        return
    
    user_info = load_user_info()
    user_id = str(ctx.author.id)
    
    # Check if user exists
    if user_id not in user_info:
        await ctx.send("❌ You need to set up your profile first. Use `!setupuser <github_username>`")
        return
    
    # Check if key exists
    if key not in user_info[user_id]:
        await ctx.send(f"❌ The key `{key}` doesn't exist in your profile.")
        return
    
    # Remove the key
    del user_info[user_id][key]
    
    # Save updated user info
    save_user_info(user_info)
    
    await ctx.send(f"✅ Removed `{key}` from your profile.")

def setup(bot):
    bot.add_command(setupuser)
    bot.add_command(addinfo)
    bot.add_command(removeinfo)