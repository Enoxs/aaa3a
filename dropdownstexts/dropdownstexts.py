import discord
from redbot.core import commands, checks
from typing import List, Tuple

class RoleDropdown(commands.Cog):
    """Cog for creating a dropdown menu to choose multiple roles with custom emojis"""

    def __init__(self, bot):
        self.bot = bot

    @checks.mod_or_permissions(administrator=True)
    @commands.guild_only()
    @commands.command()
    async def role_dropdown(self, ctx: commands.Context, dropdown_label: str, *role_data: str):
        """
        Creates a dropdown menu to choose multiple roles with custom emojis

        `dropdown_label` - The label to display for the dropdown menu
        `role_data` - A list of strings containing data for each role in the format:
        <role_mention>;<custom_emoji>
        """
        options = self._get_dropdown_options(role_data)
        dropdown = self._create_dropdown(dropdown_label, options)
        message = await ctx.send(embed=discord.Embed(description="Choose your roles:", color=0x00ff00), components=[dropdown])
        await self._handle_dropdown(message)

    def _get_dropdown_options(self, role_data: List[str]) -> List[Tuple[str, str]]:
        """
        Parses role data and returns a list of tuples containing role name and custom emoji
        """
        options = []
        for data in role_data:
            role_mention, custom_emoji = data.split(";")
            role_id = int(role_mention[3:-1])
            role = discord.utils.get(self.bot.guilds[0].roles, id=role_id)
            if role is None:
                continue
            options.append((f"{custom_emoji} {role.name}", role.id))
        return options

    def _create_dropdown(self, dropdown_label: str, options: List[Tuple[str, int]]) -> discord.ui.Select:
        """
        Creates and returns a dropdown menu with custom emojis and role names
        """
        dropdown = discord.ui.Select(
            placeholder=dropdown_label,
            options=[discord.ui.SelectOption(label=label, value=str(value)) for label, value in options],
            max_values=len(options)
        )
        return dropdown

    async def _handle_dropdown(self, message: discord.Message) -> None:
        """
        Handles a user selection in the dropdown menu
        """
        def check(interaction: discord.Interaction):
            return interaction.user == message.author and isinstance(interaction, discord.Interaction)

        try:
            interaction = await self.bot.wait_for("select_option", timeout=30.0, check=check)
        except asyncio.TimeoutError:
            return

        selected_roles = [int(value) for value in interaction.values]
        roles = [discord.utils.get(self.bot.guilds[0].roles, id=role_id) for role_id in selected_roles]

        if roles:
            await message.author.add_roles(*roles)

        await message.edit(components=[])


def setup(bot):
    bot.add_cog(RoleDropdown(bot))
