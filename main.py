import os
import discord
import dotenv
import json
from discord.ext import commands, tasks
from socket import inet_aton, inet_pton, AF_INET, error
from messages import Messages, ErrorMessages


def is_valid_ipv4_address(address: str) -> bool:
    """
    :param address: String of the address
    :return: True if IP address is a valid IPV4, False otherwise
    >>> is_valid_ipv4_address("127.0.0.1")
    True
    >>> is_valid_ipv4_address("IP")
    False
    """
    try:
        inet_pton(AF_INET, address)
    except AttributeError:  # no inet_pton here, sorry
        try:
            inet_aton(address)
        except error:
            return False
        return address.count('.') == 3
    except error:  # not a valid address
        return False
    return True


def handle_config(key: str, value: str) -> None:
    """
    Opens config.json and writes new data
    :param key:  Any string key
    :param value: Any string Value
    >>> handle_config("ip_address", "127.0.0.1")
    Will attempt to open config.json in local dir and write new key and value.
    """
    cfg_path: str = os.path.join(ROOT_DIR, "config.json")
    with open(cfg_path, 'w+') as cfg:
        try:
            cfg_json: dict = json.load(cfg)
        except json.decoder.JSONDecodeError:
            cfg_json: dict = {}
        cfg_json[key] = value
        json.dump(cfg_json, cfg, indent=6)


def main():
    """
    Initialize intents (options) and bot through a token in .env
    """
    intents: discord.Intents.default = discord.Intents.default()
    intents.message_content = True
    bot: discord.ext.commands.Bot = commands.Bot(command_prefix="mc!", intents=intents)

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

            handle_config("jar_path", path)
            embed.add_field(name="Success!", value=Messages.PathSaveSuccess)

        except Exception as e:
            try:
                embed.add_field(name="Error!", value=ErrorMessages[(type(e), "setip")].value)
            except KeyError:
                embed.add_field(name="Error!", value=Messages.UnhandledException)
        finally:
            await ctx.channel.send(embed=embed)

    @bot.command(name="setip")
    async def setip(ctx, *args) -> None:
        """
        Sets teh IP of the server.
        :param ctx: Channel context
        :param args: Iterable of arguments, ideally of length 1 (single string)
        :return: Sends message in channel. Success / Failure
        """

        embed: discord.Embed = discord.Embed()

        try:
            ip_address: str = args[0]
            assert is_valid_ipv4_address(ip_address)

            handle_config("ip_address", ip_address)
            embed.add_field(name="Success!", value=Messages.IPSaveSuccess)

        except Exception as e:
            try:
                embed.add_field(name="Error!", value=ErrorMessages[(type(e), "setip")].value)
            except KeyError:
                embed.add_field(name="Error!", value=Messages.UnhandledException)
        finally:
            await ctx.channel.send(embed=embed)

    bot.run(os.getenv("DISCORD_SECRET"))


if __name__ == "__main__":
    dotenv.load_dotenv()
    ROOT_DIR: str = os.path.abspath(os.path.dirname(__file__))
    main()
