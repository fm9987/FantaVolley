# cogs/lineup.py
import discord
from discord import app_commands
from discord.ext import commands
from db import SessionLocal, Manager, Roster, get_state, Player
import config
from court_render import render_lineup

# how many starters needed per position
POSITION_SLOTS = {
    "setter":   1,
    "opposite": 1,
    "middle":   2,
    "outside":  2,
    "libero":   1,
}

class PositionSelect(discord.ui.Select):
    """One dropdown for a single position — only shows players of that role."""
    def __init__(self, role: str, slot_index: int, roster_players: list,
                 parent_view: "LineupView"):
        self.role = role
        self.slot_index = slot_index
        self.parent_view = parent_view

        options = [
            discord.SelectOption(label=p.name[:100], value=str(p.id))
            for p in roster_players
        ]
        placeholder = f"{role.capitalize()} #{slot_index + 1}" if POSITION_SLOTS[role] > 1 else role.capitalize()

        super().__init__(
            placeholder=f"Choose your {placeholder}...",
            options=options,
            min_values=1,
            max_values=1,
            row=parent_view.next_row()
        )

    async def callback(self, interaction: discord.Interaction):
        self.parent_view.selections[(self.role, self.slot_index)] = int(self.values[0])
        await interaction.response.defer()


class ConfirmButton(discord.ui.Button):
    def __init__(self, parent_view: "LineupView"):
        super().__init__(label="Confirm lineup", style=discord.ButtonStyle.green, row=4)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        view = self.parent_view
        total_needed = sum(POSITION_SLOTS.values())

        if len(view.selections) < total_needed:
            await interaction.response.send_message(
                f"Please fill all {total_needed} starting positions before confirming.",
                ephemeral=True
            )
            return

        # check no duplicate player picked twice
        chosen_ids = list(view.selections.values())
        if len(chosen_ids) != len(set(chosen_ids)):
            await interaction.response.send_message(
                "You picked the same player in two slots!", ephemeral=True
            )
            return

        db = SessionLocal()
        try:
            # reset all roster entries for this manager/gameweek to bench
            db.query(Roster).filter_by(
                manager_id=view.manager_id, gameweek=view.gameweek
            ).update({"is_starter": False})

            # set chosen players as starters
            for player_id in chosen_ids:
                entry = db.query(Roster).filter_by(
                    manager_id=view.manager_id,
                    player_id=player_id,
                    gameweek=view.gameweek
                ).first()
                if entry:
                    entry.is_starter = True

            db.commit()

            await interaction.response.edit_message(
                content=f"✅ Lineup confirmed for gameweek {view.gameweek}!",
                view=None
            )
        finally:
            db.close()


class LineupView(discord.ui.View):
    def __init__(self, manager_id: int, gameweek: int, roster: list):
        super().__init__(timeout=180)
        self.manager_id = manager_id
        self.gameweek = gameweek
        self.selections: dict[tuple[str, int], int] = {}
        self._row_counter = 0

        # group roster players by role
        by_role: dict[str, list] = {}
        for r in roster:
            by_role.setdefault(r.player.role, []).append(r.player)

        # build one dropdown per slot (setter x1, middle x2, etc)
        for role, slots in POSITION_SLOTS.items():
            players = by_role.get(role, [])
            for slot_index in range(slots):
                if not players:
                    continue   # no players of this role on the roster
                self.add_item(PositionSelect(role, slot_index, players, self))

        self.add_item(ConfirmButton(self))

    def next_row(self) -> int:
        row = self._row_counter
        self._row_counter += 1
        return min(row, 3)   # rows 0-3 for dropdowns, row 4 reserved for button


