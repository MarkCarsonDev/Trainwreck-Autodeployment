from discord.ext import commands
import typing

@commands.command()
async def example_command(ctx):
    """
    Description under !help
    """
    gif_url = "https://tenor.com/view/dissolve-gif-18144671279500427383"
    await ctx.send(gif_url)

def setup(bot):
    bot.add_command(example_command)