import aiohttp
from discord.ext import commands

async def fetch_latest_commit_date(username):
    url = f'https://api.github.com/users/{username}/events'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                return None
            events = await response.json()
            for event in events:
                if event['type'] == 'PushEvent':
                    return event['created_at']
    return None

@commands.command()
async def finduser(ctx, username):
    """
    Fetches and displays the date of the most recent commit for a given GitHub username.
    """
    commit_date = await fetch_latest_commit_date(username)
    if commit_date:
        await ctx.reply(f"The most recent commit by {username} was on {commit_date}.")
    else:
        await ctx.reply(f"Could not find recent commits for {username}.")

def setup(bot):
    bot.add_command(finduser)
