from revChatGPT.V3 import Chatbot
from dotenv import load_dotenv
import os
from src import log
from collections import defaultdict
from discord import Interaction

logger = log.setup_logger(__name__)

load_dotenv()
openAI_API_KEY = os.getenv("OPENAI_APIKEY")

chatbot = Chatbot(api_key=openAI_API_KEY)

chatbot.conversation = defaultdict(
    lambda: [
        {
            "role": "system",
            "content": chatbot.system_prompt,
        },
    ]
)


def reset_conversation(conversation_id: str):
    chatbot.reset(conversation_id)


def send_message(conversation_id: str, userid: str, message: str):
    responses = []
    try:
        question = f"**<:03:926690697418014721> Q: {message}**"

        response = (
            f"> <@{userid}> \n\n {chatbot.ask(message, convo_id=conversation_id)}"
        )

        responses.append(question)

        char_limit = 1900
        if len(response) > char_limit:
            # Split the response into smaller chunks of no more than 1900 characters each(Discord limit is 2000 per chunk)
            if "```" in response:
                # Split the response if the code block exists

                parts = response.split("```")

                for i in range(0, len(parts)):
                    if i % 2 == 0:  # indices that are even are not code blocks
                        responses.append(parts[i])

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
                                responses.append("```" + chunk + "```")
                        else:
                            responses.append("```" + formatted_code_block + "```")

            else:
                response_chunks = [
                    response[i : i + char_limit]
                    for i in range(0, len(response), char_limit)
                ]

                for chunk in response_chunks:
                    responses.append(chunk)

        else:
            responses.append(response)

    except Exception as e:
        responses.append("> **Error: Something went wrong, please try again later!**")
        logger.exception(f"Error while sending message: {e}")

    finally:
        return responses
