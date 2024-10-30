import json
import os
import discord
import subprocess

from dotenv import load_dotenv
from discord.ext import commands, tasks
from mcstatus import JavaServer
from sys import builtin_module_names
from time import time

from constants import Messages, ErrorMessages, JavaArgs
from assistant_functions import is_valid_ipv4_address, get_ip, get_path, get_mem, write_to_config, proc_read


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

    # region BOT EVENTS AND COMMANDS
    @bot.event
    async def on_ready() -> None:
        """
        Console print whenever bot is ready and start server feed loop.
        :return:
        """
        print(f"{bot.user} Online")
        server_feedback.start()
        empty_server_timeout.start()

    @bot.command(name="setpath")
    async def setpath(ctx: discord.ext.commands.context.Context, *args: str) -> None:
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
    async def setip(ctx: discord.ext.commands.context.Context, *args: str) -> None:
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

    @bot.command(name="setmem")
    async def set_mem(ctx: discord.ext.commands.context.Context, *args: str) -> None:
        embed: discord.Embed = discord.Embed()
        try:
            assert args and args[0].isdigit()
            write_to_config("mem_alloc", args[0])

            embed.add_field(name="Success", value=Messages.SetMemSuccess.value)

        except Exception as e:
            try:
                embed.add_field(name="Error!", value=ErrorMessages[(type(e), "setmem")])
            except KeyError:
                embed.add_field(name="Error!", value=Messages.UnhandledException.value + repr(e))

        finally:
            await ctx.channel.send(embed=embed)

    @bot.command(name="showconfig")
    async def show_config(ctx: discord.ext.commands.context.Context):
        embed: discord.Embed = discord.Embed()
        with open(cfg_path, 'r') as cfg:
            cfg_json: dict = json.load(cfg)
        config_dump: str = json.dumps(cfg_json, indent=4)
        embed.add_field(name="Config", value=config_dump)
        await ctx.channel.send(embed=embed)

    @bot.command(name="status")
    async def get_status(ctx: discord.ext.commands.context.Context) -> None:
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
    async def launch(ctx: discord.ext.commands.context.Context, *args: str) -> None:
        """
        Opens the specified server jar file with launch arguments if it is not running.
        Otherwise, sends error message and does nothing.
        """
        global server_proc, server_proc_running, feedback_channel_id, latest_server_launch
        ON_POSIX: bool = 'posix' in builtin_module_names
        embed: discord.Embed = discord.Embed()

        try:
            # To ensure user has set the ip, we attempt to retrieve it
            _ = get_ip()

            # memory allocation for the server. allows user to give custom memory, though the default is 1024mb.
            default_mem: int = get_mem()
            mem_alloc = args[0] if args and args[0].isdigit() else default_mem
            # poll() returns None or exit code. None if still running, an exit code if finished.

            # by this assertion, we check that the process is not running before attempting to run it.
            assert not server_proc_running
            jar_path: str = get_path()
            server_dir: str = os.path.abspath(os.path.dirname(jar_path))
            # declare default arguments for launch, like ignoring fml query for modded
            args: list[str] = [JavaArgs.Java.value,
                               JavaArgs.MaxMem.value.format(mem_alloc),
                               JavaArgs.MinMem.value.format(mem_alloc),
                               JavaArgs.Jar.value,
                               JavaArgs.Server.value,
                               jar_path]
            print("Launch args: ", args)
            # start a popen subprocess, meaning we are able to manipulate it later on
            server_proc = subprocess.Popen(args,
                                           cwd=server_dir,
                                           stdin=subprocess.PIPE,
                                           stdout=subprocess.PIPE,
                                           close_fds=ON_POSIX)

            # The channel from which the server was launched will be the channel to receive the feedback
            feedback_channel_id = ctx.channel.id
            server_proc_running = True  # Declare that the server is running
            latest_server_launch = time()  # update latest launch time

            embed.add_field(name="Success", value=Messages.LaunchSuccess.value)

        except Exception as e:
            try:
                embed.add_field(name="Error!", value=ErrorMessages[(type(e), "launch")])
            except KeyError:
                embed.add_field(name="Error!", value=Messages.UnhandledException.value + repr(e))

        finally:
            await ctx.channel.send(embed=embed)

    @bot.command(name="close")
    async def shut_server_down(ctx: discord.ext.commands.context.Context):
        """
        Closes the server process from the jar if it is running.
        Otherwise, sends error message and does nothing.
        """
        global server_proc, server_proc_running
        embed: discord.Embed = discord.Embed()


        try:
            # by this assertion, we check that the process is running before attempting to close it.
            assert server_proc_running
            server_proc.stdin.write(b'stop\n')
            server_proc = None

            server_proc_running = False
            embed.add_field(name="Success", value=Messages.CloseSuccess.value)

        except Exception as e:
            try:
                embed.add_field(name="Error!", value=ErrorMessages[(type(e), "close")])
            except KeyError:
                embed.add_field(name="Error!", value=Messages.UnhandledException.value + repr(e))

        finally:
            await ctx.channel.send(embed=embed)


    @bot.command(name="command")
    async def command(ctx: discord.ext.commands.context.Context, *args):
        """
        Sends user args to server process' stdin, resulting in an execution of a minecraft command
        :param ctx: Channel in which the command was sent
        :param args: arguments for the minecraft command. does not verify if valid, minecraft does so by itself
        """
        global server_proc, server_proc_running
        embed: discord.Embed = discord.Embed()

        try:
            # by this assertion, we check that the process is running before attempting to close it.
            assert server_proc_running
            if not args:
                raise SyntaxError
            mc_command: str = " ".join(args)
            mc_command: bytes = mc_command.encode() + b'\n'
            server_proc.stdin.write(mc_command)
            server_proc.stdin.flush()

        except Exception as e:
            try:
                embed.add_field(name="Error!", value=ErrorMessages[(type(e), "command")])
            except KeyError:
                embed.add_field(name="Error!", value=Messages.UnhandledException.value + repr(e))
            # rare indented finally - we do not want to send anything if everything goes right.
            finally:
                await ctx.channel.send(embed=embed)

    @tasks.loop(seconds=1)
    async def server_feedback():
        """
        Prints server process' stdout in chat. This may include command results, players chatting, achievements, etc.
        """
        global server_proc, server_proc_running, feedback_channel_id, latest_server_launch
        if not server_proc_running:
            return
        # If server is running, server_proc is of type subprocess.Popen

        FIVE_MINUTES: float = 60 * 5
        delta_time: float = time() - latest_server_launch
        if delta_time < FIVE_MINUTES:
            return
        # We don't want to send anything for the first ten minute as the server is launching to not overload the chat.

        # Checking if readline returned anything:
        proc_stdout: str = proc_read(server_proc)
        if not proc_stdout:
            return

        print(proc_stdout)
        ctx_channel: discord.ext.commands.context.Context.channel = bot.get_channel(feedback_channel_id)
        await ctx_channel.send(proc_stdout)

    @tasks.loop(minutes=5)
    async def empty_server_timeout():
        """
        While we have mc!close, we can't always trust our friends to remember to close the server.
        Pings the server for status (Could be extracted locally but that's a stdout headache)
        :return:
        """
        global feedback_channel_id, server_proc_running, latest_server_launch
        TWENTY_MINUTES: float = 60 * 20
        if not server_proc_running:
            return

        try:
            server_ip: str = get_ip()
            server: JavaServer = JavaServer.lookup(server_ip)
            status: JavaServer.status = server.status()
        except (TimeoutError, ConnectionRefusedError, KeyError):
            return

        delta_time: float = time() - latest_server_launch
        # If no players online and twenty minutes passed since launch, shut down.
        if status.players.online or delta_time < TWENTY_MINUTES:
            return

        embed: discord.Embed = discord.Embed()
        embed.add_field(name="Timeout", value=Messages.InactivityTimeout.value)
        ctx_channel: discord.ext.commands.context.Context.channel = bot.get_channel(feedback_channel_id)
        await ctx_channel.send(embed=embed)
        await shut_server_down()

    # endregion

    """Now, after declaring all the bot's events and commands, we can run it"""


    bot.run(os.getenv("DISCORD_SECRET"))


if __name__ == "__main__":
    ROOT_DIR: str = os.path.abspath(os.path.dirname(__file__))

    """Initialize server process variable for subsequent uses"""
    server_proc: (subprocess.Popen, None) = None
    server_proc_running: bool = False

    feedback_channel_id: int = 0
    latest_server_launch: float = time()

    load_dotenv()  # Load .env file in order to extract discord secret
    main()
