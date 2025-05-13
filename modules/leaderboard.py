import json
import discord
from discord.ext import commands
import matplotlib.pyplot as plt
import io
from datetime import datetime
import os

# Load user information from JSON file
def load_user_info():
    try:
        with open('../user_info.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

async def generate_leaderboard_chart(ctx, user_entries, sort_field, title_text):
    """Generates a bar chart visualization for the leaderboard"""
    # Create a bar chart of the top users
    plt.figure(figsize=(10, 6))
    
    # Get top 8 or fewer users for better readability in the chart
    # Even if the user requests more in the leaderboard text
    # chart_entries = user_entries[:min(8, len(user_entries))]

    # Get 8 or fewer for the chart, but if an argument for number is given, use the top 4 total and bottom 4 from that point
    chart_entries = user_entries[:min(4, len(user_entries))]
    if len(user_entries) > 8:
        chart_entries += user_entries[-4:]
    else:   
        chart_entries += user_entries[4:8]
    # Sort the chart entries by the specified field
    chart_entries.sort(key=lambda x: x[sort_field], reverse=True)
    chart_entries = chart_entries[:8]  # Limit to top 8 for the chart
    
    # Get usernames and values
    usernames = []
    values = []
    
    for entry in chart_entries:
        try:
            user = await ctx.bot.fetch_user(int(entry['id']))
            usernames.append(user.display_name)
            values.append(entry[sort_field])
        except:
            continue
    
    # Generate bar chart with custom colors
    colors = ['#5865F2', '#57F287', '#FEE75C', '#EB459E', '#ED4245', '#9B59B6', '#3498DB', '#2ECC71']
    plt.bar(range(len(usernames)), values, color=colors[:len(usernames)])
    plt.xticks(range(len(usernames)), usernames, rotation=45, ha='right')
    plt.title(f"{title_text}")
    plt.ylabel(sort_field.replace('_', ' ').title())
    plt.tight_layout()
    
    # Set background color to match Discord dark theme
    plt.gca().set_facecolor('#36393F')
    plt.gcf().set_facecolor('#36393F')
    
    # Set text color to white
    plt.gca().xaxis.label.set_color('white')
    plt.gca().yaxis.label.set_color('white')
    plt.gca().title.set_color('white')
    plt.gca().tick_params(axis='x', colors='white')
    plt.gca().tick_params(axis='y', colors='white')
    
    # Add value labels on top of each bar
    for i, v in enumerate(values):
        plt.text(i, v + max(values)*0.03, str(v), color='white', ha='center')
    
    # Save to bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', facecolor='#36393F')
    buf.seek(0)
    plt.close()
    
    return discord.File(buf, filename="leaderboard.png")

@commands.command()
async def leaderboard(ctx, limit="10"):
    """
    Shows the leaderboard ranking users by points.
    Usage: !leaderboard [number]
    Example: !leaderboard 20 - Shows top 20 users
    """
    # Check if the argument is a number
    if not limit.isdigit():
        await ctx.reply(f"Invalid argument. Please provide a number (e.g., !leaderboard 20)")
        return
        
    limit = int(limit)
    user_info = load_user_info()
    
    # Send a loading message first
    loading_message = await ctx.reply(f"{ctx.author.mention} I'm generating the leaderboard... One moment please.")
    
    try:
        # Convert user_info dict to a list of entries for sorting
        user_entries = []
        
        for user_id, data in user_info.items():
            # Skip users without GitHub usernames
            if 'github_username' not in data:
                continue
                
            # Add entry with all relevant data
            entry = {
                'id': user_id,
                'github_username': data['github_username'],
                'points': data.get('points', 0),
                'streak_weeks': data.get('streak_weeks', 0),
                'shame_count': data.get('shame_count', 0),
                'multiplier': round(1.2 ** data.get('streak_weeks', 0), 2)
            }
            
            user_entries.append(entry)
        
        # Sort based on category
        user_entries.sort(key=lambda x: x['points'], reverse=True)
        title = "🏆 Points Leaderboard"
        description = "Who's putting in commits?"
        sort_field = "points"
        sort_emoji = "🏆"
        
        # Generate leaderboard embed
        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.gold()
        )
        
        # Generate the leaderboard entries
        leaderboard_text = []
        
        for i, entry in enumerate(user_entries[:limit]):  # Use limit parameter
            try:
                # Fetch Discord user
                user = await ctx.bot.fetch_user(int(entry['id']))
                username = user.display_name
                
                # Create rank emoji
                rank_emoji = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
                
                # Create leaderboard entry
                entry_text = (
                    f"{rank_emoji} **{username}** [@{entry['github_username']}]\n"
                    f"   {sort_emoji} **{entry[sort_field]}** | "
                    f"🔥 Streak: {entry['streak_weeks']} (x{entry['multiplier']}) | "
                    f"😱 Shame: {entry['shame_count']}"
                )
                
                leaderboard_text.append(entry_text)
            except Exception as e:
                print(f"Error processing user {entry['id']}: {str(e)}")
        
        if leaderboard_text:
            embed.add_field(
                name="Rankings",
                value="\n\n".join(leaderboard_text),
                inline=False
            )
        else:
            embed.add_field(
                name="No Data",
                value="No users found with GitHub usernames set up.",
                inline=False
            )
            
        # Add statistics field
        if len(user_entries) > 0:
            total_points = sum(entry['points'] for entry in user_entries)
            total_shame = sum(entry['shame_count'] for entry in user_entries)
            avg_streak = round(sum(entry['streak_weeks'] for entry in user_entries) / len(user_entries), 1)
            
            stats_text = (
                f"Total Points: **{total_points}**\n"
                f"Average Streak: **{avg_streak}** weeks\n"
                f"Total Shame Count: **{total_shame}**\n"
                f"Users Tracked: **{len(user_entries)}**"
            )
            
            embed.add_field(
                name="Stats Overview",
                value=stats_text,
                inline=False
            )
            
        # Add footer
        embed.set_footer(text=f"Use !leaderboard [points|streaks|shame] to view different rankings • Last updated: {discord.utils.format_dt(datetime.now(), 'R')}")
        
        # Generate and attach bar chart if we have entries
        if len(user_entries) > 0:
            chart_file = await generate_leaderboard_chart(ctx, user_entries, sort_field, title)
            embed.set_image(url="attachment://leaderboard.png")
            
            # Delete the loading message and send the leaderboard with chart
            await loading_message.delete()
            await ctx.send(file=chart_file, embed=embed)
        else:
            # No entries, just send the embed
            await loading_message.delete()
            await ctx.send(embed=embed)
            
    except Exception as e:
        # If something goes wrong, edit the loading message to show the error
        await loading_message.edit(content=f"Error generating leaderboard: {str(e)}")

