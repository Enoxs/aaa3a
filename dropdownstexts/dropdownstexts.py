from discord_slash import cog_ext, SlashContext
from discord_slash.utils.manage_components import create_select, create_select_option, create_actionrow
from discord_slash.model import SlashCommandOptionType

import discord
from discord.ext import commands


class RoleSelector(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @cog_ext.cog_slash(
        name="roles",
        description="Select roles from a dropdown menu",
        options=[
            {
                "name": "roles",
                "description": "Select the roles you want to assign",
                "type": SlashCommandOptionType.STRING,
                "required": True,
                "choices": [
                    create_select_option(role.name, role.id, emoji=str(role.emoji)) for role in your_roles_here
                ],
                "multiple": True,
            }
        ],
    )
    async def role_selector(self, ctx: SlashContext, roles):
        member = ctx.author
        guild = ctx.guild
        roles_to_add = [discord.Object(id=int(r)) for r in roles]
        await member.add_roles(*roles_to_add, reason="Selected via dropdown menu")
        await ctx.send(
            f"Assigned the following roles to {member.display_name}: {', '.join([r.name for r in roles_to_add])}",
            hidden=True,
        )

def setup(bot):
    bot.add_cog(RoleSelector(bot))
