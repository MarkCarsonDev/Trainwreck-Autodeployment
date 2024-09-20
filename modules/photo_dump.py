import os
import aiohttp
import discord
from discord.ext import commands
from datetime import datetime

async def get_media_links(channel):
    media = []
    async for message in channel.history(limit=None):
        for attachment in message.attachments:
            if not attachment.url.endswith('.gif') and 'cdn' in attachment.url:
                media.append((attachment.url, message.created_at))
        for embed in message.embeds:
            if hasattr(embed, 'url') and embed.url and not embed.url.endswith('.gif') and 'cdn' in embed.url:
                media.append((embed.url, message.created_at))
    return media

async def download_media(media, folder_path):
    async with aiohttp.ClientSession() as session:
        i = 0
        for url, timestamp in media:
            i += 1
            # Extract the file extension
            file_extension = url.split('?')[0].split('.')[-1]
            # Format the filename using the message's timestamp
            filename = f"{timestamp.strftime('%Y%m%d_%H%M%S')}.{file_extension}"
            print(f"Dumping {filename}... ({i}/{len(media)})")
            async with session.get(url) as resp:
                if resp.status == 200:
                    file_path = os.path.join(folder_path, filename)
                    with open(file_path, 'wb') as f:
                        while True:
                            chunk = await resp.content.read(1024)
                            if not chunk:
                                break
                            f.write(chunk)

@commands.command()
async def photodump(ctx):
    channel = ctx.channel
    media = await get_media_links(channel)
    if not media:
        await ctx.send("No available media found.")
        return

    datetime_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_name = f"dump_{channel.name}_{datetime_str}"
    os.makedirs(folder_name, exist_ok=True)

    await download_media(media, folder_name)
    await ctx.send(f"Media has been saved to {folder_name}.")

def setup(bot):
    bot.add_command(photodump)
