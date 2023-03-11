import discord
from discord.ext import commands
from discord_components import DiscordComponents, Select, SelectOption


class RolesDropdown(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        DiscordComponents(bot)

    @commands.command()
    async def roles(self, ctx):
        guild = ctx.guild
        options = [
            SelectOption(role.name, str(role.id), emoji=role.mention)
            for role in guild.roles
        ]
        dropdown = Select(
            placeholder="Choose your roles",
            options=options,
            max_values=len(options),
        )
        await ctx.send("Choose your roles:", components=[dropdown])

        def check(interaction):
            return interaction.message.id == ctx.message.id

        interaction = await self.bot.wait_for("select_option", check=check)
        roles = [
            guild.get_role(int(value))
            for value in interaction.values
        ]
        await interaction.respond(content=f"You have chosen the following roles: {', '.join([role.mention for role in roles])}", type=7)


def setup(bot):
    bot.add_cog(RolesDropdown(bot))
