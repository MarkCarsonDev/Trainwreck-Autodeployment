from discord.ext import commands

@commands.command()
async def example_command(ctx, arg1: str, *, everythingafterarg1: str):
    """
    Description under !help
    """
    gif_url = "https://tenor.com/view/dissolve-gif-18144671279500427383"
    if not arg1:
        arg1 = ""
    if not everythingafterarg1:
        everythingafterarg1 = ""
        
    await ctx.send(gif_url, arg1, "\n", everythingafterarg1)

def setup(bot):
    bot.add_command(example_command)