from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv
import logging
import os
import json
import csv
import ssl
import certifi
import logging
from slack_sdk import WebClient

logger = logging.getLogger(__name__)


def write_slack_users_to_csv(client, filename):
    try:
        # Call the users.list method using the WebClient
        result = client.users_list()
        users = result["members"]

        logger.info(json.dumps(users, indent=4, sort_keys=True))

        # Open the CSV file
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=["username", "full_name", "bio"])
            writer.writeheader()

            for user in users:
                # Check if the user is not a bot
                if not user.get('is_bot', False) \
                    and not user.get('deleted', False) \
                    and user['id'] != 'USLACKBOT':

                    logger.info(json.dumps(user, indent=4, sort_keys=True))
                    user_info = {
                        "username": user.get("id"),
                        "full_name": user.get("real_name"),
                        "bio": user.get("profile", {}).get("title")
                    }
                    writer.writerow(user_info)

        logger.info(f"User information has been written to {filename}")
        return True

    except SlackApiError as e:
        logger.error(f"Error: {e}")
        return False
    except IOError as e:
        logger.error(f"Error writing to file: {e}")
        return False


if __name__ == "__main__":
    
    load_dotenv()

    client = WebClient(
        token=os.environ.get("SLACK_BOT_TOKEN"),
        ssl=ssl.create_default_context(cafile=certifi.where()))

    users_csv_filepath = "data/slack_users.csv"
    if os.path.getsize(users_csv_filepath) == 0:
        success = write_slack_users_to_csv(client)
        if success:
            logger.info("Slack users written to CSV")
        else:
            logger.error("Failed to write slack users CSV file")
    else:
        logger.info("Slack users already in CSV, not calling slack API")


'''
USAGE
    export SLACK_BOT_TOKEN=<value>
    python import_slack_users.py
'''