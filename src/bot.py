import discord
import os
from discord import app_commands
import asyncio
from src.api import reset_conversation
from src.api import send_message
from src import log
from collections import defaultdict

import time

logger = log.setup_logger(__name__)

TEST_GUILD_ID = int(os.getenv("TEST_GUILD_ID"))
TEST_GUILD = discord.Object(id=TEST_GUILD_ID)

CHATGPT_ROLE = os.getenv("CHATGPT_ROLE")
OWNER_ID = int(os.getenv("OWNER_ID"))

intents = discord.Intents.default()
intents.message_content = True

isPrivate = False

lock = asyncio.Lock()
is_bot_busy = defaultdict(lambda: False)


async def set_is_busy(guild_id, is_busy):
    async with lock:
        is_bot_busy[guild_id] = is_busy


async def get_is_busy(guild_id):
    async with lock:
        return is_bot_busy[guild_id]


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
                case ".clear-test":
                    client.tree.clear_commands(guild=TEST_GUILD)
                    synced_commands = await client.tree.sync(guild=TEST_GUILD)
                    await message.author.send("Cleared! " + str(synced_commands))

    @client.event
    async def on_ready():
        logger.info(f"{client.user} is now running!")

    @client.tree.command(name="chat", description="Have a chat with ChatGPT")
    @app_commands.checks.has_role(CHATGPT_ROLE)
    async def chat(interaction: discord.Interaction, message: str):
        guild_id = interaction.guild_id

        print(interaction.guild.name)
        if await get_is_busy(guild_id):
            await interaction.response.send_message(
                "> **Warn: The bot is currently busy, please wait for the previous message to be sent!**",
                ephemeral=True,
            )
            return

        await set_is_busy(guild_id, True)

        await interaction.response.defer(ephemeral=isPrivate)
        username = str(interaction.user)
        userid = str(interaction.user.id)
        guild = str(interaction.guild)
        channel = str(interaction.channel)
        conversation_id = f"{interaction.guild_id}-{interaction.channel_id}"

        responses = await client.loop.run_in_executor(
            None, send_message, conversation_id, userid, message
        )

        for response in responses:
            await interaction.followup.send(response, ephemeral=isPrivate)

        await set_is_busy(guild_id, False)

        logger.info(f"\x1b[31m{username}\x1b[0m : '{message}' ({guild}-{channel})")

    @client.tree.command(name="reset", description="Reset current conversation")
    @app_commands.checks.has_role(CHATGPT_ROLE)
    async def reset(interaction: discord.Interaction):
        guild_id = interaction.guild_id

        print(interaction.guild.name)
        if await get_is_busy(guild_id):
            await interaction.response.send_message(
                "> **Warn: The bot is currently busy, please try again later!**",
                ephemeral=True,
            )
            return

        await set_is_busy(guild_id, True)

        reset_conversation(f"{interaction.guild.id}-{interaction.channel.id}")
        await interaction.response.send_message(
            "> **Info: I have forgotten everything.**", ephemeral=False
        )

        await set_is_busy(guild_id, False)

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

    @client.tree.error
    async def on_app_command_error(
        interaction: discord.Interaction, error: discord.app_commands.AppCommandError
    ) -> None:
        if isinstance(error, app_commands.errors.MissingRole):
            await interaction.response.send_message(
                f"> **ERROR: You do not have permission to access this command!**",
                ephemeral=True,
            )
        # else:
        #     await interaction.response.send_message(
        #         f"> **Error: Something went wrong, please try again later!**",
        #         ephemeral=True,
        #     )

    TOKEN = os.getenv("DISCORD_BOT_TOKEN")

    client.run(TOKEN)