@commands.command()
async def rank(ctx, member: discord.Member = None):
    """
    Shows a user's ranking and competitive stats on the leaderboard.
    """
    if member is None:
        member = ctx.author
    
    user_info = load_user_info()
    user_id = str(member.id)
    
    if user_id not in user_info or 'github_username' not in user_info[user_id]:
        await ctx.reply(f"{member.display_name} doesn't have a profile yet. They should set up with `!setupuser <github_username>`")
        return
    
    # Get user's data
    user_data = user_info[user_id]
    user_points = user_data.get('points', 0)
    user_streak = user_data.get('streak_weeks', 0)
    user_shame = user_data.get('shame_count', 0)
    streak_multiplier = round(1.2 ** user_streak, 2)
    
    # Calculate user's ranks in different categories
    points_ranks = []
    streak_ranks = []
    shame_ranks = []
    
    for uid, data in user_info.items():
        if 'github_username' in data:
            points_ranks.append((uid, data.get('points', 0)))
            streak_ranks.append((uid, data.get('streak_weeks', 0)))
            shame_ranks.append((uid, data.get('shame_count', 0)))
    
    points_ranks.sort(key=lambda x: x[1], reverse=True)
    streak_ranks.sort(key=lambda x: x[1], reverse=True)
    shame_ranks.sort(key=lambda x: x[1], reverse=True)
    
    points_rank = next((i+1 for i, (uid, _) in enumerate(points_ranks) if uid == user_id), "N/A")
    streak_rank = next((i+1 for i, (uid, _) in enumerate(streak_ranks) if uid == user_id), "N/A")
    shame_rank = next((i+1 for i, (uid, _) in enumerate(shame_ranks) if uid == user_id), "N/A")
    
    # Calculate how many points to next rank
    points_to_next = "Already #1! 👑" if points_rank == 1 else "N/A"
    if points_rank != 1 and points_rank != "N/A":
        next_user_points = points_ranks[points_rank-2][1]  # -2 because zero-indexed and we want the user above
        points_to_next = next_user_points - user_points
    
    # Create embed
    embed = discord.Embed(
        title=f"📊 Ranking for {member.display_name}",
        description=f"GitHub: [@{user_data['github_username']}](https://github.com/{user_data['github_username']})",
        color=member.color if member.color != discord.Color.default() else discord.Color.blurple()
    )
    
    embed.add_field(
        name="Rank Status",
        value=f"🏆 Points Rank: **#{points_rank}** of {len(points_ranks)}\n"
              f"🔥 Streak Rank: **#{streak_rank}** of {len(streak_ranks)}\n"
              f"😱 Shame Rank: **#{shame_rank}** of {len(shame_ranks)}",
        inline=True
    )
    
    embed.add_field(
        name="Stats",
        value=f"Points: **{user_points}**\n"
              f"Streak: **{user_streak}** weeks\n"
              f"Multiplier: **{streak_multiplier}x**\n"
              f"Shame Count: **{user_shame}**",
        inline=True
    )
    
    embed.add_field(
        name="Progress",
        value=f"Points to next rank: **{points_to_next}**\n"
              f"Weekly points with current streak: **{round(69 * streak_multiplier)}** per commit",
        inline=False
    )
    
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text=f"Want to improve? Push more commits, code monkey. • Updated: {discord.utils.format_dt(datetime.now(), 'R')}")
    
    await ctx.reply(embed=embed)

def setup(bot):
    bot.add_command(leaderboard)
    bot.add_command(rank)