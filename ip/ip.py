from .AAA3A_utils import CogsUtils  # isort:skip
from redbot.core import Config, commands  # isort:skip
from redbot.core.i18n import Translator, cog_i18n  # isort:skip
from redbot.core.bot import Red  # isort:skip
import typing  # isort:skip

import aiohttp
# import socket

# Credits:
# General repo credits.
# Thanks to @AverageGamer on Discord for the cog idea and the code to find the external ip!
# Thanks to @Flanisch on GitHub for the use of Wikipedia headers instead of the site found before (https://github.com/AAA3A-AAA3A/AAA3A-cogs/pull/)!

_ = Translator("Ip", __file__)

if CogsUtils().is_dpy2:
    from functools import partial

    hybrid_command = partial(commands.hybrid_command, with_app_command=False)
    hybrid_group = partial(commands.hybrid_group, with_app_command=False)
else:
    hybrid_command = commands.command
    hybrid_group = commands.group


@cog_i18n(_)
class Ip(commands.Cog):
    """A cog to get the ip address of the bot!"""

    def __init__(self, bot: Red) -> None:
        self.bot: Red = bot

        self.config: Config = Config.get_conf(
            self,
            identifier=205192943327321000143939875896557571750,  # 969369062738
            force_registration=True,
        )
        self.ip_global: typing.Dict[str, str] = {
            "port": "0000",  # Port.
        }
        self.config.register_global(**self.ip_global)

        self.cogsutils: CogsUtils = CogsUtils(cog=self)

    @commands.is_owner()
    @hybrid_group(name="ip")
    async def ip_group(self, ctx: commands.Context) -> None:
        """Commands group for Ip."""
        pass

    @ip_group.command()
    async def ip(self, ctx: commands.Context) -> None:
        """Get the ip address of the bot."""
        # hostname = socket.gethostname()
        async with aiohttp.ClientSession() as session:
            async with session.get("https://www.wikipedia.org", timeout=3) as r:
                ip = r.headers["X-Client-IP"]  # Gives the "public IP" of the Bot client PC
        await ctx.send(_("The ip address of your bot is `{ip}`.").format(ip=ip))

    @ip_group.command()
    async def website(self, ctx: commands.Context) -> None:
        """Get the ip address website."""
        # hostname = socket.gethostname()
        async with aiohttp.ClientSession() as session:
            async with session.get("https://www.wikipedia.org", timeout=3) as r:
                ip = r.headers["X-Client-IP"]  # Gives the "public IP" of the Bot client PC
        config = await self.config.all()
        port = config["port"]
        await ctx.send(
            _("The Administrator Panel website is http://{ip}:{port}/.").format(ip=ip, port=port)
        )

    @ip_group.command(name="setportip", aliases=["ipportset"], usage="<port>")
    async def setportip(self, ctx: commands.Context, *, port) -> None:
        """Set the port."""
        config = await self.config.all()

        actual_port = config["port"]
        if actual_port is port:
            await ctx.send(_("Port is already set on {port}.").format(port=port))
            return

        await self.config.port.set(port)
        await ctx.send(_("Port registered: {port}.").format(port=port))
