from revChatGPT.V3 import Chatbot
from dotenv import load_dotenv
import os
from src import log

logger = log.setup_logger(__name__)

load_dotenv()
openAI_API_KEY = os.getenv("OPENAI_APIKEY")
chatbot = Chatbot(api_key=openAI_API_KEY)


async def send_message(message, user_message, isPrivate=False):
    author = message.user.id
    await message.response.defer(ephemeral=isPrivate)

    try:
        question = f"**<:Nahida:1037942028874555423>:  {user_message}**"
        response = f"> <@{author}> \n\n {chatbot.ask(user_message)}"

        await message.followup.send(question)

        char_limit = 1900
        if len(response) > char_limit:
            # Split the response into smaller chunks of no more than 1900 characters each(Discord limit is 2000 per chunk)
            if "```" in response:
                # Split the response if the code block exists

                parts = response.split("```")

                for i in range(0, len(parts)):
                    if i % 2 == 0:  # indices that are even are not code blocks
                        await message.followup.send(parts[i])

                    # Send the code block in a seperate message
                    else:  # Odd-numbered parts are code blocks
                        code_block = parts[i].split("\n")
                        formatted_code_block = ""
                        for line in code_block:
                            while len(line) > char_limit:
                                # Split the line at the 50th character
                                formatted_code_block += line[:char_limit] + "\n"
                                line = line[char_limit:]
                            formatted_code_block += (
                                line + "\n"
                            )  # Add the line and seperate with new line

                        # Send the code block in a separate message
                        if len(formatted_code_block) > char_limit + 100:
                            code_block_chunks = [
                                formatted_code_block[i : i + char_limit]
                                for i in range(0, len(formatted_code_block), char_limit)
                            ]
                            for chunk in code_block_chunks:
                                await message.followup.send("```" + chunk + "```")
                        else:
                            await message.followup.send(
                                "```" + formatted_code_block + "```"
                            )

            else:
                response_chunks = [
                    response[i : i + char_limit]
                    for i in range(0, len(response), char_limit)
                ]

                for chunk in response_chunks:
                    await message.followup.send(chunk)

        else:
            await message.followup.send(response)

    except Exception as e:
        await message.followup.send(
            "> **Error: Something went wrong, please try again later!**"
        )
        logger.exception(f"Error while sending message: {e}")
