import logging
from itertools import chain

from maubot import MessageEvent, Plugin
from maubot.handlers import command
from mautrix.util.async_db import UpgradeTable
from mautrix.util.config import BaseProxyConfig

from .bugzilla import BugzillaHandler
from .clients.fasjson import FasjsonClient
from .config import Config
from .constants import NL
from .cookie import CookieHandler
from .db import upgrade_table
from .distgit import DistGitHandler
from .fas import FasHandler
from .fedocal import FedocalHandler
from .infra import InfraHandler
from .pagureio import PagureIOHandler

log = logging.getLogger(__name__)


class Fedora(Plugin):
    @classmethod
    def get_db_upgrade_table(cls) -> UpgradeTable:
        return upgrade_table

    async def start(self) -> None:
        assert self.config  # noqa: S101 # This is a valid use of assert
        self.config.load_and_update()
        self.fasjsonclient = FasjsonClient(self.config["fasjson_url"])
        self.register_handler_class(PagureIOHandler(self))
        self.register_handler_class(DistGitHandler(self))
        self.register_handler_class(FasHandler(self))
        self.register_handler_class(InfraHandler(self))
        self.register_handler_class(BugzillaHandler(self))
        self.register_handler_class(FedocalHandler(self))
        self.register_handler_class(CookieHandler(self))

    async def stop(self) -> None:
        pass

    @classmethod
    def get_config_class(cls) -> type[BaseProxyConfig]:
        return Config  # pragma: no cover

    def _get_handler_commands(self):
        for cmd, _ignore in chain(*self.client.event_handlers.values()):
            if not isinstance(cmd, command.CommandHandler):
                continue
            func_mod = cmd.__mb_func__.__module__
            if func_mod != __name__ and not func_mod.startswith(f"{__name__}."):
                continue  # pragma: no cover
            yield cmd

    @command.new(name="help", help="list commands")
    @command.argument("commandname", pass_raw=True, required=False)
    async def bothelp(self, evt: MessageEvent, commandname: str) -> None:
        """return help"""
        output = []

        if commandname:
            # return the full help (docstring) for the given command
            for cmd in self._get_handler_commands():
                if commandname != cmd.__mb_name__:
                    continue
                output.append(cmd.__mb_full_help__)
                break
            else:
                await evt.reply(f"`{commandname}` is not a valid command")
                return
        else:
            # list all the commands with the help arg from command.new
            for cmd in self._get_handler_commands():
                output.append(
                    f"* `{cmd.__mb_prefix__} {cmd.__mb_usage_args__}` - {cmd.__mb_help__}"
                )
        await evt.respond(NL.join(output))

    @command.new(help="return information about this bot")
    async def version(self, evt: MessageEvent) -> None:
        """
        Return the version of the plugin

        Takes no arguments
        """

        await evt.respond(f"maubot-fedora version {self.loader.meta.version}")
