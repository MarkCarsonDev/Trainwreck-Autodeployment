import aiohttp
import json
from discord.ext import commands
from scheduler import schedule
from datetime import datetime, timedelta

SHAME_CHANNEL_ID = 1082164945438916679

# Load GitHub usernames from JSON file
def load_github_usernames():
    try:
        with open('../user_info.json', 'r') as file:
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

    worst_users = []

    for discord_id, info in usernames.items():
        github_username = info['github_username']
        commit_count = await fetch_commits_in_last_week(github_username)
        if commit_count is not None and commit_count <= min_commits:
            if commit_count < min_commits:
                worst_users = []

            worst_users.append((discord_id, github_username))
            min_commits = commit_count
            

    if len(worst_users):
        mentions = [await ctx.bot.fetch_user(user[0]) for user in worst_users]
        
        await ctx.reply(f"Shame on you, {', '.join([mention.mention for mention in mentions])}! You have made the least commits ({min_commits}) in the last week!")

@schedule("0 17 * * 5")  # At 17:00 on Friday
async def scheduled_shame_task(bot):
    channel = bot.get_channel(SHAME_CHANNEL_ID)
    if channel:
        ctx = await bot.get_context(await channel.send("Starting weekly shame task..."))
        await shame(ctx)

def setup(bot):
    bot.add_command(shame)
    scheduled_shame_task.start_task(bot)
