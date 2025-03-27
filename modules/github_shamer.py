import aiohttp
import json
from discord.ext import commands
from scheduler import schedule
from datetime import datetime, timedelta
import discord
import random

SHAME_CHANNEL_ID = 1082164945438916679

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

async def fetch_commits_in_last_week(username):
    one_week_ago = datetime.now() - timedelta(days=7)
    url = f'https://api.github.com/users/{username}/events'
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
        
def get_shame_message():
    messages = [
        "Yikes, you're gonna disappoint Gene Ruebsamen if you keep this up.",
        "Shame! Shame!",
        "You are NOT Todd Ebert's strongest soldier."
    ]
    return random.choice(messages)

async def generate_shame_result(ctx, user_info, update_counts=False):
    one_week_ago = datetime.now() - timedelta(days=7)
    min_commits = float('inf')
    worst_users = []

    for discord_id, info in user_info.items():
        if 'github_username' in info:
            github_username = info['github_username']
            commit_count = await fetch_commits_in_last_week(github_username)
            
            if commit_count is not None and commit_count <= min_commits:
                if commit_count < min_commits:
                    worst_users = []
                worst_users.append((discord_id, github_username))
                min_commits = commit_count

    if worst_users:
        if update_counts:
            for discord_id, _ in worst_users:
                if discord_id in user_info:
                    if 'shame_count' not in user_info[discord_id]:
                        user_info[discord_id]['shame_count'] = 0
                    user_info[discord_id]['shame_count'] += 1
            save_user_info(user_info)

        mentions = [await ctx.bot.fetch_user(int(user[0])) for user in worst_users]
        shame_message = get_shame_message()

        embed = discord.Embed(
            title="🔔 SHAME ALERT 🔔",
            description=f"{', '.join([mention.mention for mention in mentions])}",
            color=discord.Color.red()
        )

        embed.add_field(
            name="Weekly Shame Report",
            value=f"{shame_message}\n\nCommits this week: **{min_commits}**",
            inline=False
        )

        embed.set_footer(text="Do better next week! The GitHub gods are watching...")
        return embed
    else:
        return "No users to shame this week. Everyone's doing great!"



@commands.command()
async def shame(ctx):
    """
    Finds and shames the user with the least commits in the last week.
    """
    user_info = load_user_info()
    shame_result = await generate_shame_result(ctx, user_info, update_counts=True)
    
    if isinstance(shame_result, discord.Embed):
        await ctx.send(embed=shame_result)
    else:
        await ctx.send(shame_result)

@commands.command()
async def testshame(ctx):
    """
    Tests the shame functionality in the current channel without updating shame counts.
    """
    user_info = load_user_info()
    # Create a copy to avoid modifying real data
    test_info = json.loads(json.dumps(user_info))
    
    shame_result = await generate_shame_result(ctx, test_info, update_counts=False)
    
    if isinstance(shame_result, discord.Embed):
        await ctx.send("**TEST MODE - Shame counts not actually updated**", embed=shame_result)
    else:
        await ctx.send(f"**TEST MODE:** {shame_result}")

@schedule("0 17 * * 5")  # At 17:00 on Friday
async def scheduled_shame_task(bot):
    channel = bot.get_channel(SHAME_CHANNEL_ID)
    if channel:
        user_info = load_user_info()
        ctx = await bot.get_context(await channel.send("Starting weekly shame task..."))
        shame_result = await generate_shame_result(ctx, user_info, update_counts=True)
        if isinstance(shame_result, discord.Embed):
            await channel.send(embed=shame_result)
        else:
            await channel.send(shame_result)


def setup(bot):
    bot.add_command(shame)
    bot.add_command(testshame)
    scheduled_shame_task.start_task(bot)