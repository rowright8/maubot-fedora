from maubot import MessageEvent
from maubot.handlers import command

from .clients.pagure import PagureClient
from .constants import NL
from .exceptions import InfoGatherError
from .handler import Handler


class DistGitHandler(Handler):
    def __init__(self, plugin):
        super().__init__(plugin)
        self.paguredistgitclient = PagureClient(self.plugin.config["paguredistgit_url"])

    @command.new(help="Retrieve the owner of a given package")
    @command.argument("package", required=True)
    async def whoowns(self, evt: MessageEvent, package: str) -> None:
        """
        Retrieve the owner of a given package

        #### Arguments ####

        * `package`: A Fedora package name

        """
        await evt.mark_read()
        if not package:
            await evt.respond("package argument is required. e.g. `!whoowns kernel`")
            return
        try:
            packageinfo = await self.paguredistgitclient.get_project(package, namespace="rpms")
        except InfoGatherError as e:
            await evt.respond(e.message)
            return

        admins = ", ".join(packageinfo["access_users"]["admin"])
        owners = ", ".join(packageinfo["access_users"]["owner"])
        committers = ", ".join(packageinfo["access_users"]["commit"])

        if owners:
            owners = f"__owner:__ {owners}{NL}"
        if admins:
            admins = f"__admin:__ {admins}{NL}"
        if committers:
            committers = f"__commit:__ {committers}{NL}"

        resp = (
            "".join([x for x in [owners, admins, committers] if x != ""])
            or f"{package} has no owners, admins, or users with commit access"
        )

        await evt.respond(resp)
