import os
from typing import Dict
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient

from dotenv import load_dotenv
import json
import ssl
import certifi
import logging
import http.client as http_client

from langchain.chains import ConversationChain


# load env vars
load_dotenv()

# setup logging
http_client.HTTPConnection.debuglevel = 1
logging.basicConfig()
logging.getLogger().setLevel(os.environ.get("LOG_LEVEL", "INFO"))
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(os.environ.get("LOG_LEVEL", "INFO"))
requests_log.propagate = True
logger = logging.getLogger(__name__)


# Create a WebClient with a custom SSL context
client = WebClient(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    ssl=ssl.create_default_context(cafile=certifi.where()))

# Initialize the Slack app
app = App(client=client)

SLACK_BOT_USER_ID = os.environ["SLACK_BOT_USER_ID"]

from llm.openai import OpenAILLM
llm = OpenAILLM()

active_conversations: Dict[str, ConversationChain] = {}

def get_conversation_id(channel_id, thread_ts):
    return f"{channel_id}:{thread_ts}"

@app.event("app_mention")
def handle_mention(event, say, client):
    global active_conversations

    channel_id = event["channel"]
    user_id = event["user"]
    thread_ts = event.get("thread_ts", event["ts"])
    current_ts = event["ts"]

    logger.info('logging event %s', json.dumps(event, indent=4, sort_keys=True))

    conversation_id = get_conversation_id(channel_id, thread_ts)
    if conversation_id not in active_conversations:
        active_conversations[conversation_id] = llm.get_conversation_chain()

    # is_first_message = thread_ts == current_ts
    # user_messages = []
    # if is_first_message and not conversation_id in active_conversations:
    #     user_messages = [event["text"]]
    #     active_conversations[conversation_id] = llm.get_conversation_chain()
    # else:
        # result = client.conversations_replies(
        #     channel=channel_id,
        #     ts=thread_ts)

        # Filter messages by the user who tagged Boink
        # user_messages = [
        #     message["text"]
        #     for message in result["messages"]
        #     if message.get("user") == user_id and SLACK_BOT_USER_ID in message["text"]
        # ]

    logger.info('active covnversations $$$$ %s', active_conversations)
    conversation_chain: ConversationChain = active_conversations.get(conversation_id)
    user_input = event["text"].replace(SLACK_BOT_USER_ID, '').strip()
    result, amount_of_tokens = llm.get_conversation(chain=conversation_chain, prompt=user_input, username=user_id)

    logger.info('LLM tokens used  %s', amount_of_tokens)

    say(text=f'<@{user_id}> {result}.', thread_ts=thread_ts or current_ts)


if __name__ == "__main__":
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
