from revChatGPT.V3 import Chatbot
from dotenv import load_dotenv
import os
from src import log
from collections import defaultdict
import re

logger = log.setup_logger(__name__)

load_dotenv()
openAI_API_KEY = os.getenv("OPENAI_APIKEY")

chatbot = Chatbot(api_key=openAI_API_KEY)

chatbot.temperature = float(os.getenv("TEMPERATURE", 1))
chatbot.max_tokens = int(os.getenv("MAX_TOKENS", 4096))

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


Q_EMOJI = os.getenv("Q_EMOJI")
A_EMOJI = os.getenv("A_EMOJI")


def send_message(conversation_id: str, userid: str, username: str, message: str):
    try:
        responses = []

        if len(message) > 1900:
            raise ValueError("Message too long!")

        response = chatbot.ask(message, convo_id=conversation_id)

        question = f"> {Q_EMOJI} **Q: {message}**\n\一一一\n"

        pages = _paginate(f"{question}\n{response}", 1950, preserve=True)
        total = len(pages)

        for i, page in enumerate(pages):

            page_counter = f" `[{i+1}/{total}]`" if total > 1 else ""

            if i == 0:
                responses.append(
                    f"{question}{A_EMOJI}{page_counter}\n\n{page[len(question)+1:]}"
                )
            else:
                responses.append(f"{A_EMOJI}{page_counter}\n\n{page}")

        return responses

    except Exception as e:
        logger.exception(f"Error while sending message: {e}")
        raise e


def _paginate(text: str, max_size: int = 2000, preserve: bool = True):
    pages = []

    # If the text is empty or shorter than the max size, return it as it is
    if len(text) == 0 or len(text) <= max_size:
        pages.append(text)
        return pages

    # If preserving newlines and code blocks, use a regular expression to split the text by them
    if preserve:
        chunks = re.split(r"(\n|```)", text)

    # Otherwise, just split the text by spaces
    else:
        chunks = text.split(" ")

    # Initialize an empty page and a current size counter
    page = ""
    current_size = 0

    # Loop through the chunks of text
    for chunk in chunks:

        # If the chunk is empty, skip it
        if len(chunk) == 0:
            continue

        # If the chunk is longer than the max size, raise an exception
        if len(chunk) > max_size:
            raise ValueError(f"Chunk is too big ({len(chunk)} > {max_size}): {chunk}")

        # If adding the chunk to the page would exceed the max size, yield the page and start a new one
        if current_size + len(chunk) > max_size:
            pages.append(page.strip())
            page = ""
            current_size = 0

        # Add the chunk to the page and update the current size counter
        page += chunk + (" " if not preserve else "")
        current_size += len(chunk) + (1 if not preserve else 0)

    # Yield any remaining page that is not empty
    if len(page.strip()) > 0:
        pages.append(page.strip())

    return pages
