import random
import json
import os
from discord.ext import commands, tasks
from discord import NotFound

HUNTER_PICS_CHANNEL = 1164341156277145683
BLACKLIST_FILE = '../hunter_pic_blacklist.json'

def load_blacklist():
    try:
        with open(BLACKLIST_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return []

def save_blacklist(blacklist):
    with open(BLACKLIST_FILE, 'w') as file:
        json.dump(blacklist, file)

async def get_media_links(channel):
    blacklist = load_blacklist()
    media_links = []

    async for message in channel.history(limit=None):
        if message.attachments:
            for attachment in message.attachments:
                if attachment.url not in blacklist:
                    media_links.append(attachment.url)
        if message.embeds:
            for embed in message.embeds:
                if embed.url and embed.url not in blacklist:
                    media_links.append(embed.url)
                    
    return media_links

class HunterPictures(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.add_listener(self.on_reaction_add)

    @commands.command()
    async def pookie(self, ctx):
        channel = self.bot.get_channel(HUNTER_PICS_CHANNEL)
        media_links = await get_media_links(channel)
        
        if not media_links:
            await ctx.send("No available media found.")
            return
        
        chosen_media = random.choice(media_links)
        sent_message = await ctx.send(chosen_media)
        await sent_message.add_reaction('❌')

    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return
        
        if reaction.emoji == '❌':
            message = reaction.message
            if message.channel.id != HUNTER_PICS_CHANNEL:
                return

            if message.author.id != self.bot.user.id:
                return

            blacklist = load_blacklist()
            blacklist.append(message.content)
            save_blacklist(blacklist)

            channel = self.bot.get_channel(HUNTER_PICS_CHANNEL)
            media_links = await get_media_links(channel)
            if not media_links:
                await message.edit(content="No more available media.")
            else:
                new_media = random.choice(media_links)
                await message.edit(content=new_media)
            await reaction.remove(user)

def setup(bot):
    bot.add_cog(HunterPictures(bot))