class Lineup(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

# add to cogs/lineup.py, inside the Lineup class

    @app_commands.command(name="start_player", description="Set a player as a starter")
    @app_commands.describe(player_name="Name of the player to start")
    async def start_player(self, interaction: discord.Interaction, player_name: str):
        db = SessionLocal()
        try:
            locked = get_state(db, "transfers_locked", "false") == "true"
            if locked:
                await interaction.response.send_message(
                    "🔒 Lineup changes are locked for this gameweek.", ephemeral=True
                )
                return

            manager = db.query(Manager).filter_by(
                discord_id=str(interaction.user.id)
            ).first()
            if not manager:
                await interaction.response.send_message(
                    "You're not registered. Use /register first.", ephemeral=True
                )
                return

            current_gw = int(get_state(db, "current_gameweek", "1"))

            # find the player on this manager's roster (partial name match)
            entry = (
                db.query(Roster)
                .join(Roster.player)
                .filter(
                    Roster.manager_id == manager.id,
                    Roster.gameweek == current_gw,
                    Player.name.ilike(f"%{player_name}%")
                )
                .first()
            )

            if not entry:
                await interaction.response.send_message(
                    f"Couldn't find **{player_name}** on your roster.", ephemeral=True
                )
                return

            if entry.is_starter:
                await interaction.response.send_message(
                    f"**{entry.player.name}** is already a starter.", ephemeral=True
                )
                return

            # check position slot isn't already full
            role = entry.player.role
            current_starters_in_role = db.query(Roster).join(Roster.player).filter(
                Roster.manager_id == manager.id,
                Roster.gameweek == current_gw,
                Roster.is_starter == True,
                Player.role == role
            ).count()

            slot_limit = POSITION_SLOTS.get(role, 1)
            if current_starters_in_role >= slot_limit:
                await interaction.response.send_message(
                    f"You already have {slot_limit} starting {role}(s). "
                    f"Bench one first with /switch, or pick a different player.",
                    ephemeral=True
                )
                return

            entry.is_starter = True
            db.commit()

            await interaction.response.send_message(
                f"✅ **{entry.player.name}** ({role}) is now a starter."
            )
        finally:
            db.close()


    @app_commands.command(name="switch", description="Swap a starter for a bench player")
    @app_commands.describe(
        player_out="Player currently starting to bench",
        player_in="Bench player to start instead"
    )
    async def switch(self, interaction: discord.Interaction, player_out: str, player_in: str):
        db = SessionLocal()
        try:
            locked = get_state(db, "transfers_locked", "false") == "true"
            if locked:
                await interaction.response.send_message(
                    "🔒 Lineup changes are locked for this gameweek.", ephemeral=True
                )
                return

            manager = db.query(Manager).filter_by(
                discord_id=str(interaction.user.id)
            ).first()
            if not manager:
                await interaction.response.send_message(
                    "You're not registered. Use /register first.", ephemeral=True
                )
                return

            current_gw = int(get_state(db, "current_gameweek", "1"))

            out_entry = (
                db.query(Roster).join(Roster.player)
                .filter(
                    Roster.manager_id == manager.id,
                    Roster.gameweek == current_gw,
                    Player.name.ilike(f"%{player_out}%")
                ).first()
            )
            in_entry = (
                db.query(Roster).join(Roster.player)
                .filter(
                    Roster.manager_id == manager.id,
                    Roster.gameweek == current_gw,
                    Player.name.ilike(f"%{player_in}%")
                ).first()
            )

            if not out_entry:
                await interaction.response.send_message(
                    f"Couldn't find **{player_out}** on your roster.", ephemeral=True
                )
                return
            if not in_entry:
                await interaction.response.send_message(
                    f"Couldn't find **{player_in}** on your roster.", ephemeral=True
                )
                return

            if not out_entry.is_starter:
                await interaction.response.send_message(
                    f"**{out_entry.player.name}** isn't currently a starter.", ephemeral=True
                )
                return
            if in_entry.is_starter:
                await interaction.response.send_message(
                    f"**{in_entry.player.name}** is already a starter.", ephemeral=True
                )
                return

            # same position only — keeps the formation valid
            if out_entry.player.role != in_entry.player.role:
                await interaction.response.send_message(
                    f"Position mismatch: **{out_entry.player.name}** plays "
                    f"{out_entry.player.role}, **{in_entry.player.name}** plays "
                    f"{in_entry.player.role}. You can only swap players in the same position.",
                    ephemeral=True
                )
                return

            out_entry.is_starter = False
            in_entry.is_starter  = True
            db.commit()

            await interaction.response.send_message(
                f"🔄 **{in_entry.player.name}** is in, **{out_entry.player.name}** is benched."
            )
        finally:
            db.close()


    @app_commands.command(name="bench_player", description="Move player to the bench")
    @app_commands.describe(player_name="Name of the player to bench")
    async def bench_player(self, interaction: discord.Interaction, player_name: str):
        db = SessionLocal()
        try:
            locked = get_state(db, "transfers_locked", "false") == "true"
            if locked:
                await interaction.response.send_message(
                    "🔒 Lineup changes are locked for this gameweek.", ephemeral=True
                )
                return

            manager = db.query(Manager).filter_by(
                discord_id=str(interaction.user.id)
            ).first()
            if not manager:
                await interaction.response.send_message(
                    "You're not registered. Use /register first.", ephemeral=True
                )
                return

            current_gw = int(get_state(db, "current_gameweek", "1"))

            # find the player on this manager's roster (partial name match)
            entry = (
                db.query(Roster)
                .join(Roster.player)
                .filter(
                    Roster.manager_id == manager.id,
                    Roster.gameweek == current_gw,
                    Player.name.ilike(f"%{player_name}%")
                )
                .first()
            )

            if not entry:
                await interaction.response.send_message(
                    f"Couldn't find **{player_name}** on your roster.", ephemeral=True
                )
                return

            if not entry.is_starter:
                await interaction.response.send_message(
                    f"**{entry.player.name}** is already on the bench.", ephemeral=True
                )
                return

            role = entry.player.role
            entry.is_starter = False
            db.commit()

            await interaction.response.send_message(
                f"✅ **{entry.player.name}** ({role}) is now on the bench."
            )
        finally:
            db.close()

    @app_commands.command(name="captain", description="Make a player your captain")
    @app_commands.describe(player_name="Who do you want as your captain")
    async def set_captain(self, interaction: discord.Interaction, player_name: str):
        db = SessionLocal()
        try:
            locked = get_state(db, "transfers_locked", "false") == "true"
            if locked:
                await interaction.response.send_message(
                    "🔒 Lineup changes are locked for this gameweek.", ephemeral=True
                )
                return

            manager = db.query(Manager).filter_by(
                discord_id=str(interaction.user.id)
            ).first()
            if not manager:
                await interaction.response.send_message(
                    "You're not registered. Use /register first.", ephemeral=True
                )
                return

            current_gw = int(get_state(db, "current_gameweek", "1"))

            # find the player on this manager's roster (partial name match)
            current_captain = (
                db.query(Roster)
                .join(Roster.player)
                .filter(
                    Roster.manager_id == manager.id,
                    Roster.gameweek == current_gw,
                    Roster.is_captain == True
                )
                .first()
            )
            if current_captain:
                current_captain.is_captain = False

            entry = (
                db.query(Roster)
                .join(Roster.player)
                .filter(
                    Roster.manager_id == manager.id,
                    Roster.gameweek == current_gw,
                    Player.name.ilike(f"%{player_name}%")
                )
                .first()
            )

            if not entry:
                await interaction.response.send_message(
                    f"Couldn't find **{player_name}** on your roster.", ephemeral=True
                )
                return
            entry.is_captain = True
            db.commit()

            await interaction.response.send_message(
                f"✅ **{entry.player.name}** is now your captain! x2 points for him during week {current_gw}"
            )
        finally:
            db.close()



    @app_commands.command(name="lineup_view", description="View your current lineup")
    async def lineup_view(self, interaction: discord.Interaction):
        db = SessionLocal()
        try:
            manager = db.query(Manager).filter_by(
                discord_id=str(interaction.user.id)
            ).first()
            if not manager:
                await interaction.response.send_message(
                    "You're not registered. Use /register first.", ephemeral=True
                )
                return

            current_gw = int(get_state(db, "current_gameweek", "1"))
            roster = db.query(Roster).filter_by(
                manager_id=manager.id, gameweek=current_gw
            ).all()

            starters = [r for r in roster if r.is_starter]
            bench    = [r for r in roster if not r.is_starter]

            # convert Roster objects into plain dicts for render_lineup
            starters_data = [
                {"name": r.player.name, "role": r.player.role, "number": r.player.id, "is_captain": r.is_captain}
                for r in starters
            ]
            bench_data = [
                {"name": r.player.name, "role": r.player.role, "number": r.player.id}
                for r in bench
            ]

            # build the text summary
            lines = [f"**{manager.team_name} — Gameweek {current_gw}**\n"]
            lines.append("**Starters:**")
            for r in starters:
                tag = " - C" if r.is_captain else ""
                lines.append(f"  • {r.player.name} ({r.player.role}){tag}")
            lines.append("\n**Bench:**")
            for r in bench:
                lines.append(f"  • {r.player.name} ({r.player.role})")

            # generate the court image BEFORE sending the response
            await interaction.response.defer(ephemeral=True)
            image_path = render_lineup(manager.team_name, starters_data, bench_data, manager.team)

            await interaction.followup.send(
                content="\n".join(lines),
                file=discord.File(image_path),
                ephemeral=True
            )
        finally:
            db.close()


async def setup(bot: commands.Bot):
    await bot.add_cog(Lineup(bot))