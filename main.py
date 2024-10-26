import os
import discord
import dotenv
import json
from discord.ext import commands, tasks

dotenv.load_dotenv()


def main():
    """
    Initializes intents (options) and bot through a token in .env
    """
    intents: discord.Intents.default = discord.Intents.default()
    intents.message_content = True
    bot: discord.ext.commands.Bot = commands.Bot(command_prefix="mc!", intents=intents)


    @bot.event
    async def on_ready():
        print(f"{bot.user} online")

    @bot.command(name="setpath")
    async def setpath(ctx, *args):
        embed: discord.Embed = discord.Embed()

        try:
            path: str = args[0]
            assert os.path.isfile(path)

            with open("config.json", 'w+') as cfg:
                try:
                    cfg_json: dict = json.load(cfg)
                except json.decoder.JSONDecodeError:
                    cfg_json: dict = {}
                cfg_json["jar_path"] = path
                json.dump(cfg_json, cfg, indent=6)

            embed.add_field(name="Success!", value="Path is successfully bound.")

        except IndexError:
            embed.add_field(name="Error!", value="Invalid syntax. Example: "
                                                 "mc!setpath C:\\Users\\User\\Server\\minecraft_server.jar")
        except AssertionError:
            embed.add_field(name="Error!", value=f"Provided path doesn't exist.")

        except PermissionError:
            embed.add_field(name="Error!", value="Permission error: Couldn't create/write to config file."
                                                 "Try Launching in Administrator Mode or with more privileges.")

        finally:
            await ctx.channel.send(embed=embed)

    bot.run(os.getenv("DISCORD_SECRET"))


if __name__ == "__main__":
    main()
