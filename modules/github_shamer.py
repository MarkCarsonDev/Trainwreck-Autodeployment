import aiohttp
import json
import discord
from discord.ext import commands
from scheduler import schedule
from datetime import datetime, timedelta

SHAME_CHANNEL_ID = 1082164945438916679

# Load GitHub usernames from JSON file
def load_github_usernames():
    try:
        with open('user_info.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

async def fetch_commits_in_last_week(username):
    one_week_ago = datetime.now() - timedelta(days=7)
    url = f'https://api.github.com/users/{username}/events/public'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                return None
            events = await response.json()
            commit_count = 0
            for event in events:
                if event['type'] == 'PushEvent':
                    event_time = datetime.strptime(event['created_at'], '%Y-%m-%dT%H:%M:%SZ')
                    if event_time > one_week_ago:
                        commit_count += 1
            return commit_count

@commands.command()
async def shame(ctx):
    """
    Finds and shames the user with the least commits in the last week.
    """
    usernames = load_github_usernames()
    min_commits = float('inf')
    worst_user = None

    for discord_id, info in usernames.items():
        github_username = info['github_username']
        commit_count = await fetch_commits_in_last_week(github_username)
        if commit_count is not None and commit_count < min_commits:
            min_commits = commit_count
            worst_user = (discord_id, github_username)

    if worst_user:
        discord_user = await ctx.bot.fetch_user(worst_user[0])
        await ctx.reply(f"{discord_user.mention} has made the least commits ({min_commits}) in the last week! Shame!")

@schedule("0 17 * * 5")  # At 17:00 on Friday
async def scheduled_shame_task(bot):
    channel = bot.get_channel(SHAME_CHANNEL_ID)
    if channel:
        ctx = await bot.get_context(await channel.send("Starting weekly shame task..."))
        await shame(ctx)

def setup(bot):
    bot.add_command(shame)
    bot.loop.create_task(scheduled_shame_task(bot))
