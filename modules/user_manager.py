import json
from discord.ext import commands
from discord.ext.commands import Context

USER_INFO_FILE = 'user_info.json'

# Load user information from JSON file
def load_user_info():
    try:
        with open(USER_INFO_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

# Save user information to JSON file
def save_user_info(data):
    with open(USER_INFO_FILE, 'w') as file:
        json.dump(data, file, indent=4)

@commands.command()
async def showuser(ctx: Context, user: str):
    """
    Displays all of the user's full raw JSON.
    """
    user_id = int(user[3:-1])  # Extract user ID from mention format
    user_info = load_user_info()
    if str(user_id) in user_info:
        await ctx.reply(f"User info for {user}: ```json\n{json.dumps(user_info[str(user_id)], indent=4)}\n```")
    else:
        await ctx.reply(f"No info found for user {user}.")

@commands.command()
async def usermod(ctx: Context, user: str, operation: str, data: str):
    """
    Modifies the user information.
    Usage:
    !usermod @Mark +{"key": "value"}  # Merges the new JSON object with the existing one
    !usermod @Mark -["key1", "key2"]  # Removes keys from a user
    """
    user_id = int(user[3:-1])  # Extract user ID from mention format
    user_info = load_user_info()
    
    if str(user_id) not in user_info:
        user_info[str(user_id)] = {}

    if operation == '+':
        try:
            new_data = json.loads(data)
            user_info[str(user_id)].update(new_data)
            save_user_info(user_info)
            await ctx.reply(f"Updated info for user {user}.")
        except json.JSONDecodeError:
            await ctx.reply("Invalid JSON object. Usage: !usermod @Mark +{\"key\": \"value\"}")
    elif operation == '-':
        try:
            keys_to_remove = json.loads(data)
            if isinstance(keys_to_remove, list):
                for key in keys_to_remove:
                    user_info[str(user_id)].pop(key, None)
                save_user_info(user_info)
                await ctx.reply(f"Removed specified keys from user {user}.")
            else:
                await ctx.reply("Invalid key list. Usage: !usermod @Mark -[\"key1\", \"key2\"]")
        except json.JSONDecodeError:
            await ctx.reply("Invalid key list. Usage: !usermod @Mark -[\"key1\", \"key2\"]")
    else:
        await ctx.reply("Invalid operation. Use '+' to add or update and '-' to remove keys.")

@commands.command()
async def userdump(ctx: Context):
    """
    Dumps the whole JSON file.
    """
    user_info = load_user_info()
    await ctx.reply(f"Full user info: ```json\n{json.dumps(user_info, indent=4)}\n```")

@commands.command()
async def setuserinfo(ctx: Context, data: str):
    """
    Sets the entire userinfo file.
    Usage: !setuserinfo {json object}
    """
    try:
        new_data = json.loads(data)
        save_user_info(new_data)
        await ctx.reply("User info has been updated.")
    except json.JSONDecodeError:
        await ctx.reply("Invalid JSON object. Usage: !setuserinfo {\"key\": \"value\"}")

def setup(bot):
    bot.add_command(showuser)
    bot.add_command(usermod)
    bot.add_command(userdump)
    bot.add_command(setuserinfo)
