# cogs/holi.py

import random
import logging

import discord
from discord.ext import commands
from discord import Option

# Import the DB repository functions
from repository import repository

logger = logging.getLogger("holi_bot")

# A dictionary of color name -> Discord Color
# You can add or remove as many as you want
HOLI_COLORS = {
    "Red": discord.Color.red(),
    "Orange": discord.Color.from_rgb(255, 165, 0),
    "Yellow": discord.Color.from_rgb(255, 255, 0),
    "Green": discord.Color.green(),
    "Blue": discord.Color.blue(),
    "Purple": discord.Color.purple(),
    "Pink": discord.Color.from_rgb(255, 105, 180),
}

class HoliCog(commands.Cog):
    """Cog that handles Holi role management and splashing."""

    def __init__(self, bot: discord.Bot):
        self.bot = bot

    ############################################################
    # Slash Command Group: /holi_roles
    ############################################################
    holi_roles = discord.SlashCommandGroup(
        "holi_roles",
        "Manage Holi color roles in this server"
    )

    @holi_roles.command(name="create", description="Create Holi color roles for this server.")
    @commands.has_permissions(administrator=True)
    async def create_roles(self, ctx: discord.ApplicationContext):
        """
        Creates Holi-themed roles above the 'verified' role, 
        and logs them in the database for future reference.
        """
        await ctx.defer()
        guild = ctx.guild
        if guild is None:
            await ctx.respond("Guild context not found!", ephemeral=True)
            return

        # Check if roles already exist
        existing = repository.get_holi_roles(guild.id)
        if existing:
            await ctx.respond("Holi roles already exist in this server. Use /holi_roles delete first if needed.", ephemeral=True)
            return

        # Attempt to find the 'verified' role by name, ignoring case
        verified_role = discord.utils.find(lambda r: r.name.lower() == "verified", guild.roles)
        verified_position = verified_role.position if verified_role else 0

        created_count = 0
        for color_name, color_val in HOLI_COLORS.items():
            try:
                new_role = await guild.create_role(
                    name=color_name,
                    color=color_val,
                    reason="Holi roles setup"
                )
                created_count += 1
                # Move the role above 'verified' if possible
                await new_role.edit(position=verified_position + 1)
                # Store in DB
                repository.add_holi_role(guild.id, new_role.id, color_name)
            except discord.Forbidden:
                await ctx.respond("⚠️ I don't have permission to create/manage roles.", ephemeral=True)
                return
            except Exception as e:
                logger.error(f"Error creating role {color_name}: {e}")

        await ctx.respond(f"✅ Created {created_count} Holi color roles.", ephemeral=True)

    @holi_roles.command(name="delete", description="Delete all Holi color roles from this server.")
    @commands.has_permissions(administrator=True)
    async def delete_roles(self, ctx: discord.ApplicationContext):
        """Deletes all Holi color roles in this server and removes them from the database."""
        await ctx.defer()
        guild = ctx.guild
        if guild is None:
            await ctx.respond("Guild context not found!", ephemeral=True)
            return

        roles_in_db = repository.get_holi_roles(guild.id)
        if not roles_in_db:
            await ctx.respond("No Holi roles found for this server.", ephemeral=True)
            return

        deleted_count = 0
        for record in roles_in_db:
            role_obj = guild.get_role(record.role_id)
            if role_obj:
                try:
                    await role_obj.delete(reason="Holi roles cleanup")
                    deleted_count += 1
                except discord.Forbidden:
                    await ctx.respond("⚠️ I don't have permission to delete roles.", ephemeral=True)
                    return
                except Exception as e:
                    logger.error(f"Error deleting role {role_obj.name}: {e}")

        # Clear the DB records
        repository.clear_holi_roles(guild.id)

        await ctx.respond(f"✅ Deleted {deleted_count} Holi roles from the server.", ephemeral=True)

    ############################################################
    # /splash command
    ############################################################
    @commands.slash_command(name="splash", description="Splash a user with color!")
    async def splash(
        self,
        ctx: discord.ApplicationContext,
        member: Option(discord.Member, "User to splash"),
        color: Option(str, "Choose a color (optional)", required=False, choices=list(HOLI_COLORS.keys()))
    ):
        """
        Splashes a user with the specified Holi color role.
        If no color is chosen, picks one at random.
        Removes any existing Holi color roles on the target first.
        Logs the splash in the DB.
        """
        await ctx.defer()
        guild = ctx.guild
        if guild is None:
            await ctx.respond("Guild context not found!", ephemeral=True)
            return

        # Ensure Holi roles exist
        all_holi_roles = repository.get_holi_roles(guild.id)
        if not all_holi_roles:
            await ctx.respond("⚠️ No Holi roles set up in this server. An admin must use `/holi_roles create` first.", ephemeral=True)
            return

        # Determine color to use
        if color is None:
            color = random.choice(list(HOLI_COLORS.keys()))
        color = color.title()  # In case user typed all-lower or partial

        # Find the role record in the DB that matches the chosen color
        target_role_record = None
        for rec in all_holi_roles:
            if rec.color_name.lower() == color.lower():
                target_role_record = rec
                break

        if not target_role_record:
            await ctx.respond(f"⚠️ The color '{color}' is not available. Choose from: {', '.join(HOLI_COLORS.keys())}", ephemeral=True)
            return

        target_role = guild.get_role(target_role_record.role_id)
        if not target_role:
            await ctx.respond(f"⚠️ The role for '{color}' was not found. Try `/holi_roles create` again.", ephemeral=True)
            return

        # Remove any existing Holi color roles from the target
        user_roles = member.roles
        for r in user_roles:
            if r.id in [dbrec.role_id for dbrec in all_holi_roles]:
                try:
                    await member.remove_roles(r, reason="Removing old Holi color before splashing new one")
                except discord.Forbidden:
                    await ctx.respond("⚠️ I don't have permission to remove roles.", ephemeral=True)
                    return

        # Assign the new color role
        try:
            await member.add_roles(target_role, reason=f"Holi splash by {ctx.author}")
        except discord.Forbidden:
            await ctx.respond("⚠️ I don't have permission Sto add roles.", ephemeral=True)
            return

        # Log in DB
        repository.log_splash(
            guild_id=guild.id,
            splasher_id=ctx.author.id,
            target_id=member.id,
            color_name=color
        )

        # Announce success
        embed = discord.Embed(
            title=f" {ctx.author.display_name} splashed {member.display_name} with {color}!",
            color=target_role.color
        )
        await ctx.respond(embed=embed, ephemeral=True)

    ############################################################
    # /splash_history command
    ############################################################
    @commands.slash_command(name="splash_history", description="Show the last 10 splash events for this server.")
    async def splash_history(self, ctx: discord.ApplicationContext):
        """
        Retrieves the last 10 splash logs from the DB and displays them.
        """
        guild = ctx.guild
        if guild is None:
            await ctx.respond("Guild context not found!", ephemeral=True)
            return

        logs = repository.get_splash_logs(guild.id, limit=10)
        if not logs:
            await ctx.respond("No splash events recorded yet.", ephemeral=True)
            return

        lines = []
        for record in logs:
            # Try to get the display name from the guild; fallback if user is no longer in server
            splasher_member = guild.get_member(record.splasher_id)
            target_member = guild.get_member(record.target_id)
            splasher_name = splasher_member.display_name if splasher_member else f"User({record.splasher_id})"
            target_name = target_member.display_name if target_member else f"User({record.target_id})"
            time_str = record.timestamp.strftime("%Y-%m-%d %H:%M")
            lines.append(f"`{time_str}` – **{splasher_name}** splashed **{target_name}** with **{record.color_name}**")

        history_text = "\n".join(lines)
        await ctx.respond(f"**Last {len(lines)} Splash Events:**\n{history_text}")

def setup(bot):
    """Required by PyCord to load this cog."""
    bot.add_cog(HoliCog(bot))
