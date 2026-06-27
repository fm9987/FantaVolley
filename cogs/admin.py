# cogs/admin.py
import discord
from discord import app_commands
from discord.ext import commands
from db import SessionLocal, Manager, init_db

class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        init_db()  # create tables on startup if they don't exist

    @app_commands.command(name="register", description="Register yourself as a fantasy manager")
    @app_commands.describe(team_name="Your team's name")
    async def register(self, interaction: discord.Interaction, team_name: str):
        db = SessionLocal()
        try:
            discord_id = str(interaction.user.id)

            # Already registered?
            existing = db.query(Manager).filter_by(discord_id=discord_id).first()
            if existing:
                await interaction.response.send_message(
                    f"You're already registered as **{existing.team_name}**!", ephemeral=True
                )
                return

            # Team name taken?
            name_taken = db.query(Manager).filter_by(team_name=team_name).first()
            if name_taken:
                await interaction.response.send_message(
                    f"The team name **{team_name}** is already taken. Pick another!", ephemeral=True
                )
                return

            manager = Manager(discord_id=discord_id, team_name=team_name)
            db.add(manager)
            db.commit()

            await interaction.response.send_message(
                f"✅ **{interaction.user.display_name}** registered as manager of **{team_name}**!"
            )
        finally:
            db.close()


    @app_commands.command(name="team_logo", description="Upload your team logo")
    @app_commands.describe(logo="Your team logo image (png, jpg, gif)")
    async def team_logo(
        self,
        interaction: discord.Interaction,
        logo: discord.Attachment
    ):
        db = SessionLocal()
        try:
            manager = db.query(Manager).filter_by(
                discord_id=str(interaction.user.id)
            ).first()

            if not manager:
                await interaction.response.send_message(
                    "You're not registered yet. Use /register first.",
                    ephemeral=True
                )
                return

            # validate it's actually an image
            valid_types = ("image/png", "image/jpeg", "image/gif", "image/webp")
            if logo.content_type not in valid_types:
                await interaction.response.send_message(
                    "Please upload a valid image (PNG, JPG, GIF, or WEBP).",
                    ephemeral=True
                )
                return

            # save the Discord CDN url
            manager.logo_url = logo.url
            db.commit()

            # confirm with a preview embed
            embed = discord.Embed(
                title=f"✅ Logo updated for {manager.team_name}",
                color=discord.Color.green()
            )
            embed.set_thumbnail(url=logo.url)

            await interaction.response.send_message(embed=embed)

        finally:
            db.close()

    @app_commands.command(name="myteam", description="View your current roster")
    async def myteam(self, interaction: discord.Interaction):
        db = SessionLocal()
        try:
            manager = db.query(Manager).filter_by(
                discord_id=str(interaction.user.id)
            ).first()

            if not manager:
                await interaction.response.send_message(
                    "You haven't registered yet. Use /register first.",
                    ephemeral=True
                )
                return

            starters = [r for r in manager.roster if r.is_starter]
            bench    = [r for r in manager.roster if not r.is_starter]

            embed = discord.Embed(
                title=manager.team_name,
                color=discord.Color.blue()
            )

            # show logo if one has been uploaded
            if manager.logo_url:
                embed.set_thumbnail(url=manager.logo_url)

            starter_lines = (
                "\n".join(f"• {r.player.name} ({r.player.role})" for r in starters)
                or "— empty —"
            )
            bench_lines = (
                "\n".join(f"• {r.player.name} ({r.player.role})" for r in bench)
                or "— empty —"
            )

            embed.add_field(name="Starters", value=starter_lines, inline=False)
            embed.add_field(name="Bench",    value=bench_lines,   inline=False)
            embed.set_footer(text=f"Budget: {manager.budget} credits")

            await interaction.response.send_message(embed=embed)

        finally:
            db.close()

    @app_commands.command(name="managers", description="List all registered managers")
    async def managers(self, interaction: discord.Interaction):
        db = SessionLocal()
        try:
            all_managers = db.query(Manager).all()
            if not all_managers:
                await interaction.response.send_message("No managers registered yet.")
                return

            lines = ["**Registered managers:**"]
            for m in all_managers:
                lines.append(f"  • **{m.team_name}** — <@{m.discord_id}>")

            await interaction.response.send_message("\n".join(lines))
        finally:
            db.close()

async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))