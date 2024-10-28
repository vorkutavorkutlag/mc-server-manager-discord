import os
import discord
import subprocess
from dotenv import load_dotenv
from discord.ext import commands, tasks
from mcstatus import JavaServer

from messages import Messages, ErrorMessages
from assistant_functions import is_valid_ipv4_address, get_ip, get_path, write_to_config




def main():
    """First, initialize intents (options) and bot through a token in .env"""
    intents: discord.Intents.default = discord.Intents.default()
    intents.message_content = True
    bot: discord.ext.commands.Bot = commands.Bot(command_prefix="mc!", intents=intents)

    """Initializes config file"""
    cfg_path: str = os.path.join(ROOT_DIR, "config.json")
    if not os.path.exists(cfg_path) or not os.stat(cfg_path).st_size:
        with open(cfg_path, 'w+') as cfg:
            cfg.write("{}")
    del cfg_path  # Free unneeded variable

    # region BOT EVENTS AND COMMANDS

    @bot.event
    async def on_ready() -> None:
        """
        Console print whenever bot is ready
        :return:
        """
        print(f"{bot.user} Online")

    @bot.command(name="setpath")
    async def setpath(ctx, *args) -> None:
        """
        Sets the path to the server executable.
        :param ctx: Channel context
        :param args: Iterable of arguments, ideally of length 1 (single string)
        :return: Sends message in channel. Success / Failure
        """

        embed: discord.Embed = discord.Embed()

        try:
            path: str = args[0]
            assert os.path.isfile(path)

            write_to_config("jar_path", path)
            embed.add_field(name="Success!", value=Messages.PathSaveSuccess.value)

        except Exception as e:
            try:
                embed.add_field(name="Error!", value=ErrorMessages[(type(e), "setpath")])
            except KeyError:
                embed.add_field(name="Error!", value=Messages.UnhandledException.value + repr(e))
        finally:
            await ctx.channel.send(embed=embed)

    @bot.command(name="setip")
    async def setip(ctx, *args) -> None:
        """
        Binds the IP of the server.
        :param ctx: Channel context
        :param args: Iterable of arguments, ideally of length 1 (single string)
        :return: Sends message in channel. Success / Failure
        """

        embed: discord.Embed = discord.Embed()

        try:
            ip_address: str = args[0].strip()
            assert is_valid_ipv4_address(ip_address)

            write_to_config("ip_address", ip_address)
            embed.add_field(name="Success!", value=Messages.IPSaveSuccess.value)

        except Exception as e:
            try:
                embed.add_field(name="Error!", value=ErrorMessages[(type(e), "setip")])
            except KeyError:
                embed.add_field(name="Error!", value=Messages.UnhandledException.value + repr(e))

        finally:
            await ctx.channel.send(embed=embed)

    @bot.command(name="status")
    async def get_status(ctx) -> None:
        """
        Sends the status of the server. Online / Offline, Players and Latency.
        """
        embed: discord.Embed = discord.Embed()

        try:
            server_ip: str = get_ip()
            server: JavaServer = JavaServer.lookup(server_ip)
            status: JavaServer.status = server.status()
            embed.add_field(name="Success!", value=Messages.ServerStatus.value
                        .format(status.players.online, status.latency))

        except Exception as e:
            try:
                embed.add_field(name="Error!", value=ErrorMessages[(type(e), "status")])
            except KeyError:
                embed.add_field(name="Error!", value=Messages.UnhandledException.value + repr(e))

        finally:
            await ctx.channel.send(embed=embed)

    @bot.command(name="launch")
    async def launch(ctx, *args) -> None:
        """
        Opens the specified server jar file with launch arguments.
        """
        embed: discord.Embed = discord.Embed()
        try:
            jar_path: str = get_path()

        except Exception as e:
            try:
                embed.add_field(name="Error!", value=ErrorMessages[(type(e), "launch")])
            except KeyError:
                embed.add_field(name="Error!", value=Messages.UnhandledException.value + repr(e))

        finally:
            await ctx.channel.send(embed=embed)

    # endregion

    """Now, after declaring all of the bot's events and commands, we can run it"""

    bot.run(os.getenv("DISCORD_SECRET"))




if __name__ == "__main__":
    ROOT_DIR: str = os.path.abspath(os.path.dirname(__file__))
    load_dotenv()  # Load .env file in order to extract discord secret
    main()
