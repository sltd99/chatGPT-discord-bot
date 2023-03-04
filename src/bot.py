import discord
import os
from discord import app_commands
import asyncio
from src.responses import chatbot
from src.responses import send_message
from src import log

logger = log.setup_logger(__name__)

isPrivate = False
lock = asyncio.Lock()

TEST_GUILD_ID = int(os.getenv("TEST_GUILD_ID"))
TEST_GUILD = discord.Object(id=TEST_GUILD_ID)

CHATGPT_ROLE = os.getenv("CHATGPT_ROLE")
OWNER_ID = int(os.getenv("OWNER_ID"))

intents = discord.Intents.default()
intents.message_content = True


class Client(discord.Client):
    def __init__(self) -> None:

        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.activity = discord.Activity(
            type=discord.ActivityType.watching, name="/chat | /help"
        )

    async def setup_hook(self):
        # self.tree.copy_global_to(guild=TEST_GUILD)
        # synced_commands = await self.tree.sync(guild=TEST_GUILD)
        # logger.info("Slash commands synced to test guild..." + str(synced_commands))
        pass


def run_discord_bot():
    client = Client()

    @client.event
    async def on_message(message: discord.Message):
        if message.author == client.user:
            return

        if not message.guild and message.author.id == OWNER_ID:

            match message.content:
                case ".sync":
                    synced_commands = await client.tree.sync()
                    await message.author.send("Synced! " + str(synced_commands))
                case ".clear":
                    client.tree.clear_commands(guild=TEST_GUILD)
                    synced_commands = await client.tree.sync(guild=TEST_GUILD)
                    await message.author.send("Cleared! " + str(synced_commands))

    @client.event
    async def on_ready():
        logger.info(f"{client.user} is now running!")

    @client.tree.command(name="chat", description="Have a chat with ChatGPT")
    @app_commands.checks.has_role(CHATGPT_ROLE)
    async def chat(
        interaction: discord.Interaction, message: app_commands.Range[str, 1, 1970]
    ):
        if interaction.user == client.user:
            return

        if lock.locked():
            await interaction.response.send_message(
                "> **Warn: The bot is currently busy, please wait for the previous message to be sent!**",
                ephemeral=True,
            )
            return

        async with lock:
            username = str(interaction.user)
            user_message = message
            channel = str(interaction.channel)
            logger.info(f"\x1b[31m{username}\x1b[0m : '{user_message}' ({channel})")
            await send_message(interaction, user_message)

    @client.tree.command(name="reset", description="Reset current conversation")
    @app_commands.checks.has_role(CHATGPT_ROLE)
    async def reset(interaction: discord.Interaction):
        if lock.locked():
            await interaction.response.send_message(
                "> **Warn: The bot is currently busy, please try again later!**",
                ephemeral=True,
            )
            return

        async with lock:
            chatbot.reset()
            await interaction.response.send_message(
                "> **Info: I have forgotten everything.**", ephemeral=False
            )

        logger.warning("\x1b[31mChatGPT bot has been successfully reset\x1b[0m")

    @client.tree.command(name="help", description="Show avaliable commands")
    @app_commands.checks.has_role(CHATGPT_ROLE)
    async def help(interaction: discord.Interaction):
        await interaction.response.send_message(
            """:star: **BASIC COMMANDS**
        - `/chat [message]` Chat with ChatGPT!
        - `/reset` Clear ChatGPT conversation history""",
            ephemeral=True,
        )

    # @client.tree.command(name="private", description="Toggle private access")
    # async def private(interaction: discord.Interaction):
    #     global isPrivate
    #     await interaction.response.defer(ephemeral=False)
    #     if not isPrivate:
    #         isPrivate = not isPrivate
    #         logger.warning("\x1b[31mSwitch to private mode\x1b[0m")
    #         await interaction.followup.send(
    #             "> **Info: Next, the response will be sent via private message. If you want to switch back to public mode, use `/public`**"
    #         )
    #     else:
    #         logger.info("You already on private mode!")
    #         await interaction.followup.send(
    #             "> **Warn: You already on private mode. If you want to switch to public mode, use `/public`**"
    #         )

    # @client.tree.command(name="public", description="Toggle public access")
    # async def public(interaction: discord.Interaction):
    #     global isPrivate
    #     await interaction.response.defer(ephemeral=False)
    #     if isPrivate:
    #         isPrivate = not isPrivate
    #         await interaction.followup.send(
    #             "> **Info: Next, the response will be sent to the channel directly. If you want to switch back to private mode, use `/private`**"
    #         )
    #         logger.warning("\x1b[31mSwitch to public mode\x1b[0m")
    #     else:
    #         await interaction.followup.send(
    #             "> **Warn: You already on public mode. If you want to switch to private mode, use `/private`**"
    #         )
    #         logger.info("You already on public mode!")

    @client.tree.error
    async def on_app_command_error(
        interaction: discord.Interaction, error: discord.app_commands.AppCommandError
    ) -> None:
        if isinstance(error, app_commands.errors.MissingRole):
            await interaction.response.send_message(
                f"> **ERROR: You do not have permission to access this command!**",
                ephemeral=True,
            )

    TOKEN = os.getenv("DISCORD_BOT_TOKEN")

    client.run(TOKEN)
