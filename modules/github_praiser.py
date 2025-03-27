import aiohttp
import json
from discord.ext import commands
from scheduler import schedule
from datetime import datetime, timedelta
import discord
import random
import copy

PRAISE_CHANNEL_ID = 1082164945438916679  # Same as shame channel for now

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
    """
    Fetches commit data for a GitHub user in the last week.
    
    Returns tuple of (total_commits, daily_commits) where
    daily_commits is a dict mapping days to commit counts
    """
    one_week_ago = datetime.now() - timedelta(days=7)
    url = f'https://api.github.com/users/{username}/events'
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                return 0, {}
                
            events = await response.json()
            commit_count = 0
            daily_commits = {}
            
            # Initialize daily_commits with all days of the week
            for i in range(7):
                day = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                daily_commits[day] = 0
            
            for event in events:
                if event['type'] == 'PushEvent':
                    event_time = datetime.strptime(event['created_at'], '%Y-%m-%dT%H:%M:%SZ')
                    if event_time > one_week_ago:
                        commit_count += 1
                        day = event_time.strftime('%Y-%m-%d')
                        if day in daily_commits:
                            daily_commits[day] += 1
            
            return commit_count, daily_commits

def calculate_points(commits, daily_commits, user_info):
    """Calculate points based on commits, streaks, and bonuses"""
    points = commits * 69
    
    # Check if user made commits every day
    daily_streak = all(count > 0 for count in daily_commits.values())
    if daily_streak:
        points *= 2
    
    # Calculate streak multiplier
    streak_weeks = user_info.get('streak_weeks', 0)
    if commits > 0:  # If they made at least one commit this week
        streak_multiplier = 1.0
        for _ in range(streak_weeks):
            streak_multiplier *= 1.2
        points *= streak_multiplier
    
    return round(points)

def update_streak(user_id, commits, user_info):
    """Update the user's streak information"""
    if commits > 0:
        user_info[str(user_id)]['streak_weeks'] = user_info.get(str(user_id), {}).get('streak_weeks', 0) + 1
    else:
        # Reset streak if no commits were made
        if str(user_id) in user_info:
            user_info[str(user_id)]['streak_weeks'] = 0
    
    return user_info

def get_praise_message(commits, points, streak_weeks):
    """Generate a praise message based on performance"""
    praise_messages = [
        f"Your work on {commits} commit{'' if commits == 1 else 's'} has earned you {points} points!",
    ]
    
    streak_messages = [
        f"You're on a {streak_weeks}-week streak! You're so much better than the rest of us!",
        f"You're on a {streak_weeks}-week streak! Way to show off...",
        f"You're on a {streak_weeks}-week streak! Too bad it won't get you a job.",
        f"You're on a {streak_weeks}-week streak! good job cutie :)",
    ]
    
    message = random.choice(praise_messages)
    
    if streak_weeks > 1:
        message += " " + random.choice(streak_messages)
    
    return message

async def generate_praise_embed(ctx, user_info, update_data=True):
    """
    Generate praise embed with messages
    
    Args:
        ctx: The command context
        user_info: The user info dictionary
        update_data: Whether to update the user info with new points and streaks
    
    Returns:
        Either an embed or a string message
    """
    praise_messages = []
    # Make a deep copy to avoid modifying the original if we're not updating
    working_info = user_info if update_data else copy.deepcopy(user_info)
    
    for discord_id, info in working_info.items():
        if 'github_username' in info:
            github_username = info['github_username']
            commits, daily_commits = await fetch_commits_in_last_week(github_username)
            
            # Initialize points if not exists
            if 'points' not in info:
                working_info[discord_id]['points'] = 0
            
            # Initialize streak_weeks if not exists
            if 'streak_weeks' not in info:
                working_info[discord_id]['streak_weeks'] = 0
            
            # Calculate points
            streak_weeks = info.get('streak_weeks', 0)
            points = calculate_points(commits, daily_commits, info)
            
            # Update user info
            if update_data:
                working_info[discord_id]['points'] = info.get('points', 0) + points
                working_info = update_streak(discord_id, commits, working_info)
            
            # Get user mention
            try:
                user = await ctx.bot.fetch_user(int(discord_id))
                user_mention = user.mention
                
                # Generate praise message
                if commits > 0:
                    next_streak = streak_weeks + 1 if commits > 0 else 0
                    message = f"{user_mention}: " + get_praise_message(commits, points, next_streak)
                    praise_messages.append(message)
            except:
                continue
    
    # Save updated user info ONLY if we are updating
    if update_data:
        save_user_info(working_info)
    
    if praise_messages:
        embed = discord.Embed(
            title="Praise Task",
            description="Let's see who brought honor to their names this week...",
            color=discord.Color.gold()
        )
        
        embed.add_field(name="Top Contributors", value="\n".join(praise_messages), inline=False)
        embed.set_footer(text="Next evaluation in one week. Keep it up, superstars.")
        
        return embed
    else:
        return "No GitHub activity found for any users this week. You all disappoint me."

@commands.command()
async def praise(ctx):
    """
    Praises users for their GitHub commits and awards points.
    """
    user_info = load_user_info()
    praise_result = await generate_praise_embed(ctx, user_info, update_data=True)
    
    if isinstance(praise_result, discord.Embed):
        await ctx.send(embed=praise_result)
    else:
        await ctx.send(praise_result)

@commands.command()
async def testpraise(ctx):
    """
    Tests the praise functionality in the current channel without updating points.
    """
    user_info = load_user_info()
    praise_result = await generate_praise_embed(ctx, user_info, update_data=False)
    
    if isinstance(praise_result, discord.Embed):
        await ctx.send("**TEST MODE - Points not actually awarded**", embed=praise_result)
    else:
        await ctx.send(f"**TEST MODE:** {praise_result}")

@schedule("0 16 * * 5")  # At 16:00 on Friday (1 hour before shame)
async def scheduled_praise_task(bot):
    channel = bot.get_channel(PRAISE_CHANNEL_ID)
    if channel:
        ctx = await bot.get_context(await channel.send("Starting weekly praise task..."))
        await praise(ctx)

def setup(bot):
    bot.add_command(praise)
    bot.add_command(testpraise)
    scheduled_praise_task.start_task(bot)