# bot.py
import discord
import os
from discord.ext import commands
from config import TOKEN, GUILD_ID, CHANNEL_ID

class FantasyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        self.guild_id = GUILD_ID

    async def setup_hook(self):
        # Load all cogs
        cog_list = [
            "cogs.admin",
            "cogs.draft",
            "cogs.lineup",
            "cogs.trades",
            "cogs.standings",
        ]
        for cog in cog_list:
            await self.load_extension(cog)
            print(f"  Loaded {cog}")

        # Sync slash commands to your guild (instant, no 1hr global delay)
        guild = discord.Object(id=self.guild_id)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        print("Slash commands synced.")

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        channel = self.get_channel(CHANNEL_ID)
        if channel:
            await channel.send("MOFOS I am alive and kicking!")

    async def close(self):
        channel = self.get_channel(CHANNEL_ID)
        if channel:
            await channel.send("I need some sleep too! \nCatch ya laters suckers")
        await super().close()

bot = FantasyBot()
bot.run(TOKEN)