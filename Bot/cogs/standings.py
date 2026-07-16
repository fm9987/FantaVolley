# cogs/standings.py
import discord
from discord import app_commands
from discord.ext import commands

class Standings(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="standings", description="Show current league standings")
    async def standings(self, interaction: discord.Interaction):
        # TODO: pull from DB
        await interaction.response.send_message("standings here")

    @app_commands.command(name="score", description="Show your team's score this week")
    async def score(self, interaction: discord.Interaction):
        await interaction.response.send_message("score here")

async def setup(bot: commands.Bot):
    await bot.add_cog(Standings(bot))  # <-- required at bottom of every cog