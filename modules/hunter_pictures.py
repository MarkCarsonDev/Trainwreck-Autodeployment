import discord
from discord.ext import commands
import random
import json
import os

HUNTER_PICS_CHANNEL = 1164341156277145683
PARENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
BLACKLIST_FILE = os.path.join(PARENT_DIR, 'hunter_pic_blacklist.json')

class HunterPictures(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.blacklist = self.load_blacklist()

    def load_blacklist(self):
        if os.path.exists(BLACKLIST_FILE):
            with open(BLACKLIST_FILE, 'r') as f:
                return json.load(f)
        else:
            with open(BLACKLIST_FILE, 'w') as f:
                json.dump([], f)
            return []

    def save_blacklist(self):
        with open(BLACKLIST_FILE, 'w') as f:
            json.dump(self.blacklist, f)

    async def get_media_links(self, channel):
        media_links = []
        async for message in channel.history(limit=500):
            if message.attachments:
                for attachment in message.attachments:
                    if attachment.url not in self.blacklist:
                        media_links.append(attachment.url)
            if message.embeds:
                for embed in message.embeds:
                    if embed.url and embed.url not in self.blacklist:
                        media_links.append(embed.url)
        return media_links

    @commands.command(name='pookie')
    async def pookie(self, ctx):
        channel = self.bot.get_channel(HUNTER_PICS_CHANNEL)
        media_links = await self.get_media_links(channel)
        if not media_links:
            await ctx.send("No media links found or all links are blacklisted.")
            return

        chosen_link = random.choice(media_links)
        message = await ctx.send(chosen_link)
        await message.add_reaction('❌')

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return
        
        if str(reaction.emoji) == '❌':
            message = reaction.message
            if message.author != self.bot.user:
                return

            link = message.content
            if link not in self.blacklist:
                self.blacklist.append(link)
                self.save_blacklist()

            channel = self.bot.get_channel(HUNTER_PICS_CHANNEL)
            media_links = await self.get_media_links(channel)
            if not media_links:
                await message.edit(content="No more media links available.")
                return

            new_link = random.choice(media_links)
            await message.edit(content=new_link)
            await message.remove_reaction('❌', user)

def setup(bot):
    bot.add_cog(HunterPictures(bot))
