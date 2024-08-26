import discord
import asyncio
import logging
import mimetypes
import os
import pathlib
import random
import string
import json

from discord.ext import commands

from botlogic import *

import magic

intents = discord.Intents.default()
intents.message_content = True

class EchoBot(commands.Cog, BotLogic):
    def __init__(self, bot):
        BotLogic.__init__(self)
        #commands.Cog.__init__(self)

        self.bot = bot
        self.logger = logging.getLogger('discord')
        self.logger.setLevel(logging.INFO)
        self.magic = magic.Magic()
        self.ctx = None


    def get_image_mime_type(self, image_data):
        mime_type = self.magic.from_buffer(image_data)
        return mime_type


    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Logged in as {self.bot.user.name}')
        for guild in self.bot.guilds:
            # Find the first available text channel in each guild
            default_channel = discord.utils.find(
                lambda c: isinstance(c, discord.TextChannel), 
                guild.text_channels
            )

            if default_channel:
                self.ctx = default_channel
        await self.bot.change_presence(activity=discord.Game(name='Available (Llamara3)'))


    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user or not isinstance(message.channel, discord.DMChannel):
            return


        user_message = self.sanitize_ascii_input(message.content.strip())
        user_handle = self.sanitize_ascii_input(message.author.name+"#"+str(message.author.id), True)

        if message.content and not (message.content.startswith('https://') and 'upload' in message.content):
            await self.bot.change_presence(activity=discord.Game(name='Available (Llamara3)'))
            await self.process_message(user_handle, user_message)


    @commands.command()
    async def send_text_message(self, ctx, user_handle, text: str):
        ctx = self.ctx

        user = await self.get_user_by_handle(user_handle)


        try:
            if user:
                await user.send(text)
                return True
            else:
                await ctx.send(f'User {user_handle} not found.')
                return False
        except Exception as e:
            self.logger.error(f"Could not send text message: {e}")
            await ctx.send("Error when sending text message.")
            return False


    async def get_user_by_handle(self, user_handle):
        ctx = self.ctx
        user_id = int(user_handle.split("#")[-1])
        user = bot.get_user(user_id)
    
        if user is None:
            # If user is not cached, try to fetch from Discord
            try:
                user = await bot.fetch_user(user_id)
            except discord.NotFound:
                await ctx.send("User not found.")
                return None
            except discord.Forbidden:
                await ctx.send("Bot does not have permission to access user.")
                return None
        return user


    @commands.command()
    async def send_voice_message(self, ctx, user_handle, text: str):
        ctx = self.ctx
        
        user = await self.get_user_by_handle(user_handle)

        try:
            if user:
                if await self.generate_tts_audio(text, user_handle):
                    self.process_audio_files(user_handle)
                    await user.send(file=discord.File("temp_audios/"+user_handle+".mp3"))
                else:
                    await ctx.send("Error generating audio file.")
                return True
            else:
                await ctx.send(f'User {user_handle} not found.')
                return False
        except Exception as e:
            self.logger.error(f"Could not send voice message: {e}")
            await ctx.send("Error when sending voice message.")
            return False


    @commands.command()
    async def set_avatar(self, ctx):
        ctx = self.ctx
        avatar_path = os.path.expanduser("assets/avatar.jpg")
        if os.path.isfile(avatar_path):
            with open(avatar_path, 'rb') as avatar_file:
                avatar = avatar_file.read()
                avatar_type = self.get_image_mime_type(avatar)
                try:
                    await self.bot.user.edit(avatar=avatar)
                    await ctx.send("Avatar updated successfully.")
                except discord.HTTPException as e:
                    self.logger.error(f"Could not set avatar: {e}")
                    await ctx.send("Error when setting avatar.")
        else:
            await ctx.send("Avatar file not found.")


    def is_connected(self) -> bool:
        return self.is_ready()


if __name__ == '__main__':
    with open("config.json", 'r') as file:
        config = json.load(file)

    if 'token' not in config or len(config['token']) < 10:
        print("Discord bot token missing or invalid in config.json.")
    elif not config or not "model" in config or len(config["model"]) < 3:
        print("Model name missing in config.json (e.g. Llama-3-8B-Instruct-abliterated-v2:latest)")
    else:
        logging.basicConfig(level=logging.INFO)

        intents = discord.Intents.default()
        intents.message_content = True
        bot = commands.Bot(command_prefix='!', intents=intents)
        mybot = EchoBot(bot)
        mybot.model = config["model"]
        asyncio.run(bot.add_cog(mybot))

        @bot.event
        async def on_disconnect():
            print("Bot disconnected. Attempting to reconnect...")
            while True:
                try:
                    asyncio.run(bot.connect())
                    break
                except Exception as e:
                    print(f"Reconnection failed: {e}. Retrying in 10 seconds...")
                    await asyncio.sleep(10)

        bot.run(config['token'])