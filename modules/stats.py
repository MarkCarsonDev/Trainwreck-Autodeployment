import json
import discord
from discord.ext import commands
import matplotlib.pyplot as plt
import io
from datetime import datetime, timedelta
import os
import aiohttp
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

# Load user information from JSON file
def load_user_info():
    try:
        with open('../user_info.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

async def get_user_message_counts(guild, user_id, days=30):
    """Get message counts for the last specified days"""
    today = datetime.now()
    counts = {}
    
    # Initialize all days with zero
    for i in range(days):
        date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
        counts[date] = 0
    
    # Count messages in all channels
    for channel in guild.text_channels:
        try:
            async for message in channel.history(limit=None, after=today - timedelta(days=days)):
                if message.author.id == user_id:
                    date = message.created_at.strftime('%Y-%m-%d')
                    if date in counts:
                        counts[date] += 1
        except (discord.Forbidden, discord.HTTPException):
            continue
    
    # Convert to ordered list for plotting
    dates = sorted(counts.keys())
    message_counts = [counts[date] for date in dates]
    
    return dates, message_counts

async def generate_activity_graph(guild, user_id):
    """Generate an activity graph for the user"""
    dates, message_counts = await get_user_message_counts(guild, user_id)
    
    plt.figure(figsize=(10, 5))
    plt.plot(range(len(dates)), message_counts, marker='o', linestyle='-', color='#5865F2')
    plt.title(f'Discord Activity (Last 30 Days)')
    plt.xlabel('Days Ago')
    plt.ylabel('Messages')
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Add the dates as x-axis labels but only show every few days
    tick_indices = range(0, len(dates), 5)
    plt.xticks(tick_indices, [dates[i].split('-')[2] + '/' + dates[i].split('-')[1] for i in tick_indices])
    
    # Set background color
    plt.gca().set_facecolor('#36393F')
    plt.gcf().set_facecolor('#36393F')
    
    # Set text color to white
    plt.gca().xaxis.label.set_color('white')
    plt.gca().yaxis.label.set_color('white')
    plt.gca().title.set_color('white')
    plt.gca().tick_params(axis='x', colors='white')
    plt.gca().tick_params(axis='y', colors='white')
    
    # Save to bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', facecolor='#36393F')
    buf.seek(0)
    plt.close()
    
    return buf

async def fetch_github_data(username):
    """Fetch GitHub data for a user"""
    url = f'https://api.github.com/users/{username}'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                return None
            return await response.json()

@commands.command()
async def stats(ctx, member: discord.Member = None):
    """
    Shows a user's profile with stats, points, and activity.
    """
    if member is None:
        member = ctx.author
    
    # Send a loading message first
    loading_message = await ctx.reply(f"{ctx.author.mention} I'm generating stats for {member.display_name}... This might take a moment due to Discord rate limits.")
    
    try:
        user_info = load_user_info()
        user_id = str(member.id)
        
        # If user not in database, initialize them
        if user_id not in user_info:
            await loading_message.delete()
            await ctx.send(f"No stats available for {member.display_name}. They need to set their GitHub username first!")
            return
        
        user_data = user_info[user_id]
        
        # Create embed
        embed = discord.Embed(
            title=f"📊 {member.display_name}'s Profile",
            description=f"Stats for {member.mention}",
            color=member.color if member.color != discord.Color.default() else discord.Color.blurple()
        )
        
        # Add GitHub info
        if 'github_username' in user_data:
            github_info = await fetch_github_data(user_data['github_username'])
            if github_info:
                embed.add_field(
                    name="GitHub",
                    value=f"[{user_data['github_username']}](https://github.com/{user_data['github_username']})\n" +
                          f"Repos: {github_info.get('public_repos', 'N/A')}\n" +
                          f"Followers: {github_info.get('followers', 'N/A')}",
                    inline=True
                )
        
        # Add points and streaks
        points = user_data.get('points', 0)
        streak_weeks = user_data.get('streak_weeks', 0)
        
        embed.add_field(
            name="Points & Streaks",
            value=f"🏆 Points: **{points}**\n" +
                  f"🔥 Streak: **{streak_weeks}** weeks\n" +
                  f"Current Multiplier: **{round(1.2 ** streak_weeks, 2)}x**",
            inline=True
        )
        
        # Add shame counter
        shame_count = user_data.get('shame_count', 0)
        embed.add_field(
            name="Hall of Shame",
            value=f"😱 Shamed **{shame_count}** times",
            inline=True
        )
        
        # Get message counts
        dates, message_counts = await get_user_message_counts(ctx.guild, member.id)
        total_messages = sum(message_counts)
        
        # Add join date and total messages
        embed.add_field(
            name="Discord Info",
            value=f"📅 Joined: {discord.utils.format_dt(member.joined_at, 'D')}\n" +
                  f"🔤 Messages (30 days): {total_messages}",
            inline=False
        )
        
        # Add custom user information
        custom_info = []
        for key, value in user_data.items():
            # Skip standard fields
            if key in ['github_username', 'points', 'streak_weeks', 'shame_count']:
                continue
            custom_info.append(f"**{key.replace('_', ' ').title()}**: {value}")
        
        if custom_info:
            embed.add_field(
                name="Custom Info",
                value="\n".join(custom_info),
                inline=False
            )
        
        # Set user avatar as thumbnail
        embed.set_thumbnail(url=member.display_avatar.url)
        
        # Generate and attach activity graph
        activity_graph = await generate_activity_graph(ctx.guild, member.id)
        file = discord.File(activity_graph, filename="activity.png")
        embed.set_image(url="attachment://activity.png")
        
        # Add footer
        embed.set_footer(text=f"ID: {member.id} • Stats last updated: {discord.utils.format_dt(datetime.now(), 'R')}")
        
        # Delete the loading message and send the stats
        await loading_message.delete()
        await ctx.send(file=file, embed=embed)
        
    except Exception as e:
        # If something goes wrong, edit the loading message to show the error
        await loading_message.edit(content=f"Error generating stats: {str(e)}")

def setup(bot):
    bot.add_command(stats)